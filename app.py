import streamlit as st
from pathlib import Path
# Import all parser functions
from multimodal_rag.parser import parse_pdf_comprehensive, parse_spreadsheet, parse_email, parse_website
from multimodal_rag.rag_core import create_vector_store, answer_question

VECTOR_STORE_PATH = "faiss_index_streamlit"

st.set_page_config(page_title="CogniQuery Pro", page_icon="🧠", layout="wide")

st.title("🧠 CogniQuery Pro: Chat with Documents, Spreadsheets, Emails & Websites")

# Initialize session state variables
if "processed" not in st.session_state:
    st.session_state.processed = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for inputs
with st.sidebar:
    st.header("Upload Your Data")
    
    # Input for file uploads
    uploaded_file = st.file_uploader(
        "Upload a file (.pdf, .csv, .xlsx, .eml)", 
        type=["pdf", "csv", "xlsx", "eml"]
    )
    
    st.markdown("---")
    
    # Input for URL
    url_input = st.text_input("Or enter a website URL")

    if st.button("Process"):
        parsed_data = None
        # Priority to file upload, then URL
        if uploaded_file:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                temp_dir = Path("temp_uploads")
                temp_dir.mkdir(exist_ok=True)
                file_path = temp_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                ext = file_path.suffix.lower()
                if ext == ".pdf":
                    parsed_data = parse_pdf_comprehensive(str(file_path))
                elif ext in [".csv", ".xlsx"]:
                    parsed_data = parse_spreadsheet(str(file_path))
                elif ext == ".eml":
                    parsed_data = parse_email(str(file_path))

        elif url_input:
            with st.spinner(f"Processing {url_input}..."):
                parsed_data = parse_website(url_input)
        
        else:
            st.warning("Please upload a file or enter a URL.")

        if parsed_data:
            st.session_state.messages = []
            with st.spinner("Creating knowledge base..."):
                create_vector_store(parsed_data, vector_store_path=VECTOR_STORE_PATH)
                st.session_state.processed = True
                st.session_state.vector_store_path = VECTOR_STORE_PATH
            st.success("Processing complete! You can now ask questions.")
        elif not uploaded_file and not url_input:
            pass # Avoid showing error if nothing was submitted
        else:
            st.error("Failed to process the provided data. Please check the format or URL.")


# Main chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about your data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.processed:
        with st.spinner("Thinking..."):
            response_data = answer_question(
                question=prompt, 
                chat_history=st.session_state.messages,
                vector_store_path=st.session_state.vector_store_path
            )
            answer = response_data["output_text"]
            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)
                with st.expander("Show Sources"):
                    if response_data["input_documents"]:
                        for doc in response_data["input_documents"]:
                            st.markdown(f"---")
                            st.write(f"**Source:** {doc.page_content}")
                    else:
                        st.write("No specific sources were retrieved.")
    else:
        st.warning("Please upload/enter data and click 'Process' first.")