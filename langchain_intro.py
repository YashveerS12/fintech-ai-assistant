from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGroq(
   model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

response = llm.invoke([
    HumanMessage(content="who is cm of uttar pradesh?")
])

print(response.content)