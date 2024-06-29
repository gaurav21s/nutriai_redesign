"""
Main application module for NutriAI.

This module contains the main NutriAIApp class which handles the
application's initialization and navigation.
"""

import streamlit as st
from st_pages import home, about_us, meal_plan, recommendations, food_analysis
from utils.logger import logger

class NutriAIApp:
    """
    Main application class for NutriAI.

    This class handles the initialization of the Streamlit app,
    manages the navigation, and controls the flow between different pages.
    """

    def __init__(self):
        """
        Initialize the NutriAI application.

        This method sets up the page configuration and initializes the session state.
        """
        logger.info("Initializing NutriAI application")
        self.configure_page()
        self.initialize_session_state()

    def initialize_session_state(self):
        """
        Initialize session state variables.

        This method sets up the initial state for various session variables
        used throughout the application.
        """
        if 'analysis_result' not in st.session_state:
            st.session_state.analysis_result = None
        if 'clear_inputs' not in st.session_state:
            st.session_state.clear_inputs = False
        if 'file_uploader_key' not in st.session_state:
            st.session_state.file_uploader_key = 0

    @staticmethod
    def configure_page():
        """
        Configure the Streamlit page settings.

        This method sets up the page title, icon, and layout for the Streamlit app.
        """
        logger.info("Configuring Streamlit page")
        st.set_page_config(
            page_title="NutriAI: Your Food Detective",
            page_icon="🍽️",
            layout="wide"
        )

    def create_navbar(self):
        """
        Create navigation bar in the sidebar.

        Returns:
            str: The selected navigation option.
        """
        st.sidebar.title("NutriAI Navigation")
        return st.sidebar.radio("Go to", ["Home", "Food Analysis", "Meal Plan", "Recommendations", "About Us"])

    def run(self):
        """
        Run the NutriAI application.

        This method creates the navigation bar and displays the appropriate page
        based on the user's selection.
        """
        logger.info("Starting NutriAI application")
        
        nav_selection = self.create_navbar()

        if nav_selection == "Home":
            home.show()
        elif nav_selection == "Food Analysis":
            food_analysis.show()
        elif nav_selection == "Meal Plan":
            meal_plan.show()
        elif nav_selection == "Recommendations":
            recommendations.show()
        elif nav_selection == "About Us":
            about_us.show()

if __name__ == "__main__":
    logger.info("Starting the process")
    app = NutriAIApp()
    app.run()