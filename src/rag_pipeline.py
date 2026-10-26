
from vector_store import retrieve_documents
from llm_client import generate_answer


def ask_recover(question, n_results=5):
    """
    Retrieve relevant documents and generate an answer.
    """

    results = retrieve_documents(
        question,
        n_results=n_results
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    context_parts = []

    for i, document in enumerate(documents):
        metadata = metadatas[i] or {}
        source = metadata.get("source", "Unknown source")

        context_parts.append(
            f"Source: {source}\n"
            f"Excerpt:\n{document}"
        )

    context = "\n\n".join(context_parts)

    if not context.strip():
        return "I could not find relevant information in the knowledge base."

    return generate_answer(
        question=question,
        context=context
    )
