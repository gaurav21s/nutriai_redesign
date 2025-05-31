"""
Recipe Generation Module
This module provides functionality for generating recipes using the Groq API via LangChain.
It can generate normal recipes, healthier alternatives, and new healthy recipes.

Classes:
    GroqHandler: Handles interactions with the Groq API using LangChain.
    RecipeGenerator: Generates recipes based on user input.

Todo:
    * Implement error handling for API requests
    * Add caching mechanism for frequently requested recipes
    * Implement rate limiting to avoid API overuse
"""

import os
from typing import Literal
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from utils.logger import logger

# Load environment variables
load_dotenv()

class GroqHandler:
    """Handles interactions with the Groq API using LangChain."""

    def __init__(self):
        """Initialize the GroqHandler."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY environment variable is not set")
            raise ValueError("GROQ_API_KEY environment variable is not set")
        
        try:
            self.llm = ChatGroq(
                groq_api_key=api_key,
                # Updated to use more cost-effective model
                model="llama-3.3-70b-versatile",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
            )
            logger.info("Successfully initialized Groq with model: llama-3.3-70b-versatile")
        except Exception as e:
            logger.error(f"Failed to initialize Groq handler: {str(e)}")
            raise

    def get_model_response(self, input_text: str) -> str:
        """Get a response from the Groq model for the given input text."""
        try:
            logger.info("Sending request to Groq API")
            messages = [
                ("system", "You are a helpful assistant that generates recipes."),
                ("human", input_text),
            ]
            response = self.llm.invoke(messages)
            logger.info("Successfully received response from Groq API")
            return response.content
        except Exception as e:
            logger.error(f"Error in Groq API request: {str(e)}")
            return "I apologize, but I'm currently unable to generate a recipe. Please try again later or contact support if the issue persists."

class RecipeGenerator:
    """Generates recipes based on user input."""

    def __init__(self):
        """Initialize the RecipeGenerator."""
        try:
            logger.info("Initializing RecipeGenerator")
            self.groq_handler = GroqHandler()
        except Exception as e:
            logger.error(f"Failed to initialize RecipeGenerator: {str(e)}")
            raise

    def generate_recipe(self, dish_name: str, recipe_type: Literal["normal", "healthier", "new_healthy"]) -> str:
        """
        Generate a recipe based on the given dish name and recipe type.

        Args:
            dish_name (str): The name of the dish or a general description for new recipes.
            recipe_type (Literal["normal", "healthier", "new_healthy"]): The type of recipe to generate.

        Returns:
            str: The generated recipe as a formatted string.
        """
        try:
            logger.info(f"Generating {recipe_type} recipe for: {dish_name}")
            prompt = self._get_recipe_prompt(dish_name, recipe_type)
            recipe = self.groq_handler.get_model_response(prompt)
            logger.info("Successfully generated recipe")
            return recipe
        except Exception as e:
            logger.error(f"Error generating recipe: {str(e)}")
            return "I apologize, but I'm currently unable to generate a recipe. Please try again later or contact support if the issue persists."

    @staticmethod
    def _get_recipe_prompt(dish_name: str, recipe_type: str) -> str:
        """Generate the prompt for recipe generation."""
        type_instructions = {
            "normal": f"Create a recipe for {dish_name}.",
            "healthier": f"Create a healthier version of {dish_name}.",
            "new_healthy": f"Create a new healthy and trendy recipe inspired by {dish_name}."
        }
        return f"""
        {type_instructions[recipe_type]}
        Format the output as follows:
        Recipe Name: [Name of the recipe]
        Ingredients:
        1. [quantity] [ingredient]
        2. [quantity] [ingredient]
        ...
        Steps:
        1. [Step description]
        2. [Step description]
        ...
        Ingredient List: [ingredient1, ingredient2, ...]
        {'Explanation (briefly why this version is healthier):' if recipe_type == "healthier" else ''}
        """

# Example usage
# if __name__ == "__main__":
#     try:
#         recipe_generator = RecipeGenerator()
        
#         # Generate a normal recipe
#         normal_recipe = recipe_generator.generate_recipe("Spaghetti Carbonara", "normal")
#         # Generate a healthier alternative recipe
#         healthier_recipe = recipe_generator.generate_recipe("Chocolate Cake", "healthier")
#         # Generate a new healthy recipe
#         new_healthy_recipe = recipe_generator.generate_recipe("Mediterranean cuisine", "new_healthy")
#     except Exception as e:
#         logger.error(f"Error in recipe generation example: {str(e)}")
