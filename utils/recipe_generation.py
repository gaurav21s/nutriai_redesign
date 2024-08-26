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

# Load environment variables
load_dotenv()

class GroqHandler:
    """Handles interactions with the Groq API using LangChain."""

    def __init__(self):
        """Initialize the GroqHandler."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model="mixtral-8x7b-32768",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

    def get_model_response(self, input_text: str) -> str:
        """Get a response from the Groq model for the given input text."""
        try:
            messages = [
                ("system", "You are a helpful assistant that generates recipes."),
                ("human", input_text),
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"Error in Groq API request: {e}")
            raise

class RecipeGenerator:
    """Generates recipes based on user input."""

    def __init__(self):
        """Initialize the RecipeGenerator."""
        self.groq_handler = GroqHandler()

    def generate_recipe(self, dish_name: str, recipe_type: Literal["normal", "healthier", "new_healthy"]) -> str:
        """
        Generate a recipe based on the given dish name and recipe type.

        Args:
            dish_name (str): The name of the dish or a general description for new recipes.
            recipe_type (Literal["normal", "healthier", "new_healthy"]): The type of recipe to generate.

        Returns:
            str: The generated recipe as a formatted string.
        """
        prompt = self._get_recipe_prompt(dish_name, recipe_type)
        recipe = self.groq_handler.get_model_response(prompt)
        return recipe

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
if __name__ == "__main__":
    recipe_generator = RecipeGenerator()
    
    # Generate a normal recipe
    normal_recipe = recipe_generator.generate_recipe("Spaghetti Carbonara", "normal")
    # Generate a healthier alternative recipe
    healthier_recipe = recipe_generator.generate_recipe("Chocolate Cake", "healthier")
    # Generate a new healthy recipe
    new_healthy_recipe = recipe_generator.generate_recipe("Mediterranean cuisine", "new_healthy")
