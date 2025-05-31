"""
Main application module for NutriAI.

This module contains the main NutriAIApp class which handles the
application's initialization and navigation.

"""

import streamlit as st
from st_pages import home, about_us, meal_plan, recipe_generation, food_analysis, nutri_info, article, mcq_quiz, calc, nutriqa, docs
from utils.logger import logger
from streamlit_option_menu import option_menu


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
        logger.info("Configuring Streamlit page for NutriAI app")
        st.set_page_config(
            page_title="NutriAI: Your Nutrition Companion",
            page_icon="🍽️",
            initial_sidebar_state="expanded",
        )

    def create_navbar(self):
        """
        Create navigation bar in the sidebar.

        Returns:
            str: The selected navigation option.
        """
        with st.sidebar:
            # Responsive logo sizing
            screen_width = st.session_state.get("screen_width", 1200)  # Default to desktop width
            
            if screen_width <= 768:  # Mobile breakpoint
                logo_width = 75
            else:
                logo_width = 125
            
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                st.image("style/nutriai-color.png", width=logo_width, use_container_width=False)
            
            # Add a hidden element to detect screen size changes
            st.markdown(
                """
                <script>
                    var screenWidth = window.innerWidth;
                    document.addEventListener('DOMContentLoaded', function() {
                        Streamlit.setComponentValue("screen_width", screenWidth);
                    });
                    window.addEventListener('resize', function() {
                        screenWidth = window.innerWidth;
                        Streamlit.setComponentValue("screen_width", screenWidth);
                    });
                </script>
                """,
                unsafe_allow_html=True
            )
            selected = option_menu(
                menu_title="Navigation",
                options=[
                    "Home", "Food Insight", "Ingredient Checker", "Meal Planner", "Recipe Finder",
                    "NutriQuiz", "Nutri Calc", "NutriChat", "About Us",
                    "Learn More", "NutriAI Articles"
                ],
                icons=[
                    "house", "eye", 'search', "calendar3", "book",
                    "patch-question", "calculator", "chat-dots", "people",
                    "info-circle", "newspaper"
                ],
                # menu_icon="compass",
                default_index=0,
                styles={
                    "container": {"padding": "5!important", "background-color": "#dbf3e7"},
                    "icon": {"color": "#d62176", "font-size": "25px"}, 
                    "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#E9ECEF"},
                    # "nav-link-selected": {"background-color": "#09ADA4", "color": "#F8F9FA"},
                }
            )

        return selected
        
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
        elif nav_selection == "Food Insight":
            food_analysis.show()
        elif nav_selection == "Ingredient Checker":
            nutri_info.show()
        elif nav_selection == "Meal Planner":
            meal_plan.show()
        elif nav_selection == "Recipe Finder":
            recipe_generation.show()
        elif nav_selection == "NutriQuiz":
            mcq_quiz.show()
        elif nav_selection == "Nutri Calc":
            calc.show()
        elif nav_selection == "NutriChat":
            nutriqa.show()
        elif nav_selection == "About Us":
            about_us.show()
        elif nav_selection == "Learn More":
            docs.show()
        elif nav_selection == "NutriAI Articles":
            article.show()
        

if __name__ == "__main__":
    logger.info("Starting the process")
    app = NutriAIApp()
    app.run()