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

class GoogleAIHandler:
    """Handler for Google's Generative AI interactions."""

    @staticmethod
    def configure_api():
        """Configure the Google Generative AI API."""
        logger.info("Configuring Google Generative AI API")
        if not FoodAnalysisConfig.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        genai.configure(api_key=FoodAnalysisConfig.GOOGLE_API_KEY)

    @staticmethod
    def get_gemini_response(input_text: str, image: Optional[List[Dict]] = None, prompt: str = "") -> str:
        """
        Get response from Google Gemini Pro Vision API.

        Args:
            input_text (str): The input text for the model.
            image (Optional[List[Dict]]): The image data, if any.
            prompt (str): Additional prompt for the model.

        Returns:
            str: The generated response text.
        """
        logger.info("Sending request to Google Gemini API")
        model = genai.GenerativeModel('gemini-pro-vision' if image else 'gemini-pro')
        content = [input_text, image[0], prompt] if image else input_text
        response = model.generate_content(
            content,
            generation_config=genai.types.GenerationConfig(temperature=0.001)
        )
        return response.text

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
        logger.info(f"Setting up input image: {uploaded_file.name}")
        if uploaded_file is None:
            raise FileNotFoundError("No file uploaded")

        return [{
            "mime_type": uploaded_file.type,
            "data": uploaded_file.getvalue()
        }]

class FoodAnalysis:
    """Main class for FoodAnalysis functionality."""

    def __init__(self):
        """Initialize the FoodAnalysis application."""
        logger.info("Initializing FoodAnalysis application")
        self.google_ai = GoogleAIHandler()
        self.google_ai.configure_api()

    @staticmethod
    def get_image_prompt() -> str:
        """Get the prompt for image analysis."""
        return """
        You are a fun and friendly nutritionist. Analyze the food items in the image and calculate:
        - Total calories
        - Nutrition values: carbs, fiber, protein, fats
        - Details of each food item by proportion or quantity with calorie intake

        Format your response as follows:

        1. Item 1 (quantity) - calories, carbs, fiber, protein, fats, other details (if available)
        2. Item 2 (quantity) - calories, carbs, fiber, protein, fats, other details (if available)
        ...

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

        1. Item 1 (quantity) - calories, carbs, fiber, protein, fats, other details (if available)
        2. Item 2 (quantity) - calories, carbs, fiber, protein, fats, other details (if available)
        ...

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
        
        return response