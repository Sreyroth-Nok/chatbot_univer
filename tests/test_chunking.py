import pytest

from knowledge.services.chunking import split_text


def test_empty_text():
    assert split_text("   \n\n ") == []


def test_short_paragraphs_are_grouped():
    text = "Para one.\n\nPara two.\n\nPara three."
    assert split_text(text, max_chars=100, overlap=10) == ["Para one.\n\nPara two.\n\nPara three."]


def test_chunks_never_exceed_max():
    text = "\n\n".join(f"Paragraph {i} " + "x" * 120 for i in range(20))
    chunks = split_text(text, max_chars=300, overlap=50)
    assert chunks
    assert all(len(c) <= 300 for c in chunks)


def test_long_paragraph_is_split_with_overlap():
    para = "".join(chr(65 + i % 26) for i in range(1000))
    chunks = split_text(para, max_chars=400, overlap=100)
    assert len(chunks) == 3
    assert chunks[0][-100:] == chunks[1][:100]  # overlap kept
    assert chunks[-1].endswith(para[-50:])      # nothing lost at the end


def test_overlap_must_be_smaller_than_max():
    with pytest.raises(ValueError):
        split_text("abc", max_chars=10, overlap=10)
