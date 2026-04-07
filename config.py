"""
Configuration settings for Limmes Chatbot
"""

# LLM Settings
MODEL_NAME = "gpt-4o-mini"  # Cheaper and faster than gpt-3.5-turbo, better quality
EMBEDDING_MODEL = "text-embedding-3-small"  # Cheaper than ada-002, better performance
MODEL_TEMPERATURE = 0.7

# Text Processing
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
RETRIEVAL_K = 4

# Storage
VECTORSTORE_DIR = ".chroma"
DEFAULT_PDF_PATH = "your_doc.pdf"
PDF_DIRECTORY = "pdfs"  # NEW: Load all PDFs from this directory

# Display
SHOW_SOURCE_DOCUMENTS = True
SAVE_CONVERSATIONS = True  # NEW: Save chat history to file
MAX_CONVERSATION_HISTORY = 10  # NEW: Keep last N messages in memory

# System Prompt (NEW: Customize bot behavior per client)
SYSTEM_PROMPT = """You are a helpful AI assistant. Answer questions based on the provided documents.
If you don't know the answer from the documents, say "I don't have that information in the documents provided."
Be concise and friendly."""

# Optional: Client-specific configuration
CLIENT_NAME = "Default Client"  # NEW: Name for personalization