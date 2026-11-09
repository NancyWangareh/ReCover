# ReCover

## Microinsurance Information and Recommendation System

ReCover helps mitumba market traders access reliable information about microinsurance products, understand their terms, compare available options, and explore recommendations that consider their business needs and financial circumstances.

The system combines a document-grounded microinsurance information assistant with a separate recommendation service. Traders can access the assistant through WhatsApp, making it easier to ask questions through a familiar communication channel.

## Project Objectives

- Improve access to microinsurance information for informal traders.
- Help traders understand available products, coverage, eligibility requirements, premiums, exclusions, and claims procedures.
- Provide clear, evidence-based answers to microinsurance questions.
- Offer data-driven product recommendations based on traders' business profiles and financial circumstances.
- Make the information assistant accessible through WhatsApp.

## System Architecture

### 1. Microinsurance Knowledge Base

The knowledge base uses insurance and policy documents relevant to the Kenyan microinsurance market.

Documents currently read by the notebook (in `data collection/`):

- Britam Biashara Network product guide (scanned PDF, transcribed with Gemini OCR).
- Jubilee Traders Comprehensive Insurance Policy (TCIP) brochure (scanned PDF, transcribed with Gemini OCR).
- Kenya Microinsurance Policy Paper.
- Jinue policy document.
- Kenya legal and regulatory document.

Also in the repository:

- `Microinsurance_Data_Collection_Workbook.xlsx`: Phase 1 research notes, including the 21 trader questions used for testing.
- `ReCover_Microinsurance_Product_Matching_Database.xlsx`: product, cover and trader-segment mapping, used for eligibility cautions in the rules.

These documents provide source material for retrieving information about microinsurance products, policies, and the regulatory environment.

### 2. Document Processing and Retrieval

The document-processing and retrieval pipeline is implemented in `ReCover_Chatbot.ipynb`.

