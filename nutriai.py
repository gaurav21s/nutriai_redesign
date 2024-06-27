"""
NutriAI: A vibrant Streamlit application for calculating food nutrition values.

This application uses Google's Generative AI to analyze food items from images
or text input and provide nutritional information in an engaging manner.

Usage:
    streamlit run nutriai.py

Environment variables required:
    GOOGLE_API_KEY: API key for Google's Generative AI

Dependencies:
    - streamlit
    - python-dotenv
    - google-generativeai
    - Pillow
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
from PIL import Image
import re

# Load environment variables
load_dotenv()

class NutriAIConfig:
    """Configuration class for NutriAI application."""

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    PAGE_TITLE = "NutriAI: Your Fun Food Detective! 🕵️‍♂️🍔"
    PAGE_ICON = "🍱"
    HEADER = "Welcome to NutriAI: Your Nutritional Sidekick!"
    SUBHEADER = "Uncover the secrets of your food! 🔍🥗"
    UPLOAD_TYPES = ["jpg", "jpeg", "png"]

class GoogleAIHandler:
    """Handler for Google's Generative AI interactions."""

    @staticmethod
    def configure_api():
        """Configure the Google Generative AI API."""
        if not NutriAIConfig.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        genai.configure(api_key=NutriAIConfig.GOOGLE_API_KEY)

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
        if uploaded_file is None:
            raise FileNotFoundError("No file uploaded")

        return [{
            "mime_type": uploaded_file.type,
            "data": uploaded_file.getvalue()
        }]

