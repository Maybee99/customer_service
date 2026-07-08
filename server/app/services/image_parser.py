"""
Image-aware PDF parser using Qwen-VL multimodal model.

Renders each PDF page as a high-resolution image, then calls Qwen-VL
to describe the content — including text, UI elements, and operation
steps visible in screenshots.  Generates markdown chunks with embedded
image references so downstream RAG can retrieve and display them.

Requires: PyMuPDF (fitz)
"""

import base64
import io
import os
import re
import hashlib
from typing import List, Dict, Optional, Tuple, Callable

from openai import OpenAI

from ..config import get_settings
from ..utils.logger import logger

settings = get_settings()

# ── Qwen-VL model name ────────────────────────────────────
VL_MODEL = "qwen-vl-max"

# ── Prompt for page description ───────────────────────────
VL_PROMPT = """请简洁描述这张截图，分两部分：

1. **文档来源**：一句话说明这份文档是什么（如"西南科技大学研究生管理系统操作手册"）
2. **截图内容**：用2-4句话描述这一页截图展示的具体操作或信息，包括关键按钮、菜单、文字

要求：
- 总共不超过150字
- 只描述截图实际展示的内容，不要推测
- 如果是操作步骤，用"→"连接（如：点击服务大厅 → 找到学生延迟离校审核 → 点击进入）"""


