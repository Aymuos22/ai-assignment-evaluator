import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# Only create LLM if key is set (avoids crash on Vercel when env not yet configured)
if os.getenv("GROQ_API_KEY"):
    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
    )
else:
    llm = None