- **Document reading:** `pypdf` extracts text from readable PDFs. Scanned PDFs are transcribed page by page with Gemini and saved in `data/ocr_text/`, preserving page references.
- **Text chunking:** Recursive Character Text Splitter (1,000 characters, 150 overlap), per page, so each chunk retains its source file and page.
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`).
- **Vector storage:** ChromaDB.
- **Retrieval:** Gemini rewrites the question into search queries; the original question is also searched. Results are merged and chunks below a similarity cut-off are dropped.
- **Language model:** Google Gemini is used for query rewriting and answer generation.

### 3. AI-Powered Information Assistant

The ReCover information assistant answers questions using retrieved document excerpts rather than unsupported assumptions.

It:

- Answers questions about microinsurance products available in Kenya in English, Kiswahili or Sheng.
- Collects relevant details about the trader's situation, such as type of premises, stock value and budget, and uses them during the conversation.
- Applies eligibility rules using Python rather than relying on the language model to make eligibility decisions. Each product receives one of three outcomes: may qualify, needs confirmation by the insurer, or does not meet a stated requirement.
- Provides source references: facts are labelled, and answers include the files and pages used.
- Acknowledges when the available documents do not contain an answer. If no relevant information is retrieved, a fixed response is returned rather than asking the language model to invent an answer.

The current hand-written eligibility rules cover Jubilee TCIP and Britam Biashara. They must be reviewed whenever the underlying product documents change.

### 4. WhatsApp Chatbot

The ReCover assistant has been integrated with WhatsApp using the Twilio WhatsApp messaging interface and a FastAPI backend.

The message flow is:

1. A trader sends a message to the ReCover WhatsApp number.
2. Twilio forwards the incoming WhatsApp message to the backend webhook.
3. The backend passes the message to the ReCover assistant for processing.
4. The assistant handles the information question or recommendation conversation and generates a response.
5. The backend returns the response through the WhatsApp integration so the trader can receive it in the chat.

The WhatsApp integration provides a conversational access point to the assistant. The information retrieval and recommendation components remain responsible for generating the content of the response.

**Status:** WhatsApp integration implemented. Continue testing the complete message flow, including webhook delivery, backend availability, response handling and different trader questions, before relying on it in a live environment.

### 5. Recommendation System

The recommendation system is developed separately as a clustering model exposed through a FastAPI service and connected to the assistant.

How the assistant and recommendation service work together:

- The assistant identifies whether a message is an **information** question or a **recommendation** request.
- For a recommendation, it collects the required trader details, such as risk, stock value, budget, payment preference, income pattern and stability, restock cycle, and past losses.
- It sends the collected details to the recommendation API and explains the suggested plans in the trader's language.
- If all suggested plans are above the trader's stated budget, the response communicates this clearly.
- Prices and eligibility are presented as subject to confirmation by the insurer.

**Status:** Connected to the assistant. The model was built using synthetic trader data. Product prices and plan details should be verified against the relevant insurer documents, and recommendations should be validated using real trader data.

## Technology Stack

| **Component** | **Technology** | **Purpose** |
|---|---|---|
| Development environment | Google Colab | Developing and testing the information pipeline |
| Document reading | pypdf, Gemini OCR | Extracting text from PDFs, including scanned documents |
| Text processing | Recursive Character Text Splitter | Dividing documents into retrievable chunks |
| Embeddings | Sentence Transformers | Converting text into vector representations |
| Vector database | ChromaDB | Storing and retrieving document chunks |
| Large language model | Google Gemini | Query rewriting and answer generation |
| Eligibility rules | Python | Checking requirements stated in product documents |
| Recommendation model | scikit-learn (K-means) | Grouping trader profiles for recommendation |
| Backend/API | FastAPI | Exposing assistant and recommendation functionality over HTTP |
| WhatsApp integration | Twilio WhatsApp messaging | Receiving trader messages and delivering assistant responses |

## How to Run and Configure

### Information assistant

1. Open `ReCover_Chatbot.ipynb` in Google Colab (or run it locally after installing the dependencies in `requirements.txt`).
2. If you are not running from inside the cloned repository, set the repository link in `REPO_URL` in Section 1 of the notebook.
3. Set `RECOMMENDER_URL` to the deployed recommendation API endpoint.
4. Add the Gemini API key. In Colab, use Secrets and create `GEMINI_API_KEY` with notebook access enabled. Locally, set `GEMINI_API_KEY` as an environment variable.
5. Run the notebook cells in order. The first run downloads the embedding model and processes the scanned PDFs, so it may take a few minutes.

### WhatsApp integration

The WhatsApp integration requires the backend to be deployed and reachable over HTTPS.

1. Configure the WhatsApp-enabled Twilio sender/account.
2. Set the incoming-message webhook in the Twilio WhatsApp configuration to the deployed backend's WhatsApp webhook endpoint (the `/whatsapp` route).
3. Ensure the backend has the required credentials and configuration in its deployment environment. Do not commit API keys, authentication tokens or other secrets to the repository.
4. Confirm that the webhook accepts incoming messages and that the backend returns a valid response through the WhatsApp integration.
5. Test both information questions and recommendation conversations from an actual WhatsApp client.

Deployment-specific environment variable names and secret values should be taken from the current backend configuration; do not assume that local notebook settings automatically configure the deployed service.

## Project Structure

```text
ReCover/
├── data collection/       # Source PDFs and research workbooks
├── data/
│   ├── ocr_text/          # Gemini transcriptions of scanned PDFs
│   └── chroma_db/         # Generated vector database (not committed)
├── src/                   # Earlier modular version of the pipeline
├── ReCover_Chatbot.ipynb  # End-to-end information assistant pipeline
├── Information_system.ipynb
├── LICENSE
├── README.md
├── main.py
└── requirements.txt
```

The exact deployed backend structure may differ from this notebook-oriented project structure. Update this section as the deployment code is consolidated into the repository.

## Current Development Status

| **Component** | **Status** |
|---|---|
| Collection of initial source documents | Completed |
| Reading PDFs, including scanned documents | Completed for the five PDFs currently processed |
| Text chunking with page references | Implemented |
| Embedding and vector storage | Implemented in the notebook |
| Gemini API connection | Tested successfully |
| Retrieval (question rewriting and relevance cut-off) | Implemented; evaluation against trader questions ongoing |
| Eligibility rules | Implemented for Jubilee TCIP and Britam Biashara |
| Source references in answers | Implemented |
| End-to-end information assistant | Working in the notebook; answers continue to be checked against source documents |
| Recommendation service | Connected to the assistant; model and product matching under review |
| WhatsApp chatbot integration | Implemented; end-to-end and deployment testing ongoing |

## Known Limitations

- **Recommendations require further validation.** The model was trained on synthetic data and should be validated using real trader data. Product matching and affordability logic also require continued review.
- **Premium information may be incomplete.** The Britam business insurance guide provides percentage rates rather than a flat premium, while the TCIP brochure does not provide a flat premium. The assistant should direct traders to the insurer for a quote where the documents do not establish the cost.
- **Eligibility needs insurer confirmation.** The documents do not establish whether open-air or temporary stalls qualify for Britam Biashara, so the assistant must not tell a trader that they are covered.
- **OCR can make mistakes.** Transcriptions of scanned documents should be checked against the originals.
- **Swahili and Sheng responses** need review by a native speaker before broad use with traders.
- **The fallback “I don't have that information” response** is currently English only.
- **WhatsApp availability depends on the deployed webhook and messaging configuration.** The integration should be tested for delivery failures, backend downtime and unexpected message formats.
- The assistant provides information, not insurance advice. Eligibility, premiums and policy terms must be confirmed with the insurer.

## Data and Security

- Store API keys, Twilio credentials and other secrets securely as environment variables or deployment secrets. Never commit them to version control.
- Do not commit generated vector databases or private/restricted source documents unless there is a clear reason and permission to share them.
- Responses should distinguish verified product information from missing or unavailable information.
- Product details should be checked against reliable source documents before being used to guide decisions.
- Use the minimum personal and business information needed to provide the service, and handle trader conversations and contact details responsibly.

## Next Steps

1. Add eligibility rules for more products as verified premiums and terms become available.
2. Verify the Britam Biashara Lite plan table against the official brochure and ensure the brochure is included in document processing.
3. Validate the recommendation model and product-matching logic with real trader data.
4. Have a native Kiswahili speaker review Kiswahili and Sheng responses.
7. Complete end-to-end WhatsApp testing, including information queries, multi-turn recommendation flows, webhook errors and response delivery.
8. Improve affordability and payment-frequency considerations for traders with irregular income.iderations for traders with irregular incomes.
