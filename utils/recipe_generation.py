"""
Recipe Generation Module

This module provides functionality for generating recipes using the Mistral AI API.
It can generate normal recipes, healthier alternatives, and new healthy recipes.

Classes:
    MistralHandler: Handles interactions with the Mistral AI API.
    RecipeGenerator: Generates recipes based on user input.

Todo:
    * Implement error handling for API requests
    * Add caching mechanism for frequently requested recipes
    * Implement rate limiting to avoid API overuse
"""

import os
from typing import Literal
from dotenv import load_dotenv
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# Load environment variables
load_dotenv()

class MistralHandler:
    """Handles interactions with the Mistral AI API."""

    def __init__(self):
        """Initialize the MistralHandler."""
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is not set")
        self.client = MistralClient(api_key=api_key)

    def get_model_response(self, input_text: str) -> str:
        """Get a response from the Mistral AI model for the given input text."""
        try:
            messages = [
                ChatMessage(role="user", content=input_text)
            ]
            response = self.client.chat(
                model="open-mixtral-8x7b",
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in Mistral AI API request: {e}")
            raise

class RecipeGenerator:
    """Generates recipes based on user input."""

    def __init__(self):
        """Initialize the RecipeGenerator."""
        self.mistral_handler = MistralHandler()

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
        recipe = self.mistral_handler.get_model_response(prompt)
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

        {'Explaination (briefly why this version is healthier):' if recipe_type == "healthier" else ''}
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
