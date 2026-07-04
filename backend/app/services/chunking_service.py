from __future__ import annotations

from app.services.parsing_service import ParsedPage

CHUNK_TOKEN_SIZE = 500
CHUNK_TOKEN_OVERLAP = 75

# Tiktoken needs network access on first use to download BPE vocab.
# We lazy-load and fall back to a character-based estimator (4 chars ≈ 1 token)
# so the app boots and runs in network-restricted environments.
_encoding = None


def _get_encoding():
    global _encoding
    if _encoding is not None:
        return _encoding
    try:
        import tiktoken
        _encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        _encoding = None
    return _encoding


def _encode(text: str) -> list[int]:
    enc = _get_encoding()
    if enc is not None:
        return enc.encode(text)
    # fallback: split into 4-char pseudo-tokens
    return list(range(len(text) // 4 + 1))


def _decode(tokens: list[int], original_text: str) -> str:
    enc = _get_encoding()
    if enc is not None:
        return enc.decode(tokens)
    # fallback: slice proportionally from original text
    ratio = len(original_text) / max(len(_encode(original_text)), 1)
    start = int(tokens[0] * ratio) if tokens else 0
    end = int((tokens[-1] + 1) * ratio) if tokens else len(original_text)
    return original_text[start:min(end, len(original_text))]


class PreparedChunk:
    def __init__(
        self,
        content: str,
        chunk_index: int,
        token_count: int,
        page_number: int | None,
        section: str | None,
    ):
        self.content = content
        self.chunk_index = chunk_index
        self.token_count = token_count
        self.page_number = page_number
        self.section = section


class ChunkingService:
    """
    Splits each parsed page/section into overlapping token-bounded chunks.
    Overlap preserves cross-boundary context; metadata (page/section) travels
    with every chunk so citations resolve back to exact source location.
    """

    def chunk_pages(self, pages: list[ParsedPage]) -> list[PreparedChunk]:
        chunks: list[PreparedChunk] = []
        index = 0
        enc = _get_encoding()

        for page in pages:
            text = page.text.strip()
            if not text:
                continue

            if enc is not None:
                tokens = enc.encode(text)
                start = 0
                while start < len(tokens):
                    end = min(start + CHUNK_TOKEN_SIZE, len(tokens))
                    token_slice = tokens[start:end]
                    chunk_text = enc.decode(token_slice).strip()
                    if chunk_text:
                        chunks.append(
                            PreparedChunk(
                                content=chunk_text,
                                chunk_index=index,
                                token_count=len(token_slice),
                                page_number=page.page_number,
                                section=page.section,
                            )
                        )
                        index += 1
                    if end == len(tokens):
                        break
                    start = end - CHUNK_TOKEN_OVERLAP
            else:
                # Character-based chunking fallback (4 chars ≈ 1 token)
                char_size = CHUNK_TOKEN_SIZE * 4
                char_overlap = CHUNK_TOKEN_OVERLAP * 4
                start = 0
                while start < len(text):
                    end = min(start + char_size, len(text))
                    chunk_text = text[start:end].strip()
                    if chunk_text:
                        estimated_tokens = len(chunk_text) // 4 + 1
                        chunks.append(
                            PreparedChunk(
                                content=chunk_text,
                                chunk_index=index,
                                token_count=estimated_tokens,
                                page_number=page.page_number,
                                section=page.section,
                            )
                        )
                        index += 1
                    if end == len(text):
                        break
                    start = end - char_overlap

        return chunks


chunking_service = ChunkingService()
