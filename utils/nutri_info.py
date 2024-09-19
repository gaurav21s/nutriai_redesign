import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from utils.logger import logger
import PIL
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import langchain_core.exceptions

class NutriInfoConfig:
    """Configuration class for NutriInfo application."""

    UPLOAD_TYPES = ["jpg", "jpeg", "png"]
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    MODEL_NAME = "gemini-1.5-pro"

class IngredientAnalysis(BaseModel):
    """Model for ingredient analysis results."""
    healthy_ingredients: List[str] = Field(description="List of healthy ingredients")
    unhealthy_ingredients: List[str] = Field(description="List of unhealthy ingredients")
    health_issues: Dict[str, List[str]] = Field(description="Dictionary of unhealthy ingredients and their associated health issues")

class GoogleAIHandler:
    """Handler for Google AI API interactions using Langchain."""

    def __init__(self):
        """Initialize the Google AI handler."""
        logger.info("Initializing Google AI handler with Langchain")
        if not NutriInfoConfig.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        self.llm = ChatGoogleGenerativeAI(
            model=NutriInfoConfig.MODEL_NAME,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            google_api_key=NutriInfoConfig.GOOGLE_API_KEY,
        )

    def get_model_response(self, system_message: str, human_message: str, output_parser: PydanticOutputParser) -> IngredientAnalysis:
        """
        Get response from Google's Generative AI model.

        Args:
            system_message (str): The system message for context.
            human_message (str): The human message or query.
            output_parser (PydanticOutputParser): The parser for structured output.

        Returns:
            IngredientAnalysis: The parsed analysis result.
        """
        logger.info("Sending request to Google AI API")
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=f"{human_message}\n\n{output_parser.get_format_instructions()}")
        ]
        
        max_retries = 1
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(messages)
                return output_parser.parse(response.content)
            except langchain_core.exceptions.OutputParserException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"All attempts failed. Last error: {str(e)}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise

        # This line should never be reached due to the raise in the loop, but including for completeness
        raise Exception("Failed to get valid response after multiple attempts")

    def analyze_image(self, image: PIL.Image) -> str:
        """
        Analyze image using Google's Generative AI model.

        Args:
            image_data (bytes): The image data.

        Returns:
            str: The generated response text describing the image contents.
        """
        logger.info("Sending image to Google AI API for analysis")
        messages = [
            SystemMessage(content="You are an expert in identifying ingredients from images."),
            HumanMessage(content=[image])
        ]
        response = self.llm.invoke(messages)
        return response.content

class NutriInfoHandler:
    """Handler for nutrition information processing."""

    @staticmethod
    def process_ingredients(ingredients: List[str], google_ai_handler: GoogleAIHandler) -> IngredientAnalysis:
        """
        Process the list of ingredients for nutritional analysis.

        Args:
            ingredients (List[str]): The list of ingredients.
            google_ai_handler (GoogleAIHandler): The Google AI handler for generating responses.

        Returns:
            IngredientAnalysis: The parsed analysis result.
        """
        logger.info("Processing ingredients for nutritional analysis")
        system_message = """
        You are a nutritionist providing health insights about ingredients. 
        Your response should be in JSON format with the following structure:
        {
            "healthy_ingredients": ["ingredient1", "ingredient2", ...],
            "unhealthy_ingredients": ["ingredient1", "ingredient2", ...],
            "health_issues": ["issue1","issue2"]
        }
        """
        human_message = f"""
        Analyze the following ingredients and categorize them as healthy(safe) or unhealthy(unsafe). 
        For unhealthy ingredients, list potential health issues they may cause:
        {', '.join(ingredients)}

        Give empty list if there are no healthy or safe and unhealthy or unsafe ingredients.
        Provide your response in the JSON format specified in the system message.
        """
        
        output_parser = PydanticOutputParser(pydantic_object=IngredientAnalysis)
        
        try:
            answer = google_ai_handler.get_model_response(system_message, human_message, output_parser)
            # print(answer)
            return answer
        except langchain_core.exceptions.OutputParserException as e:
            logger.error(f"Failed to parse API response: {str(e)}")
            # Return a default IngredientAnalysis object or raise a custom exception
            return IngredientAnalysis(
                healthy_ingredients=[],
                unhealthy_ingredients=[],
                health_issues={}
            )

class NutriInfo:
    """Main class for NutriInfo functionality."""

    def __init__(self):
        """Initialize the NutriInfo application."""
        logger.info("Initializing NutriInfo application")
        self.google_ai_handler = GoogleAIHandler()

    def analyze_nutrition(self, ingredients_text: str = "", uploaded_file=None) -> Optional[IngredientAnalysis]:
        """
        Analyze nutrition based on text input or uploaded image.

        Args:
            ingredients_text (str): The input text containing ingredients.
            uploaded_file: The uploaded file object.

        Returns:
            Optional[IngredientAnalysis]: The parsed analysis result, or None if an error occurred.
        """
        try:
            ingredients_list = []
            if uploaded_file:
                logger.info(f"Analyzing uploaded image")
                image_analysis = self.google_ai_handler.analyze_image(uploaded_file)
                ingredients_list = [ingredient.strip() for ingredient in image_analysis.split(',')]
            elif ingredients_text:
                ingredients_list = [ingredient.strip() for ingredient in ingredients_text.split(',')]
                logger.info(f"Analyzing text input: {ingredients_list}")

            if not ingredients_list:
                logger.warning("No ingredients provided for analysis")
                return None

            return NutriInfoHandler.process_ingredients(ingredients_list, self.google_ai_handler)
        except Exception as e:
            logger.error(f"Error in analyze_nutrition: {str(e)}")
            return None

# Example usage

# load_dotenv()  # Load environment variables
# nutri_info = NutriInfo()

# # Analyze text input
# text_analysis = nutri_info.analyze_nutrition(ingredients_text="spinach, chicken, olive oil, garlic, sugar, trans fat")
# if text_analysis:
#     print("Text Analysis Result:")
#     print(f"Healthy Ingredients: {text_analysis.healthy_ingredients}")
#     print(f"Unhealthy Ingredients: {text_analysis.unhealthy_ingredients}")
#     print("Health Issues:")
#     for issue in text_analysis.health_issues:
#         print(f"issue}")
# else:
#     print("Failed to analyze text input")

# # Analyze image (assuming you have an image file)
# with open("path_to_your_image.jpg", "rb") as image_file:
#     image_analysis = nutri_info.analyze_nutrition(uploaded_file=image_file)
#     if image_analysis:
#         print("\nImage Analysis Result:")
#         print(f"Healthy Ingredients: {image_analysis.healthy_ingredients}")
#         print(f"Unhealthy Ingredients: {image_analysis.unhealthy_ingredients}")
#         print("Health Issues:")
#         for ingredient, issues in image_analysis.health_issues.items():
#             print(f"  {ingredient}: {', '.join(issues)}")
#     else:
#         print("Failed to analyze image input")