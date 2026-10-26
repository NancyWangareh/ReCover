# ReCover
## Microinsurance Information and Recommendation System
The key is to build something that helps mitumba market traders understand available microinsurance products, compare their options, and choose what suits their needs.

The project focuses on improving access to reliable microinsurance information, helping traders understand product terms, and laying the foundation for personalized recommendations that consider their needs and financial circumstances.

## Project Objectives

* Improve access to microinsurance information for informal traders.
* Help traders understand available products, coverage, eligibility requirements, premiums, exclusions, and claims procedures.
* Provide clear, evidence-based answers to microinsurance questions.
* Build a foundation for comparing products and developing a separate recommendation system.

## System Architecture

### 1. Microinsurance Knowledge Base

The knowledge base is being developed from insurance and policy documents relevant to the Kenyan microinsurance market.

Current document collection includes:

* Britam product profile.
* Kenya Microinsurance Policy Paper.
* Jinue policy document.
* TCIP brochure.
* Kenya legal and regulatory document.
* Britam Biashara Lite brochure

These documents provide source material for retrieving information about microinsurance products, policies, and the regulatory environment.

### 2. Document Processing and Retrieval

The initial Retrieval-Augmented Generation (RAG) pipeline is being developed to retrieve relevant information from the collected documents.

Current implementation includes:

* **Document parsing:** LlamaCloud/LlamaParse for extracting content from PDF documents.
* **Text chunking:** Splitting parsed documents into smaller sections for retrieval.
* **Embeddings:** Using Sentence Transformers to represent text as numerical vectors.
* **Vector storage:** ChromaDB for storing and retrieving relevant document chunks.
* **Language model:** Google Gemini for generating responses from retrieved information.

The five collected PDF documents have been parsed into Markdown, producing approximately 265 text chunks for the initial knowledge base.

### 3. AI-Powered Information Assistant

The ReCover information assistant is designed to answer questions using retrieved document excerpts rather than unsupported assumptions.

Its intended capabilities include:

* Answering questions about microinsurance products available in Kenya.
* Identifying product names and their providers.
* Explaining coverage, eligibility, premiums, exclusions, and claims procedures when the documents provide the information.
* Identifying information gaps instead of inventing answers.
* Referencing source documents to support responses.

The retrieval and response-generation pipeline is still being developed and refined to prioritize relevant product information over general policy background.

### 4. Planned User Interface: WhatsApp Chatbot

A WhatsApp chatbot is planned as the primary user interface, making microinsurance information accessible through a familiar communication channel.

The intended interaction will allow traders to ask questions and receive clear, accessible explanations about available insurance products.

**Status:** Planned; the current focus is building and testing the underlying information retrieval and response-generation system.

### 5. Pending Recommendation System

The recommendation system will be developed separately from the information assistant.

Its intended purpose is to help traders explore suitable products and payment options based on information such as:

* Type of risk or protection needed.
* Preferred contribution frequency.
* Affordable contribution amount.
* Income variability and payment preferences.

Recommendations will need to be grounded in verified product information and clearly explain their limitations.

**Status:** Planned; not yet implemented as part of the current information assistant.

## Technology Stack

| Component               | Technology                        | Purpose                                     |
| ----------------------- | --------------------------------- | ------------------------------------------- |
| Development environment | Google Colab                      | Developing and testing the pipeline         |
| Document parsing        | LlamaCloud / LlamaParse           | Extracting content from PDF documents       |
| Text processing         | Recursive Character Text Splitter | Dividing documents into retrievable chunks  |
| Embeddings              | Sentence Transformers             | Converting text into vector representations |
| Vector database         | ChromaDB                          | Storing and retrieving document chunks      |
| Large language model    | Google Gemini                     | Generating answers from retrieved context   |
| Planned user interface  | WhatsApp                          | Providing access to the assistant           |

## Project Structure

The project is organized into modules to separate configuration, document processing, retrieval, and response generation.

```text
ReCover/
├── data/
│   ├── original/          # Source documents
│   ├── parsed_output/     # Parsed Markdown documents
│   └── chroma_db/         # Generated vector database
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── document_parser.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── llm_client.py
│   └── rag_pipeline.py
├── .gitignore
├── .Information_system.ipynb
├── .LICENSE
├── .README.md
├── .main.py
└── requirements.txt

```



## Current Development Status

| Component                              | Status                                        |
| -------------------------------------- | --------------------------------------------- |
| Collection of initial source documents | Completed                                     |
| PDF parsing using LlamaCloud           | Completed for the initial five documents      |
| Markdown document generation           | Completed for the initial documents           |
| Initial text chunking                  | Completed; approximately 265 chunks generated |
| Gemini API connection                  | Tested successfully                           |
| Embedding and vector-storage modules   | Under development and integration             |
| Retrieval quality and relevance        | Under evaluation                              |
| End-to-end RAG pipeline                | Under development                             |
| WhatsApp chatbot integration           | Planned                                       |
| Separate product recommendation system | Planned                                       |

## Data and Security

* API keys and credentials should be stored securely and excluded from version control.
* Generated vector databases and private or restricted source documents should not be committed unless there is a clear reason and permission to share them.
* Responses should distinguish verified product information from missing or unavailable information.
* Product details should be checked against reliable source documents before being used to guide decisions.

## Improvements

1. Improve retrieval so product-related questions prioritize product names, providers, and relevant product terms.
2. Test answer accuracy against the source documents and verify source references.
3. Complete integration of the parsing, chunking, embedding, retrieval, and generation modules.
4. Evaluate the assistant using representative questions from mitumba market traders.
5. Integrate the information assistant with WhatsApp.
6. Develop and validate the separate recommendation system.
7. Explore appropriate payment-frequency and affordability considerations for traders with irregular incomes.





