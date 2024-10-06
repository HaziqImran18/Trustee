import firebase_admin
from firebase_admin import firestore, auth
from firebase_config import *  # Import Firebase initialization
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Initialize Firestore
db = firestore.client()

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the Gemini Pro model and chat
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat()

# System prompt for context
system_prompt = """You are an AI assistant that provides [specific service, e.g., counseling, educational help, customer support, etc.] to users. Your responses should be professional, friendly, and helpful, focusing on providing accurate and concise information. 

- **Tone**: Be wise friend, empathetic, clear, and approachable.
- **Behavior**: 
   - Always provide accurate and fact-checked information.
   - Avoid technical jargon unless specifically asked for it. When you use technical terms, explain them in simple language.
   - Keep your responses concise and to the point, but feel free to elaborate when necessary.
   - Offer suggestions or solutions in a proactive way.
   - If the user asks something outside of your knowledge or scope, politely let them know.
- **Style**: Your tone should vary based on the context:
   - For serious topics, like mental health or sensitive issues, be empathetic and supportive.
   - For educational queries, be explanatory and informative.
   - For casual or general conversations, maintain a friendly and conversational tone.
- **Limitations**:
   - Never provide harmful, biased, or unethical advice.
   - Keep each response under 5,000 characters, ensuring clarity and focus.
   - If you don’t know something, admit it honestly but offer suggestions on where to find more information or ask for more details from the user.
"""

def save_interaction(user_uid, user_message, assistant_response):
    """Save interaction with user UID to ensure data segregation."""
    db.collection('interactions').add({
        'user_uid': user_uid,
        'user_message': user_message,
        'assistant_response': assistant_response,
        'timestamp': firestore.SERVER_TIMESTAMP
    })

def get_gemini_response(prompt, history):
    # Generate summary for context
    summary = summarize_session(history)
    
    # Combine system prompt, summary, and user prompt
    combined_prompt = f"{system_prompt}\n\nConversation Summary:\n{summary}\n\nUser: {prompt}\nAssistant:"
    
    try:
        response = chat.send_message(combined_prompt)
        full_response = response.text
    except AttributeError:
        full_response = "Error: Unable to extract response text."
    except Exception as e:
        full_response = f"An error occurred: {str(e)}. Please try again later."
    
    history.append({"role": "assistant", "content": full_response})
    
    return full_response

def summarize_session(history):
    """Generate a high-level summary of the session using Gemini."""
    conversation_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history])
    prompt = f"Please summarize the following conversation:\n\n{conversation_history}\n\nSummary:"

    try:
        response = chat.send_message(prompt)
        full_response = response.text
        summary = full_response[:500]  # Truncate to a maximum of 500 characters
    except AttributeError:
        summary = "Error: Unable to extract response text."
    except Exception as e:
        summary = f"An error occurred: {str(e)}. Please try again later."
    
    return summary
