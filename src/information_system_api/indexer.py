from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer
from .config import DB_DIR, EMBEDDING_MODEL_NAME, COLLECTION_NAME

class VectorIndexer:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
        self.embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        if self.collection.count() == len(chunks) and len(chunks) > 0:
            return  # Already indexed

        self.chroma_client.delete_collection(COLLECTION_NAME)
        self.collection = self.chroma_client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        texts = [c["text"] for c in chunks]
        embeddings = self.embed_model.encode(texts, show_progress_bar=False).tolist()
        metadatas = [{"source": c["source"], "page": c["page"], "chunk_id": c["id"]} for c in chunks]
        ids = [c["id"] for c in chunks]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        query_vec = self.embed_model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_vec,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        hits = []
        if not results or not results["documents"]:
            return hits

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        for doc, meta, dist in zip(docs, metas, dists):
            similarity = 1.0 - dist
            hits.append({
                "id": meta["chunk_id"],
                "text": doc,
                "source": meta["source"],
                "page": meta["page"],
                "similarity": similarity
            })
        return hits