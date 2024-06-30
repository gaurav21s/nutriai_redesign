"""
Meal Plan requirements: 
1. Weight Gain or Fat Loss or Lean Diet
2. Veg or Nonveg or Vegan
3. Any issue or allergy None or Lactose intolerant or Other
4. Gym or workout yes/no
"""
import os
from typing import Dict, Optional
from dotenv import load_dotenv
from langchain_together import ChatTogether
from utils.logger import logger

# Load environment variables
load_dotenv()

class MealPlanConfig:
    """Configuration class for MealPlan application."""

    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
    MODEL_NAME = "mistralai/Mixtral-8x22B-Instruct-v0.1"

class TogetherAIHandler:
    """Handler for Together AI API interactions."""

    def __init__(self):
        """Initialize the Together AI handler."""
        logger.info("Initializing Together AI handler")
        if not MealPlanConfig.TOGETHER_API_KEY:
            raise ValueError("TOGETHER_API_KEY environment variable is not set")
        self.chat_model = ChatTogether(
            together_api_key=MealPlanConfig.TOGETHER_API_KEY,
            model=MealPlanConfig.MODEL_NAME,
            temperature=0.0001
        )

    def get_model_response(self, input_text: str) -> str:
        """
        Get response from Together AI's Mixtral model.

        Args:
            input_text (str): The input text for the model.

        Returns:
            str: The generated response text.
        """
        logger.info("Sending request to Together AI API")
        response = self.chat_model.invoke(input_text)
        return response.content

class MealPlan:
    """Main class for MealPlan functionality."""

    def __init__(self):
        """Initialize the MealPlan page."""
        logger.info("Initializing MealPlan application")
        self.together_ai_handler = TogetherAIHandler()

    @staticmethod
    def get_meal_plan_prompt(gender: str, goal: str, diet_choice: str, issue: str, gym: str, height: str, weight: str,food_type: str) -> str:
        """
        Get the prompt for meal plan generation.

        Args:
            goal (str): The user's goal (e.g., "weight gain", "fat loss", "lean diet").
            diet_choice (str): The user's diet preference (e.g., "vegetarian", "non-vegetarian", "vegan").
            issue (str): Any dietary issues or allergies (e.g., "none", "lactose intolerant", "other").
            gym (str): Whether the user works out or not (e.g., "do gym/workout", "don't workout").
            food_type (str): The preferred cuisine type (e.g., "indian", "mediterranean", "american").

        Returns:
            str: The formatted prompt for meal plan generation.
        """
        workout_options = """
        Pre-Workout:
        - [Pre-workout option 1: with quantity or portion size: (calories in meal)]
        - [Pre-workout option 2: with quantity or portion size: (calories in meal)]

        Post-Workout:
        - [Post-workout option 1: with quantity or portion size: (calories in meal)]
        - [Post-workout option 2: with quantity or portion size: (calories in meal)]
        """ if 'do gym' in gym.lower() else """
        Pre-Workout:
        - Give "Not needed"

        Post-Workout:
        - Give "Not needed"
        """

        return f"""
        You are a friendly and expert nutritionist. Create a simple home made meal-plan based on the following preferences:

        User's choice: I am a {gender}. I want to {goal} and I am {diet_choice} in diet. I have a {issue} condition. I {gym} and my height is {height} and weight is {weight}. I prefer {food_type} of dishes.

        Strictly follow this format for your response:

        Breakfast:
        - [Breakfast option 1: with quantity or portion size: (calories in meal)]
        - [Breakfast option 2: with quantity or portion size: (calories in meal)]

        Lunch:
        - [Lunch option 1: with quantity or portion size: (calories in meal)]
        - [Lunch option 2: with quantity or portion size: (calories in meal)]

        {workout_options}

        Dinner:
        - [Dinner option 1: with quantity or portion size: (calories in meal)]
        - [Dinner option 2: with quantity or portion size: (calories in meal)]

        Important Rules to be followed:
        1. Provide only simple home-made and healthy meal names, not recipes.
        2. Adjust portion sizes and nutrient balance to support the user's goal ({goal}).
        3. Adjust the calories required based on height, weight, gender, and goal.
        4. Consider the user's food preferences ({food_type} cuisine) in all meal suggestions.
        5. Account for any dietary issues or allergies ({issue}) when suggesting meals.
        6. Do not add any extra explanations or information outside the specified format.
        7. Ensure each meal option is unique and varied.
        """

    def create_meal_plan(self, gender: str, goal: str, diet_choice: str, issue: str, gym: str, height: str, weight: str, food_type: str) -> str:
        """
        Create a meal plan based on user preferences.

        Args:
            goal (str): The user's goal (e.g., "weight gain", "fat loss", "lean diet").
            diet_choice (str): The user's diet preference (e.g., "vegetarian", "non-vegetarian", "vegan").
            issue (str): Any dietary issues or allergies (e.g., "none", "lactose intolerant", "other").
            gym (str): Whether the user works out or not (e.g., "do gym/workout", "don't workout").
            food_type (str): The preferred cuisine type (e.g., "indian", "mediterranean", "american").

        Returns:
            str: The generated meal plan.
        """
        logger.info(f"Creating meal plan for: gender={gender} ,goal={goal}, diet={diet_choice}, issue={issue}, gym={gym}, height={height}, weight={weight}, food_type={food_type}")
        prompt = self.get_meal_plan_prompt(gender, goal, diet_choice, issue, gym, height, weight, food_type)
        meal_plan = self.together_ai_handler.get_model_response(prompt)
        
        return meal_plan
    
# example usage

# meal_planner = MealPlan()

# # Set user preferences
# gender= "male"
# goal = "gain muscle"
# diet_choice = "vegetarian"
# issue = "no allegry"
# gym = "do gym/workout"
# height = '1.8m'
# weight = '69kg'
# food_type = "indian"

# # Generate meal plan
# meal_plan = meal_planner.create_meal_plan(gender, goal, diet_choice, issue, gym, height, weight, food_type)
# print("Generated Meal Plan:")
# print(meal_plan)