class NutriAIApp:
    """Main application class for NutriAI."""

    def __init__(self):
        """Initialize the NutriAI application."""
        self.configure_page()
        self.google_ai = GoogleAIHandler()
        self.google_ai.configure_api()

    @staticmethod
    def configure_page():
        """Configure the Streamlit page settings."""
        st.set_page_config(
            page_title=NutriAIConfig.PAGE_TITLE,
            page_icon=NutriAIConfig.PAGE_ICON,
            layout="wide"
        )

    def run(self):
        """Run the NutriAI application."""
        self.set_background()
        self.set_text_styles()
        self.create_sidebar()
        st.title(NutriAIConfig.HEADER)
        st.subheader(NutriAIConfig.SUBHEADER)

        st.markdown("""
        <style>
        .big-font {
            font-size:20px !important;
            font-weight: bold;
            color: #1E90FF;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<p class="big-font">Choose your adventure: Text or Image? 🤔</p>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.info("📝 Text Input: Type your food items")
            input_text = st.text_input("", key="input", placeholder='E.g., 2 slices of pizza, 1 apple')

        with col2:
            st.info("📸 Image Input: Upload a food picture")
            uploaded_file = st.file_uploader("", type=NutriAIConfig.UPLOAD_TYPES)

        if (input_text and uploaded_file) or (not input_text and not uploaded_file):
            st.warning("Please provide either text input OR image input, not both or neither! 🙃")
        elif st.button("Analyze My Food! 🚀", type="primary"):
            try:
                with st.spinner("🧙‍♂️ NutriAI is working its magic..."):
                    if uploaded_file:
                        image = Image.open(uploaded_file)
                        st.image(image, caption="Your Yummy Upload 😋", width=300)
                        image_data = ImageHandler.setup_input_image(uploaded_file)
                        response = self.google_ai.get_gemini_response(
                            self.get_image_prompt(),
                            image_data,
                            ""
                        )
                    else:
                        response = self.google_ai.get_gemini_response(
                            self.get_text_prompt(input_text)
                        )

                st.success("Analysis complete! 🎉")
                self.display_results(response)
            except Exception as e:
                st.error(f"Oops! Something went wrong: {str(e)} 😅")

    @staticmethod
    def create_sidebar():
        """Create a fun and sarcastic sidebar explaining the app."""
        st.sidebar.title("🍔 Welcome to NutriAI 🥗")
        st.sidebar.markdown("""
        Are you tired of enjoying your meals in blissful ignorance? 
        Do you wake up in cold sweats, wondering about the fiber content of that 
        midnight snack? Fear not, fellow food detective! NutriAI is here to 
        crush your culinary dreams and serve you a steaming hot plate of reality!

        ### 🕵️‍♂️ How it works:
        1. **Input your guilty pleasures**: 
           Type in your food items or upload a photo of your "balanced meal".

        2. **Watch the magic unfold**: 
           Our AI nutritionist (who never sleeps and judges you 24/7) analyzes your input.

        3. **Face the music**: 
           Get a detailed breakdown of calories, nutrients, and a verdict on your life choices.


        ### 🚀 The future of food:
        Soon, you'll be able to hook this up to your fridge and get passive-aggressive notifications about your eating habits. 
        Imagine the joy of your fridge telling you "Are you sure about that midnight snack, Karen?"

        Remember, ignorance is bliss, but knowledge is power... 
        to make yourself feel guilty about that donut. Enjoy! 🍩😈
        """)
    
    @staticmethod
    def set_background():
        """Set a subtle, food-themed background for the app."""
        background_style = """
        <style>
        .stApp {
            background-image: url("https://www.transparenttextures.com/patterns/food.png");
            background-color: #f0f8ff;
        }
        .stApp > header {
            background-color: transparent;
        }
        .stApp .block-container {
            background-color: rgba(255, 255, 255, 0.9);
            padding: 2rem;
            border-radius: 10px;
        }
        </style>
        """
        st.markdown(background_style, unsafe_allow_html=True)

    @staticmethod
    def set_text_styles():
        """Apply custom CSS for better text styling and visibility."""
        text_styles = """
        <style>
        h1, h2, h3 {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 5px;
        }
        h1 {
            color: #1E90FF;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        h2 {
            color: #2E8B57;
        }
        h3 {
            color: #4682B4;
        }
        .stSubheader {
            color: #2F4F4F;
            font-weight: bold;
        }
        .big-font {
            font-size: 18px !important;
            color: #2F4F4F;
            font-weight: bold;
            background-color: rgba(255, 255, 255, 0.2);
            padding: 5px;
            border-radius: 3px;
        }
        p {
            color: #333333;
        }
        /* Sidebar styles */
        .sidebar .sidebar-content {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 10px;
            border-radius: 5px;
        }
        .sidebar h1, .sidebar h2, .sidebar h3 {
            color: #1E90FF;
            background-color: #ffffff;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .sidebar p, .sidebar ul, .sidebar ol {
            color: #333333;
            background-color: #ffffff;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .sidebar ul, .sidebar ol {
            padding-left: 30px;
        }
        .sidebar li {
            margin-bottom: 10px;
        }
        .sidebar strong {
            color: #1E90FF;
        }
        /* Output styles */
        .food-items {
            background-color: #F0FFF0;  /* Light mint green background */
            padding: 10px;
            border-radius: 5px;
            color: #006400;  /* Dark green text */
            margin-bottom: 10px;
        }
        .food-item {
            margin-bottom: 5px;
            font-size: 16px;
        }
        .nutrition-info {
            background-color: #f0f8ff;
            padding: 10px;
            border-radius: 5px;
            color: #333333;
            margin-bottom: 10px;
        }
        .verdict {
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .verdict-healthy {
            background-color: #90EE90;
            color: #006400;
        }
        .verdict-unhealthy {
            background-color: #FFB6C1;
            color: #8B0000;
        }
        .facts {
            background-color: #E6E6FA;
            padding: 10px;
            border-radius: 5px;
            color: #333333;
        }
        </style>
        """
        st.markdown(text_styles, unsafe_allow_html=True)

    @staticmethod
    def display_results(response: str):
        """
        Display the nutrition analysis results in an engaging format.

        Args:
            response (str): The response containing all sections in a single string.
        """
        st.markdown("## 🍽️ Your Nutrition Breakdown:")
        sections = re.split(r'(?:Total:|Verdict:|Facts:)', response)
        
        if len(sections) >= 3:
            # Display food items
            food_items_section = sections[0].strip()
            if food_items_section:
                st.markdown("### 🍳 Food Items:")
                food_items = re.findall(r'\d+\.\s+(.+)', food_items_section)
                if food_items:
                    food_items_html = "<ul>" + "".join([f'<li class="food-item">{item}</li>' for item in food_items]) + "</ul>"
                    st.markdown(f'<div class="food-items">{food_items_html}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="food-items">No food items detected.</div>', unsafe_allow_html=True)


            # Display total nutrition
            total_nutrition_section = sections[1].strip()
            if total_nutrition_section:
                st.markdown("### 📊 Total Nutrition:")
                st.markdown(f'<div class="nutrition-info">{total_nutrition_section}</div>', unsafe_allow_html=True)

            # Display verdict
            verdict_section = sections[2].strip()
            if verdict_section:
                verdict = verdict_section
                if verdict:
                    verdict_text = verdict
                    verdict_class = "verdict-healthy" if "Not" not in verdict_text else "verdict-unhealthy"
                    st.markdown(f'<div class="verdict {verdict_class}">Verdict: {verdict_text}</div>', unsafe_allow_html=True)

            # Display facts
            if len(sections) > 3:
                facts_section = sections[3].strip()
                if facts_section:
                    st.markdown("### 🧠 Fun Facts:")
                    facts = re.findall(r'-\s+(.+)', facts_section)
                    facts_html = "<ul>" + "".join([f"<li>{fact}</li>" for fact in facts]) + "</ul>"
                    st.markdown(f'<div class="facts">{facts_html}</div>', unsafe_allow_html=True)
        else:
            st.warning("Unable to get the nutrition value of this food item.")

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

if __name__ == "__main__":
    app = NutriAIApp()
    app.run()
