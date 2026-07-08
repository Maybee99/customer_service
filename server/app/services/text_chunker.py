"""
Intelligent text chunker for RAG document ingestion.
Splits long documents into overlapping chunks optimized for embedding.
"""
import re
from typing import List, Dict
from ..utils.logger import logger


class TextChunker:
    """Split text into overlapping chunks with sentence/paragraph awareness."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 128):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # ── Public API ──────────────────────────────────────────

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks using hierarchical strategy.

        Strategy (priority descending):
          1. Split by paragraphs (\\n\\n)
          2. If paragraph > chunk_size, split by sentences
          3. If sentence > chunk_size, split by fixed size + overlap
        """
        if not text or not text.strip():
            return []

        # Step 1: Split into paragraphs
        paragraphs = self._split_paragraphs(text)

        # Step 2: Build chunks from paragraphs
        chunks = []
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph keeps us under chunk_size, accumulate
            if not current:
                current = para
            elif len(current) + len(para) + 2 <= self.chunk_size:
                current += "\n\n" + para
            else:
                # Current chunk is full — finalize it
                if len(current) <= self.chunk_size:
                    chunks.append(current)
                else:
                    # Current itself is too large, split by sentences
                    chunks.extend(self._split_long_paragraph(current))
                current = para

        # Don't forget the last chunk
        if current:
            if len(current) <= self.chunk_size:
                chunks.append(current)
            else:
                chunks.extend(self._split_long_paragraph(current))

        # Remove empty/whitespace-only chunks
        chunks = [c.strip() for c in chunks if c.strip()]

        logger.info(f"[TextChunker] Split {len(text)} chars → {len(chunks)} chunks"
                     f" (size={self.chunk_size}, overlap={self.chunk_overlap})")
        return chunks

    def chunk_with_metadata(
        self,
        text: str,
        source_file: str,
        category: str
    ) -> List[Dict[str, object]]:
        """Chunk text and attach metadata for Milvus insertion."""
        chunks = self.chunk_text(text)
        return [
            {
                "content": chunk,
                "chunk_index": i,
                "source_file": source_file,
                "category": category,
            }
            for i, chunk in enumerate(chunks)
        ]

    # ── Internal helpers ────────────────────────────────────

    @staticmethod
    def _split_paragraphs(text: str) -> List[str]:
        """Split text into paragraphs by double newlines."""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Split on 2+ consecutive newlines
        return re.split(r'\n{2,}', text)

    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """Split an over-size paragraph: try sentences first, then fixed-size."""
        sentences = self._split_sentences(paragraph)

        chunks = []
        current = ""

        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue

            if not current:
                current = sent
            elif len(current) + len(sent) + 1 <= self.chunk_size:
                current += " " + sent
            else:
                if len(current) <= self.chunk_size:
                    chunks.append(current)
                else:
                    # Single sentence is too large → fixed-size split
                    chunks.extend(self._fixed_size_split(current))
                current = sent

        if current:
            if len(current) <= self.chunk_size:
                chunks.append(current)
            else:
                chunks.extend(self._fixed_size_split(current))

        return chunks

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences (Chinese + English aware).

        Uses punctuation as sentence boundaries:
          Chinese: 。！？；
          English: . ! ? (followed by space or end)
        """
        # Match sentence-ending punctuation followed by optional quotes and whitespace
        pattern = r'(?<=[。！？；.!?])(?=[\s"“”‘’]*[^\s。！？；.!?])'
        parts = re.split(pattern, text)
        # Merge very short parts with their neighbors
        merged = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if merged and len(part) < 10:
                merged[-1] += part
            else:
                merged.append(part)
        return merged

    def _fixed_size_split(self, text: str) -> List[str]:
        """Split text into fixed-size chunks with overlap."""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            # Try to break at a natural boundary near chunk_size
            if end < text_len:
                # Look for a sentence boundary within the last 20% of the chunk
                search_start = max(start, end - self.chunk_size // 5)
                boundary = self._find_boundary(text, search_start, end)
                if boundary > search_start:
                    end = boundary + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - self.chunk_overlap if end < text_len else text_len

        return chunks

    @staticmethod
    def _find_boundary(text: str, start: int, end: int) -> int:
        """Find the last sentence boundary position within [start, end)."""
        for i in range(end - 1, start - 1, -1):
            if text[i] in '。！？；.!?\n':
                return i
        return -1


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 128
) -> List[str]:
    """Convenience function for simple chunking."""
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_text(text)
