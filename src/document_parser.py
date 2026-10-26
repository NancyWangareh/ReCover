
"""
Parse PDF documents using LlamaCloud and save the output as Markdown.
"""

import os
from pathlib import Path

from llama_cloud_services import LlamaParse


PROJECT_DIR = Path("/content/drive/MyDrive/ReCover")
INPUT_DIR = PROJECT_DIR / "data" / "original"
OUTPUT_DIR = PROJECT_DIR / "data" / "parsed_output"


def parse_documents(input_dir=None, output_dir=None):
    """
    Parse PDFs in the input directory and save Markdown output.

    The LLAMA_CLOUD_API_KEY environment variable must be configured.

    Returns:
        list[Path]: Paths to the saved Markdown files.
    """
    input_dir = Path(input_dir or INPUT_DIR)
    output_dir = Path(output_dir or OUTPUT_DIR)

    if not os.getenv("LLAMA_CLOUD_API_KEY"):
        raise EnvironmentError(
            "LLAMA_CLOUD_API_KEY is not configured."
        )

    if not input_dir.exists():
        raise FileNotFoundError(
            f"Input directory does not exist: {input_dir}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    parser = LlamaParse(
        api_key=os.environ["LLAMA_CLOUD_API_KEY"],
        result_type="markdown",
    )

    saved_files = []

    for pdf_path in sorted(input_dir.glob("*.pdf")):
        output_path = output_dir / f"{pdf_path.stem}.md"

        if output_path.exists():
            print(f"Skipping existing file: {output_path.name}")
            saved_files.append(output_path)
            continue

        print(f"Parsing: {pdf_path.name}")

        documents = parser.parse(str(pdf_path))

        markdown_parts = []

        for document in documents:
            text = getattr(document, "text", "")
            if text:
                markdown_parts.append(text)

        if not markdown_parts:
            print(f"Warning: No text extracted from {pdf_path.name}")
            continue

        output_path.write_text(
            "\n\n".join(markdown_parts),
            encoding="utf-8",
        )

        saved_files.append(output_path)
        print(f"Saved: {output_path}")

    print(f"\nParsing complete. Markdown files available: {len(saved_files)}")

    return saved_files
