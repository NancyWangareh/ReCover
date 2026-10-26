
import chromadb
from pathlib import Path

PROJECT_DIR = Path("/content/drive/MyDrive/ReCover")
CHROMA_DIR = PROJECT_DIR / "data" / "chroma_db"

COLLECTION_NAME = "recover_microinsurance"


def get_collection():
    """
    Connect to the existing ChromaDB collection.
    """
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    return collection


def retrieve_documents(question, n_results=5):
    """
    Retrieve relevant passages from ChromaDB.
    """
    collection = get_collection()

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    return results
