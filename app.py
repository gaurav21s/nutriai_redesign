import streamlit as st
from nutriai import NutriAI, NutriAIConfig
from PIL import Image
import re
from logger import logger

class NutriAIApp:
    def __init__(self):
        """Initialize the NutriAI application."""
        logger.info("Initializing NutriAI application")
        self.configure_page()
        self.nutriai = NutriAI()
        self.initialize_session_state()

    def initialize_session_state(self):
        """Initialize session state variables."""
        if 'analysis_result' not in st.session_state:
            st.session_state.analysis_result = None
        if 'clear_inputs' not in st.session_state:
            st.session_state.clear_inputs = False
        if 'file_uploader_key' not in st.session_state:
            st.session_state.file_uploader_key = 0

    @staticmethod
    def configure_page():
        """Configure the Streamlit page settings."""
        logger.info("Configuring Streamlit page")
        st.set_page_config(
            page_title="NutriAI: Your Food Detective",
            page_icon="🍽️",
            layout="wide"
        )

    def analyze_food(self, input_text, uploaded_file):
        """Analyze food based on input."""
        try:
            logger.info("Starting food analysis")
            with st.spinner("Analyzing your food..."):
                response = self.nutriai.analyze_food(input_text, uploaded_file)
            
            logger.info("Analysis complete")
            st.session_state.analysis_result = response
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            st.error(f"An error occurred: {str(e)}")

    def run(self):
        """Run the NutriAI application."""
        logger.info("Starting NutriAI application")
        self.create_sidebar()

        st.title("NutriAI: Your Nutritional Sidekick")
        st.subheader("Uncover the secrets of your food 🔍🥗")

        st.subheader("Choose your input method:")

        col1, col2 = st.columns(2)

        with col1:
            st.text("📝 Text Input")
            input_text = st.text_input("Enter food items", key="input_text", placeholder='E.g., 2 slices of pizza, 1 apple', value="" if st.session_state.clear_inputs else None)

        with col2:
            st.text("📸 Image Input")
            uploaded_file = st.file_uploader("Upload a food picture", type=NutriAIConfig.UPLOAD_TYPES, key=f"uploaded_file_{st.session_state.file_uploader_key}")

        if st.session_state.clear_inputs:
            st.session_state.clear_inputs = False
            st.session_state.file_uploader_key += 1
            st.experimental_rerun()

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)

        if st.button("Analyze My Food", type="primary"):
            if (input_text and uploaded_file) or (not input_text and not uploaded_file):
                logger.warning("User provided invalid input combination")
                st.warning("Please provide either text input OR image input, not both or neither.")
            else:
                self.analyze_food(input_text, uploaded_file)

        if st.session_state.analysis_result:
            st.success("Analysis complete!")
            self.display_results(st.session_state.analysis_result)

            if st.button("Clear Output and Start New Analysis", key="clear_button"):
                logger.info("User cleared inputs.")
                self.clear_inputs()
                st.experimental_rerun()

    def clear_inputs(self):
        """Set flag to clear inputs on next rerun."""
        st.session_state.clear_inputs = True
        st.session_state.analysis_result = None
        st.session_state.file_uploader_key += 1

    def create_sidebar(self):
        """Create an informative sidebar."""
        st.sidebar.title("About NutriAI")
        st.sidebar.info(
            "NutriAI is your personal nutrition detective. "
            "Simply input your food items or upload a picture, "
            "and let our AI analyze the nutritional content for you!"
        )
        st.sidebar.subheader("How it works:")
        st.sidebar.text("1. Enter food items or upload an image")
        st.sidebar.text("2. Click 'Analyze My Food'")
        st.sidebar.text("3. Get detailed nutritional insights")
        
        st.sidebar.subheader("Why?")
        st.sidebar.text("1. To check your macronutrients")

    def display_results(self, response: str):
        """Display the nutrition analysis results."""
        st.subheader("🍽️ Your Nutrition Breakdown:")
        
        sections = re.split(r'(?:Total:|Verdict:|Facts:)', response)
        
        if len(sections) >= 3:
            # Display food items
            food_items_section = sections[0].strip()
            if food_items_section:
                st.text("Food Items:")
                st.info(food_items_section)

            # Display total nutrition
            total_nutrition_section = sections[1].strip()
            if total_nutrition_section:
                st.text("Total Nutrition:")
                st.info(total_nutrition_section)

            # Display verdict
            verdict_section = sections[2].strip()
            if verdict_section:
                st.text("Verdict:")
                if "Not" in verdict_section:
                    st.warning(verdict_section)
                else:
                    st.success(verdict_section)

            # Display facts
            if len(sections) > 3:
                facts_section = sections[3].strip()
                if facts_section:
                    st.text("Interesting Facts:")
                    st.info(facts_section)
        else:
            st.warning("Unable to get the nutrition value of this food item.")

if __name__ == "__main__":
    logger.info("Starting the process")
    app = NutriAIApp()
    app.run()
