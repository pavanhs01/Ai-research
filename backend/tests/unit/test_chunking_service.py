"""Unit tests for ChunkingService — no DB, no network required."""
import pytest
from app.services.chunking_service import ChunkingService, CHUNK_TOKEN_SIZE
from app.services.parsing_service import ParsedPage


@pytest.fixture
def service():
    return ChunkingService()


def test_single_short_page_produces_one_chunk(service):
    pages = [ParsedPage(page_number=1, section="Intro", text="Hello world, this is a test.")]
    chunks = service.chunk_pages(pages)
    assert len(chunks) == 1
    assert chunks[0].content == "Hello world, this is a test."
    assert chunks[0].page_number == 1
    assert chunks[0].section == "Intro"
    assert chunks[0].chunk_index == 0


def test_long_text_splits_into_multiple_chunks(service):
    long_text = "word " * 800  # ~800 tokens
    pages = [ParsedPage(page_number=2, section=None, text=long_text)]
    chunks = service.chunk_pages(pages)
    assert len(chunks) > 1
    assert all(c.page_number == 2 for c in chunks)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_multiple_pages_preserve_individual_metadata(service):
    pages = [
        ParsedPage(page_number=1, section="Chapter 1", text="Content of chapter one. " * 10),
        ParsedPage(page_number=2, section="Chapter 2", text="Content of chapter two. " * 10),
    ]
    chunks = service.chunk_pages(pages)
    page1_chunks = [c for c in chunks if c.page_number == 1]
    page2_chunks = [c for c in chunks if c.page_number == 2]
    assert len(page1_chunks) >= 1
    assert len(page2_chunks) >= 1
    assert all(c.section == "Chapter 1" for c in page1_chunks)
    assert all(c.section == "Chapter 2" for c in page2_chunks)


def test_empty_pages_produce_no_chunks(service):
    pages = [ParsedPage(page_number=1, section=None, text="   ")]
    chunks = service.chunk_pages(pages)
    assert chunks == []


def test_chunk_indices_are_globally_sequential(service):
    pages = [
        ParsedPage(page_number=i, section=None, text="Some content here. " * 20)
        for i in range(1, 4)
    ]
    chunks = service.chunk_pages(pages)
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_token_count_is_positive(service):
    pages = [ParsedPage(page_number=1, section=None, text="A reasonable paragraph of text for testing.")]
    chunks = service.chunk_pages(pages)
    assert all(c.token_count > 0 for c in chunks)
