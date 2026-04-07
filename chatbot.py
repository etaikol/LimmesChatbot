"""
RAG Chatbot - Retrieval-Augmented Generation using LangChain
A document-based QA system that answers questions about PDF documents.

Features:
- Conversation memory (context awareness)
- Multiple PDF support (load entire directories)
- System prompts (customizable per client)
- Graceful error handling (user-friendly messages)
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from config import (
    VECTORSTORE_DIR,
    EMBEDDING_MODEL,
    MODEL_NAME,
    MODEL_TEMPERATURE,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    RETRIEVAL_K,
    DEFAULT_PDF_PATH,
    PDF_DIRECTORY,
    SHOW_SOURCE_DOCUMENTS,
    SAVE_CONVERSATIONS,
    MAX_CONVERSATION_HISTORY,
    SYSTEM_PROMPT,
    CLIENT_NAME,
)


# ============================================================================
# 1. GRACEFUL ERROR HANDLING
# ============================================================================

class ChatbotError(Exception):
    """Custom exception for user-friendly error messages"""
    pass


def handle_openai_error(error):
    """Convert OpenAI errors to user-friendly messages"""
    error_str = str(error).lower()
    
    if "invalid_api_key" in error_str or "unauthorized" in error_str:
        return "❌ API Key Error: Your OpenAI API key is invalid or expired.\n   Please check your .env file and update OPENAI_API_KEY at https://platform.openai.com/api-keys"
    
    elif "rate_limit" in error_str:
        return "❌ Rate Limit: You've hit OpenAI's rate limit.\n   Please wait a moment and try again."
    
    elif "insufficient_quota" in error_str or "quota" in error_str:
        return "❌ Quota Error: Your OpenAI account has run out of credits.\n   Please add credits at https://platform.openai.com/account/billing/overview"
    
    elif "connection" in error_str or "timeout" in error_str:
        return "❌ Connection Error: Cannot reach OpenAI API.\n   Check your internet connection or try again later."
    
    elif "model" in error_str and "not found" in error_str:
        return f"❌ Model Error: The model '{MODEL_NAME}' is not available.\n   Check config.py and choose a valid model."
    
    else:
        return f"❌ API Error: {str(error)}\n   Please check your configuration and try again."


def safe_openai_call(func, *args, **kwargs):
    """Safely call OpenAI APIs with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_msg = handle_openai_error(e)
        raise ChatbotError(error_msg) from e


# ============================================================================
# 2. LOAD MULTIPLE PDFs FROM DIRECTORY
# ============================================================================

def load_pdf_directory(directory):
    """Load all PDFs from a directory"""
    pdf_dir = Path(directory)
    
    if not pdf_dir.exists():
        raise ChatbotError(
            f"❌ Directory Error: '{directory}' does not exist.\n"
            f"   Create a '{directory}' folder and add your PDF files there."
        )
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        raise ChatbotError(
            f"❌ No PDFs Found: '{directory}' folder is empty.\n"
            f"   Add PDF files to the '{directory}' folder and try again."
        )
    
    print(f"\n📚 Found {len(pdf_files)} PDF file(s) to load:")
    for pdf_file in sorted(pdf_files):
        print(f"   ✓ {pdf_file.name}")
    
    return sorted(pdf_files)


def load_and_process_pdfs(pdf_paths):
    """Load and process multiple PDFs"""
    all_chunks = []
    
    for pdf_path in pdf_paths:
        try:
            print(f"\n📄 Loading PDF: {pdf_path.name}")
            loader = PyPDFLoader(str(pdf_path))
            pages = loader.load()
            print(f"✅ Loaded {len(pages)} pages from {pdf_path.name}")
            
            # Add source filename to metadata for tracking
            for page in pages:
                page.metadata['pdf_filename'] = pdf_path.name
            
            # Split into chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP
            )
            chunks = splitter.split_documents(pages)
            all_chunks.extend(chunks)
            print(f"✅ Created {len(chunks)} chunks")
            
        except Exception as e:
            raise ChatbotError(
                f"❌ PDF Loading Error: Could not load '{pdf_path.name}'\n"
                f"   Make sure it's a valid PDF file.\n"
                f"   Error: {str(e)}"
            )
    
    if not all_chunks:
        raise ChatbotError(
            "❌ No Content: PDFs have no readable content.\n"
            "   Make sure your PDFs contain text (not just images)."
        )
    
    print(f"\n✅ Total: {len(all_chunks)} chunks from {len(pdf_paths)} PDF(s)")
    return all_chunks


def load_and_process_pdf(pdf_path):
    """Load single PDF (backward compatible)"""
    print(f"\n📄 Loading PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        raise ChatbotError(
            f"❌ File Not Found: '{pdf_path}' does not exist.\n"
            f"   Create or download a PDF and place it in the project folder."
        )
    
    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        print(f"✅ Loaded {len(pages)} pages")
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        chunks = splitter.split_documents(pages)
        print(f"✅ Created {len(chunks)} chunks")
        return chunks
    except Exception as e:
        raise ChatbotError(
            f"❌ PDF Loading Error: {str(e)}\n"
            f"   Make sure the file is a valid PDF with readable text."
        )


