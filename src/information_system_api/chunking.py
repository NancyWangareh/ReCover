from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .config import CHUNK_SIZE, CHUNK_OVERLAP

def chunk_pages(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "; ", " ", ""]
    )
    chunks = []
    for p in pages:
        text = p["text"].strip()
        if not text:
            continue
        splits = splitter.split_text(text)
        for i, split_text in enumerate(splits):
            chunk_id = f"{p['source']}-p{p['page']}-c{i}"
            chunks.append({
                "id": chunk_id,
                "text": split_text,
                "source": p["source"],
                "page": p["page"],
                "chunk_index": i
            })
    return chunks