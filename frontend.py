import streamlit as st
from backend import get_gemini_response, summarize_session, save_interaction
from firebase_admin import firestore, auth
import firebase_admin
import time

# Initialize Firebase and Firestore
db = firestore.client()

# Title
st.title("Trustee: AI Counseling Companion")

# User authentication
def authenticate_user(email, password):
    """Authenticate a user with email and password."""
    try:
        user = auth.get_user_by_email(email)
        return user.email  # Return the user's email
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None

def sign_up_user(email, password):
    """Sign up a new user and return the user's email."""
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        st.success("Sign-up successful! Please login now.")
        return user.email
    except Exception as e:
        st.error(f"Sign-up failed: {e}")
        return None

# Login or sign-up section
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# Initialize user_uid in session state
if "user_uid" not in st.session_state:
    st.session_state.user_uid = None

# Load previous chat history from Firestore for the authenticated user
@st.cache_data(ttl=300)
def load_chat_history(user_uid):
    print("Loading chat history for user:", user_uid)
    interactions_ref = db.collection("interactions").where("user_uid", "==", user_uid).order_by("timestamp").stream()
    messages = []
    for doc in interactions_ref:
        data = doc.to_dict()
        print("Loaded interaction:", data)
        messages.append({"role": "user", "content": data.get('user_message', '')})
        messages.append({"role": "assistant", "content": data.get('assistant_response', '')})
    print("Loaded chat history:", messages)
    return messages

# Check if the user is authenticated
if st.session_state.user_email is None:
    st.subheader("Login or Sign-up to access your chats")

    # Toggle between login and sign-up
    login_tab, signup_tab = st.tabs(["Login", "Sign-up"])

    # Login Tab
    with login_tab:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            user_email = authenticate_user(email, password)
            if user_email:
                st.session_state.user_email = user_email
                st.session_state.user_uid = email  # Assuming email as the user UID
                st.success("Login successful! You can now access your chats.")
                # Reload chat history after login
                st.session_state.messages = load_chat_history(st.session_state.user_uid)

    # Sign-up Tab
    with signup_tab:
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Sign-up"):
            user_email = sign_up_user(new_email, new_password)
            if user_email:
                st.success("Sign-up successful! Please login now.")

else:
    # Load previous chats if user is authenticated
    if "messages" not in st.session_state or st.session_state.user_uid != st.session_state.user_email:

        print("Loading previous chats...")
        st.session_state.messages = load_chat_history(st.session_state.user_uid)
        print("Previous chats loaded:", st.session_state.messages)

    st.sidebar.title("Options")
    st.sidebar.write(f"Logged in as: **{st.session_state.user_email}**")

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.user_email = None
        st.session_state.user_uid = None  # Clear user_uid on logout
        st.session_state.messages = []  # Clear the chat on logout
        st.success("Logged out successfully!")

    # Button to clear chat history
    if st.sidebar.button("Delete Chat"):
        st.session_state.messages = []
        interactions_ref = db.collection('interactions').where('user_uid', '==', st.session_state.user_uid).stream()
        for doc in interactions_ref:
            doc.reference.delete()
        st.sidebar.success("Chat history cleared.")

    # Button to summarize conversation
    if st.sidebar.button("Summarize"):
        summary = summarize_session(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": f"**Summary of the session:**\n\n{summary}"})

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What's on your mind?"):
        # Check for duplicate messages in the current session
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1]["content"] == prompt:
            st.warning("You already sent this message. Please enter a new message.")
        else:
            # Append user's message only if it's not a duplicate
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Placeholder for assistant response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for response in get_gemini_response(prompt, st.session_state.messages):
                    full_response += response
                    message_placeholder.markdown(full_response + "▌")  # Display the response with a placeholder character

                # Final display of the complete response
                message_placeholder.markdown(full_response)

            # Save the conversation to Firestore
            save_interaction(st.session_state.user_uid, prompt, full_response)
