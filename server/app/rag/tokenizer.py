"""
Shared Chinese/English tokenizer for BM25 indexing and querying.

Uses jieba for Chinese word segmentation + space-based tokenization
for English/numbers.  Ensures consistent tokenization between index
build time and query time — the root cause of BM25 returning zero
results for Chinese queries.
"""

import re
import jieba
from typing import List


# ── CJK character detection ──────────────────────────────
_CJK_RE = re.compile(r'[一-鿿㐀-䶿豈-﫿]')

# Common stopwords to filter out (reduces noise in BM25)
_STOPWORDS: set = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
    '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
    '没有', '看', '好', '自己', '这', '他', '她', '它', '们', '那', '些',
    '所', '为', '所以', '因为', '但是', '然而', '而且', '虽然', '如果',
    '之', '与', '及', '或', '但', '而', '且', '被', '从', '以', '对',
    '将', '已', '能', '可以', '可能', '应该', '已经', '还', '又', '再',
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'under', 'again', 'further', 'then', 'once', 'here',
    'there', 'when', 'where', 'why', 'how', 'all', 'both', 'each',
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    'just', 'because', 'about', 'also', 'if', 'or', 'and', 'but',
}


def tokenize(text: str, remove_stopwords: bool = True) -> List[str]:
    """Tokenize text for BM25 indexing and querying.

    - Chinese text → jieba word segmentation
    - English/numbers → whitespace split
    - Single CJK characters also added as fallback
    - Optional stopword removal

    Returns a list of tokens.
    """
    if not text:
        return []

    tokens: List[str] = []

    # ── Step 1: jieba segmentation for Chinese ──
    # Use jieba.cut for accurate word segmentation
    jieba_words = list(jieba.cut(text))
    for word in jieba_words:
        word = word.strip()
        if not word or word == ' ':
            continue
        if remove_stopwords and word.lower() in _STOPWORDS:
            continue
        tokens.append(word)

    # ── Step 2: Whitespace tokens for English / mixed content ──
    for part in text.split():
        part = part.strip()
        if not part:
            continue
        # Only add if it contains non-CJK characters (CJK chars already
        # handled by jieba above)
        if not _CJK_RE.search(part):
            if remove_stopwords and part.lower() in _STOPWORDS:
                continue
            if part not in tokens:
                tokens.append(part)

    # ── Step 3: Character bigrams as fallback (catch partial matches) ──
    # Remove spaces/punctuation for bigram generation
    stripped = re.sub(r'\s+', '', text)
    cleaned = re.sub(r'[^一-鿿㐀-䶿豈-﫿a-zA-Z0-9]',
                     '', stripped)
    for i in range(len(cleaned) - 1):
        bigram = cleaned[i:i + 2]
        if bigram not in tokens:
            tokens.append(bigram)

    return tokens


def tokenize_for_bm25(text: str) -> List[str]:
    """Convenience wrapper: tokenize and return unique tokens."""
    return list(set(tokenize(text, remove_stopwords=True)))
