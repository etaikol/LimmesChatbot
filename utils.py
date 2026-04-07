"""
Utility functions for Limmes Chatbot
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any


def ensure_directory_exists(directory: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory}: {e}")
        return False


def save_conversation(conversation: List[Dict[str, str]], filename: str = None) -> bool:
    """Save conversation history to a JSON file"""
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(conversation, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Conversation saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving conversation: {e}")
        return False


def load_conversation(filename: str) -> List[Dict[str, str]]:
    """Load conversation history from a JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading conversation: {e}")
        return []


def format_answer(answer: str, max_length: int = 1000) -> str:
    """Format and truncate answer if needed"""
    if len(answer) > max_length:
        return answer[:max_length] + "..."
    return answer


def get_model_info(model_name: str) -> Dict[str, Any]:
    """Get information about OpenAI models"""
    models = {
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "cost_per_1k_input": 0.0005,
            "cost_per_1k_output": 0.0015,
            "description": "Fast, cost-effective model for basic tasks"
        },
        "gpt-4o-mini": {
            "name": "GPT-4o Mini",
            "cost_per_1k_input": 0.00015,
            "cost_per_1k_output": 0.0006,
            "description": "Fast, affordable model with strong capabilities"
        },
        "gpt-4": {
            "name": "GPT-4",
            "cost_per_1k_input": 0.03,
            "cost_per_1k_output": 0.06,
            "description": "More capable, better for complex tasks"
        }
    }
    return models.get(model_name, {})


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost of API usage"""
    model_info = get_model_info(model)
    if not model_info:
        return 0.0
    
    input_cost = (input_tokens / 1000) * model_info["cost_per_1k_input"]
    output_cost = (output_tokens / 1000) * model_info["cost_per_1k_output"]
    return input_cost + output_cost


def validate_pdf_path(path: str) -> bool:
    """Validate that a PDF file exists and is readable"""
    if not os.path.exists(path):
        return False
    if not path.lower().endswith('.pdf'):
        return False
    if not os.access(path, os.R_OK):
        return False
    return True


def get_pdf_info(path: str) -> Dict[str, Any]:
    """Get information about a PDF file"""
    try:
        if not validate_pdf_path(path):
            return {"error": "File not found or not readable"}
        
        size_mb = os.path.getsize(path) / (1024 * 1024)
        return {
            "path": path,
            "size_mb": round(size_mb, 2),
            "exists": True,
            "readable": True
        }
    except Exception as e:
        return {"error": str(e)}


def format_conversation_history(messages: List[Dict[str, str]], max_messages: int = 10) -> str:
    """
    Format conversation history for use as LLM context.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        max_messages: Maximum number of recent messages to include
    
    Returns:
        Formatted string with conversation history, ready to pass to LLM
    
    Example:
        >>> messages = [
        ...     {"role": "user", "content": "What are your hours?"},
        ...     {"role": "assistant", "content": "We're open 9-5"}
        ... ]
        >>> formatted = format_conversation_history(messages)
        >>> print(formatted)
        User: What are your hours?
        Assistant: We're open 9-5
    """
    if not messages:
        return ""
    
    # Keep only recent messages
    recent = messages[-max_messages:] if len(messages) > max_messages else messages
    
    formatted_lines = []
    for msg in recent:
        role = "User" if msg.get('role') == 'user' else "Assistant"
        content = msg.get('content', '')
        formatted_lines.append(f"{role}: {content}")
    
    return "\n".join(formatted_lines)