class ImageParser:
    """Parse image-heavy PDFs using Qwen-VL multimodal model.

    Workflow:
      1. Render each PDF page as a PNG image (PyMuPDF)
      2. Send each image to Qwen-VL with a structured prompt
      3. Qwen-VL returns a markdown description of the page
      4. Save page images to disk for serving
      5. Return page descriptions + image paths
    """

    def __init__(self, dpi: int = 150, save_images: bool = True,
                 max_workers: int = 4):
        self.dpi = dpi
        self.save_images = save_images
        self.max_workers = max_workers
        self.image_dir = os.path.join(settings.data_dir, "images")
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_api_base,
            )
        return self._client

    # ── Public API ──────────────────────────────────────────

    def parse_pdf(self, file_path: str,
                  file_hash: str = "",
                  file_id: int = None,
                  progress_callback: Callable[[int, str], None] = None
                  ) -> List[Dict[str, object]]:
        """Parse an image-heavy PDF page by page with Qwen-VL.

        Args:
            file_path: Path to the PDF file
            file_hash: SHA256 hash of the file (for naming images)
            file_id: KnowledgeFile DB id (for saving image metadata)
            progress_callback: Optional fn(pct, step_label) for progress

        Returns:
            List of page dicts with fields:
              {page_num, text, image_path, image_filename,
               step_label, description, image_count}
        """
        import fitz  # PyMuPDF
        from concurrent.futures import ThreadPoolExecutor, as_completed

        if not file_hash:
            file_hash = self._hash_file(file_path)

        doc = fitz.open(file_path)
        total_pages = len(doc)
        logger.info(
            f"[ImageParser] Parsing {total_pages} pages @ {self.dpi} DPI "
            f"({self.max_workers} workers) "
            f"(file={os.path.basename(file_path)})"
        )

        # ── Step 1: Render all pages & save images (fast) ──
        page_images: List[Tuple[int, bytes, str]] = []
        os.makedirs(self.image_dir, exist_ok=True)

        for page_num in range(total_pages):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=self.dpi)
            img_bytes = pix.tobytes("png")
            image_filename = f"{file_hash}_p{page_num + 1}.png"

            if self.save_images:
                img_path = os.path.join(self.image_dir, image_filename)
                with open(img_path, "wb") as f:
                    f.write(img_bytes)

            page_images.append((page_num + 1, img_bytes, image_filename))

        doc.close()

        if progress_callback:
            progress_callback(2, "图片渲染完成，开始识别...")

        # ── Step 2: Call Qwen-VL for all pages in parallel ──
        total = total_pages
        completed = 0

        def _describe_one(page_num: int, img_bytes: bytes) -> Tuple[int, str]:
            return page_num, self._describe_page(img_bytes, page_num, total)

        results: Dict[int, str] = {}
        workers = min(self.max_workers, total_pages)
        logger.info(f"[ImageParser] Starting {workers} parallel VL workers for {total} pages")

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_describe_one, pn, ib): pn
                for pn, ib, _ in page_images
            }
            for future in as_completed(futures):
                page_num, desc = future.result()
                results[page_num] = desc
                completed += 1
                logger.info(
                    f"[ImageParser] Page {page_num}/{total} done "
                    f"({completed}/{total}, {len(desc)} chars)"
                )
                if progress_callback:
                    pct = 3 + int(completed / total * 12)  # 3%→15%
                    progress_callback(pct, f"识别第{page_num}/{total}页...")

        # ── Step 3: Build page dicts (plain text, no embedded images) ──
        pages: List[Dict] = []
        for page_num, img_bytes, filename in page_images:
            description = results.get(page_num, "（无法识别此页面内容）")
            image_url = f"{settings.server_url}/api/knowledge/images/{filename}"
            step_label = self._extract_step_label(description)

            pages.append({
                "page_num": page_num,
                "text": description.strip(),           # plain text for embedding
                "image_path": image_url,
                "image_filename": filename,
                "step_label": step_label,
                "description": description.strip(),
                "image_count": 1,
            })

        # ── Step 4: Save image metadata to DB ──
        if file_id:
            self._save_image_metadata(file_id, file_hash, pages)

        logger.info(
            f"[ImageParser] Done: {len(pages)} pages, "
            f"images → {self.image_dir}"
        )
        return pages

    def get_text_density(self, file_path: str) -> Tuple[int, float]:
        """Quick check: how much text per page does the PDF have?

        Returns (total_pages, avg_chars_per_page).
        Use this to decide whether to use ImageParser.
        """
        import fitz

        doc = fitz.open(file_path)
        total_chars = 0
        for page in doc:
            text = page.get_text()
            total_chars += len(text.strip())
        pages = doc.page_count
        doc.close()

        pages = pages or 1
        avg = total_chars / pages
        logger.info(
            f"[ImageParser] Text density: {total_chars} chars / "
            f"{pages} pages = {avg:.1f} chars/page"
        )
        return pages, avg

    # ── Internal ───────────────────────────────────────────

    def _describe_page(self, img_bytes: bytes,
                       page_num: int, total_pages: int) -> str:
        """Call Qwen-VL to describe a single page image."""

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        data_url = f"data:image/png;base64,{img_b64}"

        try:
            response = self.client.chat.completions.create(
                model=VL_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                        {
                            "type": "text",
                            "text": (
                                f"这是文档的第{page_num}/{total_pages}页。"
                                f"{VL_PROMPT}"
                            ),
                        },
                    ],
                }],
                max_tokens=2048,
            )
            content = response.choices[0].message.content
            return content.strip() if content else "（无法识别此页面内容）"

        except Exception as e:
            logger.error(f"[ImageParser] VL call failed for page {page_num}: {e}")
            return f"（页面{page_num}识别失败: {str(e)[:200]}）"

    @staticmethod
    def _save_image_metadata(file_id: int, file_hash: str,
                              pages: List[Dict]) -> None:
        """Save per-page image metadata to the knowledge_images table."""
        from ..models.database import SessionLocal
        from ..models.knowledge_image import KnowledgeImage

        db = SessionLocal()
        try:
            # Delete existing records for this file (re-index case)
            db.query(KnowledgeImage).filter(
                KnowledgeImage.file_id == file_id
            ).delete()
            for page in pages:
                db.add(KnowledgeImage(
                    file_id=file_id,
                    file_hash=file_hash,
                    page_num=page["page_num"],
                    image_path=page["image_path"],
                    image_filename=page["image_filename"],
                    step_label=page.get("step_label", ""),
                    description=page.get("description", ""),
                ))
            db.commit()
            logger.info(f"[ImageParser] Saved {len(pages)} image metadata records "
                        f"for file #{file_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"[ImageParser] Failed to save image metadata: {e}")
        finally:
            db.close()

    @staticmethod
    def _extract_step_label(description: str) -> str:
        """Extract a step label from Qwen-VL description.

        Matches patterns like:
          截图内容：xxx
          第一步：登录系统
          步骤1: xxx
        Returns the matched label or first meaningful sentence.
        """
        if not description:
            return ""
        # New prompt format: "2. **截图内容**：xxx"
        m = re.search(r'\*{0,2}截图内容\*{0,2}[：:]\s*(.+?)(?:。|$)', description)
        if m:
            label = m.group(1).strip()
            if len(label) > 60:
                label = label[:60] + '...'
            return label
        # Old prompt format: "第一步：xxx"
        patterns = [
            r'(第[一二三四五六七八九十\d]+步[：:]\s*[^\n]+)',
            r'(步骤\s*\d+[：:]\s*[^\n]+)',
        ]
        for pat in patterns:
            m = re.search(pat, description)
            if m:
                return m.group(1).strip()
        # Fallback: return first sentence (up to 60 chars)
        first = description.split('。')[0].strip()
        if len(first) > 60:
            first = first[:60] + '...'
        return first

    @staticmethod
    def _hash_file(file_path: str) -> str:
        """SHA256 hash of file for naming images."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
