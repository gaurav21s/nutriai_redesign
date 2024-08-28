import streamlit as st

def show():
    st.title("NutriAI Project Documentation - Version 2.1.0")
    
    st.write('''
    Welcome to the comprehensive documentation for the NutriAI project. This document provides an in-depth guide to the various features, methods, and technologies used in this advanced nutritional analysis and recommendation system.
    ''')

    # Introduction
    with st.expander("Introduction"):
        st.write('''
        NutriAI is a cutting-edge nutritional analysis and recommendation system that leverages various AI technologies to provide personalized meal plans, analyze nutritional content, and offer intelligent recommendations for healthy living. The project combines multiple AI models and APIs to deliver a comprehensive suite of nutrition-related tools.
        ''')

    # Key Features
    with st.expander("Key Features"):
        st.write('''
        1. **Personalized Meal Planning**: Generate customized meal plans based on user preferences and dietary requirements.
        2. **Food Analysis**: Analyze the nutritional content of various foods using image recognition or text input.
        3. **Interactive Nutrition Quiz**: Test your nutrition knowledge with an AI-generated quiz.
        4. **NutriQA**: An AI-powered question-answering system for nutritional advice.
        5. **Recipe Generation**: Create new recipes or healthier alternatives to existing dishes.
        6. **Shopping Link Generation**: Generate affiliate links for ingredients on popular platforms.
        ''')

    # Technologies and Platforms
    with st.expander("Technologies and Platforms"):
        st.write('''
        NutriAI utilizes a variety of cutting-edge technologies and platforms:

        1. **AI and Machine Learning**:
           - OpenAI GPT-3.5 Turbo: Used for general recommendations
           - Google's Gemini Pro and Gemini Pro Vision: For food analysis and image recognition
           - Together AI's Mixtral-8x7B: For meal planning and chatbot functionality
           - Groq API: For recipe generation and MCQ quiz creation

        2. **Web Framework**:
           - Streamlit: For creating the interactive web application

        3. **Python Libraries**:
           - LangChain: For integrating various language models
           - Pillow (PIL): For image processing
           - dotenv: For managing environment variables

        4. **APIs**:
           - Together AI API
           - Google Generative AI API
           - Groq API
           - OpenAI API

        5. **Other Tools**:
           - Amazon Affiliate Program: For generating shopping links
        ''')

    # Project Structure
    with st.expander("Project Structure"):
        st.write('''
        NutriAI is structured into several key components:

        1. **Streamlit Pages** (`st_pages` directory):
           - Each script represents a different page of the app (e.g., `docs.py`, `meal_plan.py`, etc.)

        2. **Utility Scripts** (`utils` directory):
           - `food_analysis.py`: Analyzes food items using Google's Gemini Pro Vision
           - `meal_plan.py`: Generates meal plans using Together AI's Mixtral model
           - `mcq_quiz.py`: Creates nutrition quizzes using Groq API
           - `nutriqa.py`: Implements a nutrition-focused chatbot using Together AI
           - `recommendations.py`: Provides food recommendations using OpenAI's GPT-3.5
           - `recipe_generation.py`: Generates recipes using Groq API
           - `shopping_link_generation.py`: Creates affiliate links for ingredients

        3. **Configuration**:
           - `.env`: Stores environment variables and API keys
           - `config.toml`: Contains Streamlit settings

        4. **Styling**:
           - `style.css`: Applies custom styles to the Streamlit app

        5. **Templates**:
           - HTML templates for specific content rendering
        ''')

    # How to Use
    with st.expander("How to Use"):
        st.write('''
        Using NutriAI is straightforward:
        1. Navigate through different sections using the sidebar.
        2. Input your dietary preferences, goals, and constraints.
        3. Utilize various features like meal planning, food analysis, or recipe generation.
        4. Review the AI-generated results and adjust as needed.
        5. Explore the interactive quiz and chatbot for more nutrition information.
        ''')

    # API Integration
    with st.expander("API Integration"):
        st.write('''
        NutriAI integrates multiple APIs to provide its diverse functionality:
        - Together AI API: Used for meal planning and the NutriQA chatbot
        - Google Generative AI API: Powers the food analysis feature
        - Groq API: Utilized for recipe generation and quiz creation
        - OpenAI API: Handles general recommendations

        API keys are managed securely through environment variables.
        ''')

    # Data Handling and Privacy
    with st.expander("Data Handling and Privacy"):
        st.write('''
        - User data is processed locally and not stored persistently.
        - API requests are made securely, transmitting only necessary information.
        - No personal information is shared with third-party services.
        ''')

    # Future Enhancements
    with st.expander("Future Enhancements"):
        st.write('''
        Planned improvements for NutriAI include:
        - Integration with fitness tracking devices
        - Expanded database of regional cuisines
        - Advanced dietary pattern analysis
        - Collaborative meal planning for households
        ''')

    # Version Information
    with st.expander("Version Info"):
        st.write('''
        **Current Version**: 2.1.0

        **Change Log**:
        - 2.1.0: Added recipe generation and shopping link features
        - 2.0.0: Integrated multiple AI models for enhanced functionality
        - 1.3.0: Added advanced recommendation features
        - 1.2.0: Improved nutritional analysis algorithms
        - 1.0.0: Initial release with basic meal planning and analysis
        ''')

if __name__ == "__main__":
    show()
