# CogniQuery Pro: A Multi-Modal RAG Engine

**Live Demo:** [Link to your deployed Streamlit App will go here after deployment]

CogniQuery Pro is a sophisticated Question-Answering system built to understand and converse with complex, multi-format data sources. It leverages a multi-modal Retrieval-Augmented Generation (RAG) architecture to analyze and extract insights from both text and visual elements within PDFs, spreadsheets, emails, and live websites.

## Core Features

* 🧠 **Multi-Format Ingestion:** Built with a modular framework to handle PDFs, spreadsheets (.csv, .xlsx), emails (.eml), and live websites.
* 👁️ **Multi-Modal Understanding:** AI-powered vision analyzes charts, graphs, and images found within documents, making them fully searchable.
* 💬 **Conversational Memory:** Remembers the context of the chat to answer follow-up questions naturally, creating a true conversational experience.
* 🔎 **Interactive Source Verification:** Allows users to inspect the exact text snippets or images used by the AI to generate an answer, ensuring trust and transparency.

## Tech Stack

* **Language:** Python
* **Application Framework:** Streamlit
* **AI/ML Libraries:** LangChain, Google Gemini (for LLM and Vision), FAISS (for vector search)
* **Data Parsing:** PyMuPDF, Pandas, BeautifulSoup

## Setup & Running Locally

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/delta96040/Multi-modal-document-chatbot.git](https://github.com/delta96040/Multi-modal-document-chatbot.git)
    cd Multi-modal-document-chatbot
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On MacOS/Linux
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up your API key:**
    * Create a file named `.env` in the root directory.
    * Add your Google Gemini API key: `GOOGLE_API_KEY="YOUR_API_KEY"`
5.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

## Challenges & Solutions

* **Challenge:** Handling diverse data sources (PDFs, URLs, etc.) within a single, coherent system.
    * **Solution:** I designed a modular parser architecture. The main application identifies the data type and routes it to a specialized parsing function. All parsers output a standardized data structure, which is then fed into a single, unified RAG pipeline. This makes the system clean and easily extensible.

* **Challenge:** Extracting meaningful information from visuals like charts and diagrams, which are often stored as vector graphics, not simple images.
    * **Solution:** I implemented a hybrid visual parser. It first extracts any standard embedded images. It then uses PyMuPDF's `get_drawings()` method to detect vector graphics, calculates their bounding box, and renders a targeted, high-resolution image of just that graphic. This ensures no visual information is lost.

## Future Improvements

* **Advanced Table Recognition:** Implement a dedicated library to parse tables from PDFs into a structured format (like Markdown) for more precise Q&A on tabular data.
* **Asynchronous Processing:** For very large documents or slow websites, move the ingestion and processing pipeline to a background worker (e.g., using Celery) to keep the UI fully responsive.
* **User Accounts:** Add user authentication to allow individuals to save and manage their own library of processed documents.