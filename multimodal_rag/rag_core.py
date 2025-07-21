import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from PIL import Image

def get_image_description(img_path: str):
    """Generates a description for a single image using Gemini Pro Vision."""
    try:
        img = Image.open(img_path)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = "Describe this image in detail. If it is a chart or graph, explain what it shows and its key takeaways. If it is a photo or diagram, describe the main elements."
        response = model.generate_content([prompt, img])
        return response.text
    except Exception as e:
        print(f"Error describing image {img_path}: {e}")
        return None

def create_vector_store(parsed_data: list, vector_store_path="faiss_index"):
    """Creates a FAISS vector store from parsed PDF data."""
    all_chunks = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    for page_data in parsed_data:
        text_chunks = text_splitter.split_text(page_data["text"])
        for chunk in text_chunks:
            all_chunks.append({"type": "text", "content": chunk, "page": page_data["page_number"]})
        
        if page_data["visuals"]:
            print(f"Describing visuals for page {page_data['page_number']}...")
            for img_path in page_data["visuals"]:
                description = get_image_description(img_path)
                if description:
                    all_chunks.append({"type": "image_summary", "content": description, "page": page_data["page_number"], "source_image": img_path})

    contents_to_embed = [chunk["content"] for chunk in all_chunks]
    metadata = all_chunks

    print("Embedding all text chunks and image descriptions...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    vector_store = FAISS.from_texts(contents_to_embed, embedding=embeddings, metadatas=metadata)
    
    vector_store.save_local(vector_store_path)
    print(f"Vector store created and saved at '{vector_store_path}'.")
    return vector_store

def answer_question(question: str, chat_history: list, vector_store_path="faiss_index"):
    """Answers a question using the vector store and conversation history."""
    print("Loading the vector store...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.7)

    # 1. Prompt to rewrite the user's question based on history
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Given a chat history and the latest user question, formulate a standalone question which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

    # 2. Prompt to answer the question, given the retrieved context
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant for answering questions about a document. Your answers should be concise and clear. Use ONLY the following retrieved context to answer the question. If you don't know the answer, just say that you don't know. Do not make up an answer.\n\nContext:\n{context}"),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    Youtube_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # 3. Create the final conversational chain
    rag_chain = create_retrieval_chain(history_aware_retriever, Youtube_chain)

    print("Generating the answer with conversation history...")
    response = rag_chain.invoke({"input": question, "chat_history": chat_history})
    
    answer = response.get("answer", "I could not find an answer.")
    context_docs = response.get("context", [])
    
    print("\n--- Answer ---")
    print(answer)
    
    return {
        "output_text": answer,
        "input_documents": context_docs
    }