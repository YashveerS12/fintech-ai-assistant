from langchain_groq import ChatGroq
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os

load_dotenv()

print("Loading fintech knowledge base...")
loader = TextLoader("docs/fintech.txt")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = splitter.split_documents(documents)
print(f"Created {len(chunks)} chunks")

print("Creating vector store...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

print("\nFintech Assistant Ready!")
print("Type 'exit' to quit")
print("-" * 40)

while True:
    question = input("\nAsk anything: ")
    
    if question.lower() == "exit":
        print("Bye!")
        break

    docs = retriever.invoke(question)
    context = "\n".join([doc.page_content for doc in docs])

    response = llm.invoke([
        SystemMessage(content="You are a fintech expert assistant. Answer only using the context provided: " + context),
        HumanMessage(content=question)
    ])

    print(f"\nAnswer: {response.content}")
    print("-" * 40)
