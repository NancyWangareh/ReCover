
"""
Split parsed Markdown documents into overlapping text chunks.
"""

from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter


PROJECT_DIR = Path("/content/drive/MyDrive/ReCover")
PARSED_DIR = PROJECT_DIR / "data" / "parsed_output"


def chunk_text(
    text,
    chunk_size=1000,
    chunk_overlap=150,
):
    """
    Split a text string into overlapping chunks.

    Args:
        text: Text to split.
        chunk_size: Maximum chunk size in characters.
        chunk_overlap: Number of overlapping characters.

    Returns:
        list[str]: Non-empty text chunks.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string.")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be non-negative and smaller than chunk_size."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    return [
        chunk.strip()
        for chunk in splitter.split_text(text)
        if chunk.strip()
    ]


def chunk_markdown_file(
    file_path,
    chunk_size=1000,
    chunk_overlap=150,
):
    """
    Read a Markdown file and split it into chunks.

    Returns:
        list[dict]: Chunks with source filename and chunk index.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Markdown file not found: {file_path}"
        )

    text = file_path.read_text(encoding="utf-8")

    chunks = chunk_text(
        text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    return [
        {
            "text": chunk,
            "source": file_path.name,
            "chunk_index": index,
        }
        for index, chunk in enumerate(chunks)
    ]


def chunk_parsed_directory(
    parsed_dir=None,
    chunk_size=1000,
    chunk_overlap=150,
):
    """
    Process all Markdown files in a directory.

    Returns:
        list[dict]: All chunks with source metadata.
    """
    parsed_dir = Path(parsed_dir or PARSED_DIR)

    if not parsed_dir.exists():
        raise FileNotFoundError(
            f"Parsed directory not found: {parsed_dir}"
        )

    all_chunks = []

    for file_path in sorted(parsed_dir.glob("*.md")):
        print(f"Chunking: {file_path.name}")

        chunks = chunk_markdown_file(
            file_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        all_chunks.extend(chunks)

        print(f"  Chunks created: {len(chunks)}")

    print(f"\nTotal chunks created: {len(all_chunks)}")

    return all_chunks