# ============================================================================
# 3. CONVERSATION MEMORY
# ============================================================================

class ConversationMemory:
    """Manage conversation history with file persistence"""
    
    def __init__(self, max_history=MAX_CONVERSATION_HISTORY):
        self.history = []
        self.max_history = max_history
        self.conversation_file = Path("conversation_history.json")
        self.load_history()
    
    def add_message(self, role, content):
        """Add message to history"""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent messages (prevent infinite growth)
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history:]
        
        # Auto-save if enabled
        if SAVE_CONVERSATIONS:
            self.save_history()
    
    def get_recent(self, n=None):
        """Get last N messages (for context)"""
        if n is None:
            n = self.max_history
        return self.history[-n:] if self.history else []
    
    def get_messages_str(self):
        """Format messages for context (recent messages only)"""
        recent = self.get_recent(n=10)  # Only keep last 10 for context
        if not recent:
            return ""
        
        formatted = []
        for msg in recent:
            role = "User" if msg['role'] == 'user' else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def save_history(self):
        """Save conversation to file"""
        try:
            with open(self.conversation_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            pass  # Silently fail to not interrupt chat
    
    def load_history(self):
        """Load conversation from file"""
        try:
            if self.conversation_file.exists():
                with open(self.conversation_file, 'r') as f:
                    self.history = json.load(f)
                print(f"✅ Loaded {len(self.history)} messages from history")
        except Exception as e:
            print(f"⚠️  Could not load history: {e}")  # Dev visibility during debugging
    
    def clear_history(self):
        """Clear all history"""
        self.history = []
        if self.conversation_file.exists():
            self.conversation_file.unlink()




def get_vectorstore_metadata():
    """Read metadata about cached vectorstore"""
    metadata_file = Path(VECTORSTORE_DIR) / "metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_vectorstore_metadata(pdf_paths, file_hash):
    """Save metadata about current vectorstore"""
    Path(VECTORSTORE_DIR).mkdir(parents=True, exist_ok=True)
    metadata = {
        "pdf_paths": [str(p) for p in pdf_paths],
        "file_hash": file_hash,
        "created_at": datetime.now().isoformat(),
        "embedding_model": EMBEDDING_MODEL
    }
    try:
        with open(Path(VECTORSTORE_DIR) / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        pass  # Silently fail


def get_file_hash(file_paths):
    """Get hash of PDF files to detect changes"""
    try:
        total_size = 0
        total_time = 0
        for file_path in file_paths:
            file_stat = os.stat(file_path)
            total_size += file_stat.st_size
            total_time += file_stat.st_mtime
        return f"{total_size}_{total_time}"
    except Exception:
        return None


def load_existing_vectorstore():
    """Load vectorstore from disk if it exists"""
    if not Path(VECTORSTORE_DIR).exists():
        return None
    
    print("\n📂 Checking for cached vector store...")
    try:
        embeddings = safe_openai_call(OpenAIEmbeddings, model=EMBEDDING_MODEL)
        vectorstore = safe_openai_call(
            Chroma,
            persist_directory=str(VECTORSTORE_DIR),
            embedding_function=embeddings
        )
        
        if vectorstore._collection.count() > 0:
            print(f"✅ Loaded cached vector store ({vectorstore._collection.count()} embeddings)")
            return vectorstore
    except ChatbotError:
        raise
    except Exception as e:
        print(f"⚠️  Could not load existing vectorstore: {e}")
    
    return None


def create_vectorstore(chunks, pdf_paths):
    """Create new vectorstore and persist to disk"""
    print("\n🔗 Creating embeddings and storing in ChromaDB...")
    try:
        embeddings = safe_openai_call(OpenAIEmbeddings, model=EMBEDDING_MODEL)
        vectorstore = safe_openai_call(
            Chroma.from_documents,
            chunks,
            embeddings,
            persist_directory=str(VECTORSTORE_DIR),
            collection_name="documents"
        )
        
        # Save metadata for future checks
        file_hash = get_file_hash(pdf_paths)
        save_vectorstore_metadata(pdf_paths, file_hash)
        
        print(f"✅ Vector store created and saved to {VECTORSTORE_DIR}")
        print(f"💾 Embeddings cached for instant load on next startup")
        return vectorstore
    except ChatbotError:
        raise
    except Exception as e:
        raise ChatbotError(
            f"❌ Vector Store Error: Could not create embeddings\n"
            f"   Check your OpenAI API key and internet connection.\n"
            f"   Error: {str(e)}"
        )


def should_rebuild_vectorstore(pdf_paths):
    """Check if vectorstore needs to be rebuilt"""
    metadata = get_vectorstore_metadata()
    if metadata is None:
        return True
    
    # Check if PDF paths changed
    stored_paths = set(metadata.get("pdf_paths", []))
    current_paths = set(str(p) for p in pdf_paths)
    
    if stored_paths != current_paths:
        print(f"📝 PDF files changed, rebuilding vectorstore...")
        return True
    
    # Check if PDF files have been modified
    current_hash = get_file_hash(pdf_paths)
    if current_hash != metadata.get("file_hash"):
        print(f"📝 PDF files have been updated, rebuilding vectorstore...")
        return True
    
    return False


def setup_qa_chain(vectorstore):
    """Setup LCEL chain with system prompt and conversation history"""
    print("\n🤖 Setting up QA chain...")
    try:
        llm = safe_openai_call(
            ChatOpenAI,
            model=MODEL_NAME,
            temperature=MODEL_TEMPERATURE
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})
        
        # Enhanced prompt with system prompt AND conversation history
        prompt = ChatPromptTemplate.from_template("""
{system_prompt}

{history}

Context from documents:
{context}

Question: {question}
""")
        
        from langchain_core.runnables import RunnableLambda
        
        chain = (
            {
                "system_prompt": RunnableLambda(lambda x: SYSTEM_PROMPT),
                "history": RunnableLambda(lambda x: ""),
                "context": retriever,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        print("✅ QA chain ready")
        return chain, retriever
    except ChatbotError:
        raise
    except Exception as e:
        raise ChatbotError(
            f"❌ Chain Setup Error: {str(e)}\n"
            f"   Could not initialize the QA chain. Check your configuration."
        )


def run_chatbot(chain, retriever, memory):
    """Run interactive chatbot with memory"""
    print("\n" + "="*60)
    print(f"🚀 RAG Chatbot Started! ({CLIENT_NAME})")
    print("Type 'quit' to exit | 'clear' to clear history")
    print("="*60 + "\n")

    while True:
        try:
            question = input("\n👤 You: ").strip()
            
            if question.lower() == "quit":
                print("\n👋 Goodbye!")
                break
            
            if question.lower() == "clear":
                memory.clear_history()
                print("🗑️  Conversation history cleared")
                continue
            
            if not question:
                continue
            
            # Add user question to memory
            memory.add_message("user", question)
            
            print("\n🤔 Thinking...")
            
            try:
                # FORMAT CONVERSATION HISTORY FOR CONTEXT
                history_context = memory.get_messages_str()
                if history_context:
                    history_context = "Previous conversation:\n" + history_context + "\n"
                
                # PASS HISTORY TO CHAIN
                answer = chain.invoke({
                    "question": question,
                    "history": history_context
                })
                
                # Add assistant response to memory
                memory.add_message("assistant", answer)
                
                print(f"\n🤖 Bot: {answer}")
                
                # Show sources
                if SHOW_SOURCE_DOCUMENTS:
                    docs = retriever.invoke(question)
                    if docs:
                        print("\n📚 Sources:")
                        for i, doc in enumerate(docs, 1):
                            source = doc.metadata.get('pdf_filename', doc.metadata.get('source', 'Unknown'))
                            page = doc.metadata.get('page', 'N/A')
                            print(f"  {i}. {source} (Page {page})")
            
            except ChatbotError as e:
                print(f"\n{e}")
            except Exception as e:
                error_msg = handle_openai_error(e)
                print(f"\n{error_msg}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


def main():
    """Main entry point with complete feature support"""
    try:
        # Load API key
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ChatbotError(
                "❌ API Key Error: OPENAI_API_KEY not found!\n"
                "   1. Create a .env file (copy .env.example)\n"
                "   2. Add your OpenAI API key: OPENAI_API_KEY=sk-...\n"
                "   3. Get a key at: https://platform.openai.com/api-keys"
            )
        
        # Step 1: Load PDFs (try directory first, then fallback to single file)
        pdf_paths = None
        try:
            pdf_paths = load_pdf_directory(PDF_DIRECTORY)
        except ChatbotError:
            print("\n⚠️  PDF directory not found, trying single PDF mode...")
            pdf_paths = [Path(DEFAULT_PDF_PATH)]
        
        # Step 2: Try to load cached vectorstore
        vectorstore = None
        # Step 3: Check if vectorstore needs rebuild (before loading)
        needs_rebuild = should_rebuild_vectorstore(pdf_paths)
        
        try:
            if needs_rebuild:
                # Skip loading if we need to rebuild
                vectorstore = None
            else:
                vectorstore = load_existing_vectorstore()
        except ChatbotError:
            raise
        
        # Step 4: Create vectorstore if needed
        if vectorstore is None:
            try:
                if len(pdf_paths) > 1:
                    chunks = load_and_process_pdfs(pdf_paths)
                else:
                    chunks = load_and_process_pdf(str(pdf_paths[0]))
                vectorstore = create_vectorstore(chunks, pdf_paths)
            except ChatbotError:
                raise
        
        # Step 5: Setup QA chain
        chain, retriever = setup_qa_chain(vectorstore)
        
        # Step 6: Initialize conversation memory
        memory = ConversationMemory()
        
        # Step 6: Start chatbot
        run_chatbot(chain, retriever, memory)
    
    except ChatbotError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal Error: {str(e)}")
        print("   This is unexpected. Please check your configuration and try again.")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
