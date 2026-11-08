
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
            return

        self.chroma_client.delete_collection(COLLECTION_NAME)
        self.collection = self.chroma_client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        batch_size = 16

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            texts = [c["text"] for c in batch]

            embeddings = self.embed_model.encode(
                texts,
                batch_size=4,
                show_progress_bar=False,
                convert_to_numpy=True
            ).tolist()

            metadatas = [
                {
                    "source": c["source"],
                    "page": c["page"],
                    "chunk_id": c["id"]
                }
                for c in batch
            ]

            ids = [c["id"] for c in batch]

            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

        print(f"Successfully indexed {len(chunks)} chunks.")

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
            hits.append({
                "id": meta["chunk_id"],
                "text": doc,
                "source": meta["source"],
                "page": meta["page"],
                "similarity": 1.0 - dist
            })

        return hits
