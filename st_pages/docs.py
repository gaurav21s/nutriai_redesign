import streamlit as st

def show():
    st.title("Project Documentation - Version 2.0.0")
    
    st.write('''
    Welcome to the documentation for the NutriAI project. This document is designed to guide users through the various features, methods, and technologies used in this project.
    ''')

    # Introduction
    with st.expander("Introduction"):
        st.write('''
        NutriAI is an advanced nutritional analysis and recommendation system built using cutting-edge AI technologies. This project aims to provide personalized meal plans, analyze nutritional content, and offer intelligent recommendations for healthy living.
        ''')

    # How to Use
    with st.expander("How to Use"):
        st.write('''
        Using NutriAI is simple:
        1. **Navigate** through the different sections using the sidebar.
        2. **Input** your dietary preferences and constraints.
        3. **Generate** personalized meal plans or analyze specific foods for nutritional content.
        4. **Review** the results and make adjustments as needed.
        ''')

    # Methods and Technologies
    with st.expander("Methods and Technologies"):
        st.write('''
        The following methods and technologies are used in this project:
        - **Food Analysis** (`utils/food_analysis.py`): Analyzes the nutritional content of various foods.
        - **Meal Planning** (`utils/meal_plan.py`): Generates meal plans based on user preferences and dietary requirements.
        - **MCQ Quiz** (`utils/mcq_quiz.py`): Implements a multiple-choice quiz to assess user knowledge.
        - **NutriQA** (`utils/nutriqa.py`): A question-answering system that provides nutritional advice.
        - **Recommendation System** (`utils/recommendations.py`): Offers personalized recommendations for food and nutrition.
        ''')

    # Framework and Structure
    with st.expander("Framework and Structure"):
        st.write('''
        NutriAI is structured into several key components:
        - **Streamlit Pages**: Located in the `st_pages` directory, each script represents a different page of the app.
        - **Utility Scripts**: Located in the `utils` directory, these scripts provide the core functionalities like food analysis, meal planning, and recommendations.
        - **Configuration**: Managed through the `.env` file for environment variables and `config.toml` for Streamlit settings.
        - **Styling**: Custom styles are applied via the `style.css` file.
        - **Templates**: HTML templates, such as `about_us.html`, are used for rendering specific content.
        ''')

    # FAQ Section
    with st.expander("FAQ"):
        st.write('''
        **Q: How do I update the nutritional database?**
        A: The nutritional database can be updated by modifying the corresponding files in the `utils` directory.

        **Q: Can I customize the meal plans generated?**
        A: Yes, the meal plans can be customized by adjusting the input preferences and constraints.

        **Q: How is user data handled?**
        A: User data is processed locally, and no personal information is stored unless explicitly saved by the user.
        ''')

    # Version Information
    with st.expander("Version Info"):
        st.write('''
        **Current Version**: 2.0.0

        **Previous Versions**:
        - 1.3.0: Added advanced recommendation features.
        - 1.2.0: Improved nutritional analysis algorithms.
        - 1.0.0: Initial release with basic meal planning and analysis.
        ''')

if __name__ == "__main__":
    show()
"""
