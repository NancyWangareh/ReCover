
import re
from typing import List, Dict, Any
from urllib.parse import quote
from pathlib import Path

from .config import DOCS_DIR


def validate_and_extract_citations(
    answer: str,
    evidence: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:

    tags = re.findall(r"\[S(\d+)\]", answer)
    cited_indices = sorted(set(int(tag) - 1 for tag in tags))

    sources = []

    for idx in cited_indices:
        if 0 <= idx < len(evidence):
            chunk = evidence[idx]

            document = chunk["source"]
            page = chunk["page"]

            document_path = DOCS_DIR / document

            source = {
                "tag": f"[S{idx + 1}]",
                "document": document,
                "page": page,
                "reference": f"{document}, p.{page}",
                "url": None
            }

            if document_path.is_file():
                encoded_filename = quote(document)
                source["url"] = (
                    f"/documents/{encoded_filename}#page={page}"
                )

            sources.append(source)

    return sources
