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
    MODEL_NAME: str = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
    TEMPERATURE: float = 0.6

class TogetherAIHandler:
    """Handles interactions with the Together AI API."""

    def __init__(self):
        """Initialize the Together AI handler."""
        logger.info("Initializing Together AI handler")
        if not NutriAIBotConfig.TOGETHER_API_KEY:
            logger.error("TOGETHER_API_KEY environment variable is not set")
            raise ValueError("TOGETHER_API_KEY environment variable is not set")
        
        try:
            self.chat_model = ChatTogether(
                together_api_key=NutriAIBotConfig.TOGETHER_API_KEY,
                model=NutriAIBotConfig.MODEL_NAME,
                temperature=NutriAIBotConfig.TEMPERATURE
            )
            logger.info(f"Successfully initialized Together AI with model: {NutriAIBotConfig.MODEL_NAME}")
            
            self.system_prompt = """
            You are NutriBot for NutriAI site, a friendly AI assistant specializing in nutrition. 
            Respond to questions about fitness, diet, healthy eating, food recommendations, vitamins, and minerals. 
            For meal plans, recipes, or detailed food nutrition info, or for generating the fun quizzes suggest and direct them using specific NutriAI features like:
            - For meal plans: "Try NutriAI Meal Plan feature"
            - For recipes: "Try NutriAI Recipe Finder feature"
            - For nutrition info: "Try NutriAI Food Insight feature"
            - For ingredient checker: "Try NutriAI Ingredient Checker feature"
            - For generating quiz: "Try NutriAI Quiz feature"
            If asked about non-nutrition topics, politely explain you're focused on nutrition and offer to help with diet-related questions. 
            Keep responses concise, fun and friendly, and informative!
            """
        except Exception as e:
            logger.error(f"Failed to initialize Together AI handler: {str(e)}")
            raise

    def get_model_response(self, input_text: str) -> str:
        """
        Get response from Together AI's Llama model.

        Args:
            input_text (str): The input text for the model.

        Returns:
            str: The generated response text.

        Raises:
            Exception: If there's an error in the API request.
        """
        try:
            logger.info("Sending request to Together AI API")
            prompt_with_input = f"{self.system_prompt}\nUser: {input_text}\nAssistant:"
            response = self.chat_model.invoke(prompt_with_input)
            logger.info("Successfully received response from Together AI API")
            return response.content
        except Exception as e:
            logger.error(f"Error in Together AI API request: {str(e)}")
            return "I apologize, but I encountered an error while processing your request. Please try again later."

class NutriAIBot:
    """Manages the chatbot's interactions and responses."""

    def __init__(self):
        """Initialize the NutriAIBot."""
        logger.info("Initializing NutriAIBot")
        try:
            self.ai_handler = TogetherAIHandler()
        except Exception as e:
            logger.error(f"Failed to initialize NutriAIBot: {str(e)}")
            raise

    def ask_question(self, question: str) -> str:
        """
        Ask a question to the NutriAI bot and get a response.

        Args:
            question (str): The question to ask.

        Returns:
            str: The response from the bot.
        """
        try:
            logger.info(f"Processing question: {question}")
            response = self.ai_handler.get_model_response(question)
            logger.info("Successfully processed question")
            return response
        except Exception as e:
            logger.error(f"Error in processing question: {str(e)}")
            return "I apologize, but I encountered an error while processing your request. Please try again later."
