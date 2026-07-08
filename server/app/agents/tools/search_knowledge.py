"""Search knowledge base tool — hybrid retrieval + image matching."""

from typing import List, Dict, Any

from ...rag.hybrid_retrieval import HybridRetrieval
from ...models.database import SessionLocal
from ...models.knowledge_image import KnowledgeImage
from ...utils.logger import logger


class SearchKnowledgeTool:
    def __init__(self):
        self.retrieval = HybridRetrieval()
        self.name = "search_knowledge_base"
        self.description = "搜索客服知识库"

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "用户的问题"},
                        "category": {"type": "string", "description": "分类过滤"},
                    },
                    "required": ["query"],
                },
            },
        }

    async def execute(self, query: str, category: str = None) -> str:
        logger.info(f"[search_knowledge] === START: query='{query}', category={category} ===")
        results = self.retrieval.search(query, category=category)
        if not results:
            logger.warning(f"[search_knowledge] === NO RESULTS for '{query}' ===")
            return "知识库中未找到相关信息"

        context = ""
        seen_pages: dict = {}  # (file_hash, page_num) → bool
        used_sources: set = set()

        for i, doc in enumerate(results, 1):
            chunk = doc['content']
            source = doc.get('source_file', '未知')
            score = doc.get('rerank_score', doc.get('score', 'N/A'))
            score_pct = f"{score * 100:.1f}%" if isinstance(score, (int, float)) else str(score)
            file_hash = doc.get('file_hash', '')
            used_sources.add(file_hash)

            logger.info(f"[search_knowledge] Result #{i}: score={score}, source={source}, "
                        f"hash={file_hash[:16] if file_hash else 'N/A'}")

            chunk_idx = doc.get('chunk_index', -1)
            images = self._get_matching_images(file_hash, chunk, chunk_index=chunk_idx)

            context += f"[{i}] {chunk}\n"
            for img in images:
                alt = img.get('step_label') or f"操作步骤{img['page_num']}"
                context += f"![{alt}]({img['image_path']})\n"
                seen_pages[(file_hash, img['page_num'])] = True
            context += f"来源: {source}\n"
            context += f"相关度: {score_pct}\n\n"

        # ── Supplement: add missing pages from image-heavy files ──
        supplemental = 0
        for fh in used_sources:
            all_imgs = self._get_matching_images(fh, chunk_index=-1)
            for img in all_imgs:
                key = (fh, img['page_num'])
                if key not in seen_pages:
                    alt = img.get('step_label') or f"操作步骤{img['page_num']}"
                    context += f"[{len(results) + supplemental + 1}] {img.get('description', '')}\n"
                    context += f"![{alt}]({img['image_path']})\n\n"
                    seen_pages[key] = True
                    supplemental += 1

        if supplemental:
            logger.info(f"[search_knowledge] Supplemented {supplemental} missing pages "
                         f"from {len(used_sources)} source(s)")

        logger.info(f"[search_knowledge] === RETURNING {len(results)} + {supplemental} "
                     f"supplemental ===")
        return context.strip()

    @staticmethod
    def _get_matching_images(file_hash: str, chunk_text: str = "",
                              chunk_index: int = -1) -> List[Dict]:
        """Look up page images for a given chunk.

        Matches by chunk_index → page_num (1-based).  For image-based
        PDFs each chunk = one page, so this gives exactly one image.
        Falls back to all images if chunk_index is unknown.
        """
        if not file_hash:
            return []
        try:
            db = SessionLocal()
            query = db.query(KnowledgeImage).filter(
                KnowledgeImage.file_hash == file_hash
            ).order_by(KnowledgeImage.page_num)

            # Match by chunk_index if provided (image PDFs: 1 chunk = 1 page)
            # chunk_index=-1 means "return all pages" (used for supplemental)
            if chunk_index >= 0:
                query = query.filter(KnowledgeImage.page_num == chunk_index + 1)

            records = query.all()
            images = []
            for r in records:
                if r.image_path not in chunk_text:
                    images.append({
                        "page_num": r.page_num,
                        "image_path": r.image_path,
                        "step_label": r.step_label,
                        "description": r.description,
                    })
            return images
        except Exception as e:
            logger.warning(f"[search_knowledge] Image lookup failed: {e}")
            return []
        finally:
            db.close()
