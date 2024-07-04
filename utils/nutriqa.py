"""
NutriAI Bot Module for NutriAI.

This module contains the core functionality for the NutriAI chatbot,
including configuration, API handling, and bot logic. It allows
users to interact with an AI-powered nutrition assistant.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_together import ChatTogether
from utils.logger import logger

# Load environment variables
load_dotenv()

class NutriAIBotConfig:
    """Configuration class for NutriAI application."""

    TOGETHER_API_KEY: str = os.getenv("TOGETHER_API_KEY")
    MODEL_NAME: str = "mistralai/Mixtral-8x22B-Instruct-v0.1"
    TEMPERATURE: float = 0.6

class TogetherAIHandler:
    """Handles interactions with the Together AI API."""

    def __init__(self):
        """Initialize the Together AI handler."""
        logger.info("Initializing Together AI handler")
        if not NutriAIBotConfig.TOGETHER_API_KEY:
            raise ValueError("TOGETHER_API_KEY environment variable is not set")
        self.chat_model = ChatTogether(
            together_api_key=NutriAIBotConfig.TOGETHER_API_KEY,
            model=NutriAIBotConfig.MODEL_NAME,
            temperature=NutriAIBotConfig.TEMPERATURE
        )
        self.system_prompt = """
        You are NutriBot for NutriAI site, a friendly AI assistant specializing in nutrition. 
        Respond to questions about diet, healthy eating, food recommendations, vitamins, and minerals. 
        For meal plans, recipes, or detailed food nutrition info, suggest using specific NutriAI features:
        - For meal plans: "Try NutriAI Meal Plan feature"
        - For recipes: "Try NutriAI Recipe Recommender feature"
        - For nutrition info: "Try NutriAI Food Analysis feature"
        If asked about non-nutrition topics, politely explain you're focused on nutrition and offer to help with diet-related questions. 
        Keep responses concise, fun and friendly, and informative!
        """

    def get_model_response(self, input_text: str) -> str:
        """
        Get response from Together AI's Mixtral model.

        Args:
            input_text (str): The input text for the model.

        Returns:
            str: The generated response text.

        Raises:
            Exception: If there's an error in the API request.
        """
        logger.info("Sending request to Together AI API")
        try:
            prompt_with_input = f"{self.system_prompt}\nUser: {input_text}\nAssistant:"
            response = self.chat_model.invoke(prompt_with_input)
            return response.content
        except Exception as e:
            logger.error(f"Error in Together AI API request: {e}")
            raise

class NutriAIBot:
    """Manages the chatbot's interactions and responses."""

    def __init__(self):
        """Initialize the NutriAIBot."""
        logger.info("Initializing NutriAIBot")
        self.ai_handler = TogetherAIHandler()

    def ask_question(self, question: str) -> str:
        """
        Ask a question to the NutriAI bot and get a response.

        Args:
            question (str): The question to ask.

        Returns:
            str: The response from the bot.
        """
        logger.info(f"Processing question: {question}")
        try:
            return self.ai_handler.get_model_response(question)
        except Exception as e:
            logger.error(f"Error in processing question: {e}")
            return "I apologize, but I encountered an error while processing your request. Please try again later."
