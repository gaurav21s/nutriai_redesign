import streamlit as st

def show():
   st.markdown("""
   <h1 style='text-align: center; color: #15627D;'>NutriAI Project Documentation</h1>
   <h3 style='text-align: center; color: #333;'>Version 2.3.0</h3>
   """, unsafe_allow_html=True)
   
   st.write('''
   Welcome to the comprehensive documentation for the NutriAI project. This document provides an in-depth guide to the various features, methods, and technologies used in this advanced nutritional analysis.
   ''')

   # Custom CSS for improved UI
   st.markdown("""
   <style>
   .stExpander {
      background-color: #f0f8ff;
      border-radius: 10px;
      margin-bottom: 1rem;
   }
   .stExpander > div > div > div > div > div > p {
      color: #333;
      font-size: 16px;
   }
   .stExpander > div > div > div > div > div > ul {
      color: #333;
      font-size: 16px;
   }
   .stExpander > div > div > div > div > div > ol {
      color: #333;
      font-size: 16px;
   }
   </style>
   """, unsafe_allow_html=True)

   # Introduction
   with st.expander("📌 Introduction"):
      st.write('''
      NutriAI is a cutting-edge nutritional analysis and recommendation system that leverages various AI technologies to provide personalized meal plans, analyze nutritional content, and offer intelligent recommendations for healthy living. The project combines multiple AI models and APIs to deliver a comprehensive suite of nutrition-related tools.
      
      A key component of this system is the `nutri_info.py` module, which provides advanced ingredient analysis capabilities using AI-powered image recognition and natural language processing.
      ''')

   # Key Features
   with st.expander("🔑 Key Features"):
      st.write('''
      1. **Personalized Meal Planning**: Generate customized meal plans based on user preferences and dietary requirements.
      2. **Food Analysis**: Analyze the nutritional content of various foods using image recognition or text input.
      3. **Interactive Nutrition Quiz**: Test your nutrition knowledge with an AI-generated quiz.
      4. **NutriQA**: An AI-powered question-answering system for nutritional advice.
      5. **Recipe Generation**: Create new recipes or healthier alternatives to existing dishes.
      6. **Shopping Link Generation**: Generate affiliate links for ingredients on popular platforms.
      7. **Ingredient Analysis**: Utilize AI to categorize ingredients as healthy or unhealthy and identify potential health issues (powered by `nutri_info.py`). Now with improved image processing capabilities.
      8. **NutriChat**: An AI-powered chatbot that will help users in their nutritional journey. 
      ''')

   # Technologies and Platforms
   with st.expander("💻 Technologies and Platforms"):
      col1, col2 = st.columns(2)
      with col1:
         st.subheader("APIs")
         st.write("""
         - Together AI API
         - Google Generative AI API
         - Groq API
         - OpenAI API
         """)
         st.subheader("Web Framework")
         st.write("- Streamlit")
      with col2:
         st.subheader("Python Libraries")
         st.write("""
         - LangChain
         - LlamaIndex
         - Pillow (PIL)
         - dotenv
         """)
         
   # Project Structure
   with st.expander("🏗️ Project Structure"):
      st.write('''
      NutriAI is structured into several key components:
      ''')
      st.subheader("Streamlit Pages")
      st.write("Located in `st_pages` directory")
      st.write("""
      - docs.py
      - meal_plan.py
      - food_analysis.py
      - mcq_quiz.py
      - nutriqa.py
      - recipe_generation.py
      - nutri_info.py
      """)
      st.subheader("Utility Scripts")
      st.write("Located in `utils` directory")
      st.write("""
      - food_analysis.py
      - meal_plan.py
      - mcq_quiz.py
      - nutriqa.py
      - recipe_generation.py
      - shopping_link_generation.py
      - nutri_info.py 
      """)
      st.subheader("Configuration and Styling")
      st.write("""
      - `.env`: Environment variables and API keys
      - `config.toml`: Streamlit settings
      - `style.css`: Custom styles
      - `templates/`: HTML templates
      """)

   # How to Use
   with st.expander("🚀 How to Use"):
      st.write('''
      Using NutriAI is straightforward:
      ''')
      for i, step in enumerate([
         "Navigate through different sections using the sidebar.",
         "Input your dietary preferences, goals, and constraints.",
         "Utilize various features like meal planning, food analysis, or recipe generation.",
         "For ingredient analysis, upload an image or enter ingredients as text.",
         "Review the AI-generated results and adjust as needed.",
         "Explore the interactive quiz and chatbot for more nutrition information."
      ], 1):
         st.markdown(f"{i}. {step}")

   # # API Integration
   # with st.expander("🔌 API Integration"):
   #    st.write('''
   #    NutriAI integrates multiple APIs to provide its diverse functionality:
   #    ''')
   #    api_info = {
   #       "Together AI API": "Meal planning and NutriQA chatbot",
   #       "Google Generative AI API": "Food analysis and ingredient categorization (used in nutri_info.py)",
   #       "Groq API": "Recipe generation and quiz creation",
   #       "OpenAI API": "General recommendations"
   #    }
   #    for api, purpose in api_info.items():
   #       st.markdown(f"- **{api}**: {purpose}")
   #    st.info("API keys are managed securely through environment variables.")

   # Data Handling and Privacy
   with st.expander("🔒 Data Handling and Privacy"):
      st.write('''
      - User data is processed locally and not stored persistently.
      - API requests are made securely, transmitting only necessary information.
      - No personal information is shared with third-party services.
      - Image data for ingredient analysis is converted to base64 and transmitted securely.
      ''')

   # Future Enhancements
   with st.expander("🔮 Future Enhancements"):
      st.write('''
      Planned improvements for NutriAI include:
      ''')
      enhancements = [
         "Integration with fitness tracking devices",
         "Expanded database of regional cuisines",
         "Advanced dietary pattern analysis",
         "Collaborative meal planning for households",
         "Further improvements to image analysis capabilities",
         "Support for additional image formats and sources",
         "Integration of nutritional databases for more comprehensive analysis"
      ]
      for enhancement in enhancements:
         st.markdown(f"- {enhancement}")

   # Version Information
   with st.expander("ℹ️ Version Info"):
        st.write('''
        **Current Version**: 2.3.0
        ''')
        st.subheader("Change Log")
        versions = {
            "2.3.0": "Updated new AI models and APIs and improved image processing capabilities",
            "2.2.0": "Integrated nutri_info.py for advanced ingredient analysis",
            "2.1.0": "Added recipe generation and shopping link features",
            "2.0.0": "Integrated multiple AI models for enhanced functionality",
            "1.3.0": "Added advanced recommendation features",
            "1.2.0": "Improved nutritional analysis algorithms",
            "1.0.0": "Initial release with basic meal planning and analysis"
        }
        for version, changes in versions.items():
            st.markdown(f"- **{version}**: {changes}")
   
   st.markdown("""
        <div style='position: fixed; left: 10px; bottom: 10px;'>
            <img src="https://raw.githubusercontent.com/gaurav21s/nutriai/v2/style/nutriai-favicon-color.png" alt="NutriAI Logo" width="50" height="50">
        </div>
        <div style='position: fixed; right: 10px; bottom: 10px;'>
            <a href="https://github.com/gaurav21s" target="_blank">@gaurav21s</a>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    show()