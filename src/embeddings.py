
"""
Generate semantic text embeddings using Sentence Transformers.
"""

from sentence_transformers import SentenceTransformer


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingModel:
    """
    Generate embeddings for document chunks and user queries.
    """

    def __init__(self, model_name=DEFAULT_MODEL):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts, batch_size=32):
        """
        Convert multiple texts into embeddings.

        Args:
            texts: List of strings.
            batch_size: Number of texts processed per batch.

        Returns:
            list[list[float]]: Embedding vectors.
        """
        if not texts:
            return []

        if not all(isinstance(text, str) for text in texts):
            raise TypeError("All input texts must be strings.")

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 32,
        )

        return embeddings.tolist()

    def embed_query(self, query):
        """
        Generate an embedding for a single user query.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string.")

        return self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).tolist()
