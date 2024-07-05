"""
NutriAI Chat Page Module for NutriAI.

This module contains the Streamlit page functionality for the NutriAI chatbot,
allowing users to interact with an AI-powered nutrition assistant through
a user-friendly chat interface.
"""

import streamlit as st
from utils.nutriqa import NutriAIBot
from utils.logger import logger

def initialize_session_state():
    """Initialize session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'bot' not in st.session_state:
        st.session_state.bot = NutriAIBot()

def display_chat_history():
    """Display the chat history."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def process_user_input(user_input: str) -> str:
    """
    Process user input and get bot response.

    Args:
        user_input (str): User's input message.

    Returns:
        str: Bot's response.
    """
    return st.session_state.bot.ask_question(user_input)

def show():
    """Display the NutriAI chatbot in the Streamlit app."""
    logger.info("NutriAI chatbot page started")

    # Add custom CSS to ensure chat input text is visible
    st.markdown("""
    <style>
    .stTextInput > div > div > input::placeholder {
        color: #4CAF50 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("NutriAI ChatBot 🥗💬")
    st.subheader("Your personal nutrition assistant")

    initialize_session_state()

    # Display chat history
    display_chat_history()

    # User input
    if user_input := st.chat_input("Ask me about nutrition!"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Get and display bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                bot_response = process_user_input(user_input)
            st.markdown(bot_response)
        st.session_state.messages.append({"role": "assistant", "content": bot_response})

    # Disclaimer
    st.write("---")
    st.info(
        "Disclaimer: NutriAI is an AI assistant and should not replace professional medical advice. "
        "Always consult with a qualified healthcare provider for personalized nutrition guidance."
    )

if __name__ == "__main__":
    show()
