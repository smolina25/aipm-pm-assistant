import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# Setup the LLM
# You can switch models here easily
LLM_MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0.3

llm = ChatGroq(model=LLM_MODEL, temperature=TEMPERATURE)
