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

Documents currently read by the notebook (in `data collection/`):

* Britam Biashara Network product guide (scanned PDF, transcribed with Gemini OCR).
* Jubilee Traders Comprehensive Insurance Policy (TCIP) brochure (scanned PDF, transcribed with Gemini OCR).
* Kenya Microinsurance Policy Paper.
* Jinue policy document.
* Kenya legal and regulatory document.

Also in the repo:

* `Microinsurance_Data_Collection_Workbook.xlsx`: Phase 1 research notes, including the 21 trader questions used for testing.
* `ReCover_Microinsurance_Product_Matching_Database.xlsx`: product, cover and trader-segment mapping, used for the eligibility cautions in the rules.

These documents provide source material for retrieving information about microinsurance products, policies, and the regulatory environment.

### 2. Document Processing and Retrieval

The pipeline lives in `ReCover_Chatbot.ipynb` and runs top to bottom.

* **Document reading:** `pypdf` for PDFs that contain text. PDFs that are scans (no readable text) are transcribed page by page with Gemini and saved in `data/ocr_text/`, so each fact keeps its page number.
* **Text chunking:** Recursive Character Text Splitter (1,000 characters, 150 overlap), per page, so every chunk keeps its file and page.
* **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`).
* **Vector storage:** ChromaDB.
* **Retrieval:** Gemini rewrites the question into search queries, the original question is always searched too, results are merged, and chunks below a similarity cut-off are dropped.
* **Language model:** Google Gemini, used to rewrite questions, read the trader's facts, and write the answer.

### 3. AI-Powered Information Assistant

The ReCover information assistant answers questions using retrieved document excerpts rather than unsupported assumptions.

What it does:

* Answers questions about microinsurance products available in Kenya, in English, Kiswahili or Sheng.
* Reads the trader's situation (type of premises, stock value, budget) and remembers it during the conversation.
* Applies rules for eligibility, using plain Python rather than the language model. Each product gets one of three results: may qualify, needs confirmation by the insurer, or does not meet a stated requirement.
* Cites its sources: every fact is labelled, and each answer ends with a list of the files and pages it used.
* Says so when the documents don't contain the answer. If nothing relevant is found, a fixed message is returned and the language model is not asked to answer.

The rules currently cover Jubilee TCIP and Britam Biashara only. They are written by hand from the documents, so they must be updated if a document changes.

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

| Component               | Technology                        | Purpose                                              |
| ----------------------- | --------------------------------- | ---------------------------------------------------- |
| Development environment | Google Colab                      | Developing and testing the pipeline                  |
| Document reading        | pypdf, Gemini (OCR for scans)     | Extracting text from PDFs, including scanned ones    |
| Text processing         | Recursive Character Text Splitter | Dividing documents into retrievable chunks           |
| Embeddings              | Sentence Transformers             | Converting text into vector representations          |
| Vector database         | ChromaDB                          | Storing and retrieving document chunks               |
| Large language model    | Google Gemini                     | Understanding questions and generating answers       |
| Eligibility rules       | Python                            | Checking requirements stated in the documents        |
| Planned user interface  | WhatsApp                          | Providing access to the assistant                    |

## How to Run

1. Open `ReCover_Chatbot.ipynb` in Google Colab (or locally after `pip install -r requirements.txt`).
2. If you are not running from inside the cloned repo, put the repo link in `REPO_URL` in Section 1.
3. Add your Gemini key. In Colab: Secrets > `GEMINI_API_KEY`, with notebook access on. Locally: set the `GEMINI_API_KEY` environment variable.
4. Run the cells in order. The first run downloads the embedding model and transcribes the scanned PDFs, so it takes a few minutes.

## Project Structure

```text
ReCover/
├── data collection/       # Source PDFs and the Excel workbooks
├── data/
│   ├── ocr_text/          # Gemini transcriptions of scanned PDFs
│   └── chroma_db/         # Generated vector database (not committed)
├── src/                   # Earlier modular version of the pipeline; not used by the notebook
├── ReCover_Chatbot.ipynb  # Current end-to-end pipeline
├── Information_system.ipynb
├── LICENSE
├── README.md
├── main.py
└── requirements.txt
```

## Current Development Status

| Component                                         | Status                                                          |
| ------------------------------------------------- | --------------------------------------------------------------- |
| Collection of initial source documents            | Completed                                                       |
| Reading PDFs, including scanned ones              | Completed for the five PDFs in `data collection/`               |
| Text chunking with page numbers                   | Completed                                                       |
| Embedding and vector storage                      | Completed in the notebook                                       |
| Gemini API connection                             | Tested successfully                                             |
| Retrieval (question rewriting and relevance cut-off) | Implemented; evaluation against the trader questions in progress |
| Eligibility rules                                 | Implemented for Jubilee TCIP and Britam Biashara                |
| Source references in answers                      | Implemented                                                     |
| End-to-end information assistant                  | Working in the notebook; answers being checked against sources  |
| WhatsApp chatbot integration                      | Planned                                                         |
| Separate product recommendation system            | Planned                                                         |

## Known Limitations

* **No flat premiums.** Neither business insurance document gives one (Britam gives percentage rates, TCIP gives none), so the assistant cannot say whether a product fits a trader's budget. It tells the trader to get a quote.
* **Eligibility needs insurer confirmation.** The documents do not say whether open-air or temporary stalls qualify for Britam Biashara, so the assistant never says a trader is covered.
* **OCR can make mistakes.** Transcriptions of scanned PDFs should be checked against the originals.
* **Swahili and Sheng answers** need review by a native speaker before real traders use them.
* **The "I don't have that information" message** is English only.
* The assistant gives information, not insurance advice. Eligibility and premiums must be confirmed with the insurer.

## Data and Security

* API keys and credentials should be stored securely and excluded from version control. The notebook reads the key from Colab Secrets or an environment variable.
* Generated vector databases and private or restricted source documents should not be committed unless there is a clear reason and permission to share them.
* Responses should distinguish verified product information from missing or unavailable information.
* Product details should be checked against reliable source documents before being used to guide decisions.

## Improvements

1. Add the Britam Biashara Lite brochure to `data collection/` so the notebook reads it (it is part of the document collection but is not read yet).
2. Check every answer to the 21 trader questions against the source documents, and have a native Swahili speaker review the Swahili.
3. Add eligibility rules for more products as verified premiums and terms become available.
4. Load product facts from the Excel database instead of writing them in the notebook.
5. Integrate the information assistant with WhatsApp.
6. Develop and validate the separate recommendation system.
7. Explore appropriate payment-frequency and affordability considerations for traders with irregular incomes.
