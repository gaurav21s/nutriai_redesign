import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
from utils.logger import logger

# Load environment variables
load_dotenv()

class FoodAnalysisConfig:
    """Configuration class for FoodAnalysis application."""

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    UPLOAD_TYPES = ["jpg", "jpeg", "png"]
    # Updated to match user preference
    MODEL_NAME = "gemini-2.0-flash"

class GoogleAIHandler:
    """Handler for Google's Generative AI interactions."""

    @staticmethod
    def configure_api():
        """Configure the Google Generative AI API."""
        logger.info("Configuring Google Generative AI API")
        if not FoodAnalysisConfig.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY environment variable is not set")
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        try:
            genai.configure(api_key=FoodAnalysisConfig.GOOGLE_API_KEY)
            logger.info("Successfully configured Google Generative AI API")
        except Exception as e:
            logger.error(f"Failed to configure Google Generative AI API: {str(e)}")
            raise

    @staticmethod
    def get_gemini_response(input_text: str, image: Optional[List[Dict]] = None, prompt: str = "") -> str:
        """
        Get response from Google Gemini Flash API.

        Args:
            input_text (str): The input text for the model.
            image (Optional[List[Dict]]): The image data, if any.
            prompt (str): Additional prompt for the model.

        Returns:
            str: The generated response text.
        """
        try:
            logger.info("Sending request to Google Gemini API")
            # Updated to use more cost-effective model
            model = genai.GenerativeModel(FoodAnalysisConfig.MODEL_NAME)
            content = [input_text, image[0], prompt] if image else input_text
            response = model.generate_content(
                content,
                generation_config=genai.types.GenerationConfig(temperature=0.001)
            )
            logger.info("Successfully received response from Google Gemini API")
            return response.text
        except Exception as e:
            logger.error(f"Error in Google Gemini API request: {str(e)}")
            return "I apologize, but I'm currently unable to analyze the food. Please try again later or contact support if the issue persists."

class ImageHandler:
    """Handler for image-related operations."""

    @staticmethod
    def setup_input_image(uploaded_file) -> List[Dict]:
        """
        Set up the input image for processing.

        Args:
            uploaded_file: The uploaded file object from Streamlit.

        Returns:
            List[Dict]: A list containing the image data and MIME type.

        Raises:
            FileNotFoundError: If no file is uploaded.
        """
        try:
            logger.info(f"Setting up input image: {uploaded_file.name}")
            if uploaded_file is None:
                logger.error("No file uploaded")
                raise FileNotFoundError("No file uploaded")

            return [{
                "mime_type": uploaded_file.type,
                "data": uploaded_file.getvalue()
            }]
        except Exception as e:
            logger.error(f"Error setting up input image: {str(e)}")
            raise

class FoodAnalysis:
    """Main class for FoodAnalysis functionality."""

    def __init__(self):
        """Initialize the FoodAnalysis application."""
        logger.info("Initializing FoodAnalysis application")
        try:
            self.google_ai = GoogleAIHandler()
            self.google_ai.configure_api()
        except Exception as e:
            logger.error(f"Failed to initialize FoodAnalysis: {str(e)}")
            raise

    @staticmethod
    def get_image_prompt() -> str:
        """Get the prompt for image analysis."""
        return """
        You are a fun and friendly nutritionist. Analyze the food items in the image and calculate:
        - Total calories
        - Nutrition values: carbs, fiber, protein, fats
        - Details of each food item by proportion or quantity with calorie intake

        Follow this format strictly and don't add extra information:

        1. Item 1 (quantity) - calories range, carbs range, fiber range, protein range, fats range, other details (if available)
        2. Item 2 (quantity) - calories range, carbs range, fiber range, protein range, fats range, other details (if available)
        ...
        
        (example: 1 aaloo paratha, 100g yogurt
        
        1. 1 aaloo paratha - 200-250 calories, 25-35g carbs, 1-2g fiber, 6-8g protein, 8-10g fats
        2. 100g yogurt - 50-60 calories, 5-6g carbs, 0g fiber, 5-8g protein, 1-3g fats
        example ended.)

        Total: calories, carbs, fiber, protein, fats
        Verdict: Healthy or Not Healthy
        Facts: Share 2-3 interesting, sarcastic and fun nutrition facts about the dish
        """

    @staticmethod
    def get_text_prompt(input_text: str) -> str:
        """
        Get the prompt for text input analysis.

        Args:
            input_text (str): The input text containing food items.

        Returns:
            str: The formatted prompt for text analysis.
        """
        return f"""
        You are a fun and friendly nutritionist. Calculate nutrition values for these food items or dishes: [{input_text}]
        Follow this format strictly and don't add extra information:

        1. Item 1 (quantity) - calories range, carbs range, fiber range, protein range, fats range, other details (if available)
        2. Item 2 (quantity) - calories range, carbs range, fiber range, protein range, fats range, other details (if available)
        ...
        
        (example: 1 aaloo paratha, 100g yogurt
        
        1. 1 aaloo paratha - 200-250 calories, 25-35g carbs, 1-2g fiber, 6-8g protein, 8-10g fats
        2. 100g yogurt - 50-60 calories, 5-6g carbs, 0g fiber, 5-8g protein, 1-3g fats
        example ended.)

        Total: calories, carbs, fiber, protein, fats
        Verdict: Healthy or Not Healthy
        Facts: Share 2-3 interesting, sarcastic and fun nutrition facts about the dish
        """

    def analyze_food(self, input_text: str = "", uploaded_file=None) -> str:
        """
        Analyze food based on text input or uploaded image.

        Args:
            input_text (str): The input text containing food items.
            uploaded_file: The uploaded file object from Streamlit.

        Returns:
            str: The analysis result.
        """
        try:
            if uploaded_file:
                logger.info(f"Analyzing uploaded image: {uploaded_file.name}")
                image_data = ImageHandler.setup_input_image(uploaded_file)
                response = self.google_ai.get_gemini_response(
                    self.get_image_prompt(),
                    image_data,
                    ""
                )
            else:
                logger.info(f"Analyzing text input: {input_text}")
                response = self.google_ai.get_gemini_response(
                    self.get_text_prompt(input_text)
                )
            
            logger.info("Successfully analyzed food")
            return response
        except Exception as e:
            logger.error(f"Error in food analysis: {str(e)}")
            return "I apologize, but I'm currently unable to analyze the food. Please try again later or contact support if the issue persists."