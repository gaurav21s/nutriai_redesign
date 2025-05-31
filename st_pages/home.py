"""
Home page module for NutriAI.
This module contains the content for the home page of the NutriAI application,
providing an introduction and overview of the app's features.
"""
import streamlit as st
from utils.logger import logger
def create_feature_card(title, icon, description):
    return f"""
    <div class="feature-card" onclick="handleCardClick('{title.lower().replace(' ', '_')}')">
        <div class="card-content">
            <i class="{icon}"></i>
            <h3>{title}</h3>
            <p>{description}</p>
        </div>
    </div>
    """

def show():
    """
    Display the home page of the NutriAI application.
    This function presents a modern and engaging introduction to NutriAI,
    highlighting its key features and benefits.
    """
    logger.info("Started Home page")

    st.markdown("""
    <style>
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr); /* 3 columns */
        gap: 1.5rem;
        margin-top: 2rem;
    }
    .feature-card {
        background-color: #f8f9fa;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        text-align: center; /* Centering content */
    }
    .feature-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
    }
    .card-content {
        padding: 1.5rem;
        background-color: rgba(255, 255, 255, 0.9);
        height: 100%;
        transition: background-color 0.3s ease;
    }
    .feature-card:hover .card-content {
        background-color: rgba(214, 33, 118, 0.1);
    }
    .feature-card i {
        font-size: 3rem; /* Increase icon size */
        color: #d62176;
        margin-bottom: 1rem;
        display: block;
        transition: transform 0.3s ease;
    }
    .feature-card:hover i {
        transform: scale(1.2);
    }
    .feature-card h3 {
        color: #15627D;
        margin-bottom: 0.75rem;
        font-size: 1.3rem; /* Increase title size */
    }
    .feature-card p {
        color: #555;
        font-size: 0.95rem;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h1 style='text-align: center; color: #15627D;'>Welcome to NutriAI</h1>
    <h3 style='text-align: center; color: #333;'>Your Personal Nutrition Companion 🌱</h3>
    <p style='text-align: center; font-size: 18px; color: #555;'>
    Discover the power of AI-driven nutritional insights for a healthier you.
    </p>
    <h2 style='text-align: center; color: #15627D; margin-top: 2rem;'>Our Features</h2>
    """, unsafe_allow_html=True)

    feature_cards = """
    <div class="feature-grid">
        {0}
        {1}
        {2}
        {3}
        {4}
        {5}
        {6}
        {7}
        {8}
    </div>
    """.format(
        create_feature_card("Food Insight", "ri-eye-line", "Gain deep insights into the nutritional content of your food with our AI-powered analysis."),
        create_feature_card("Meal Planner", "ri-calendar-line", "Get personalized meal plans tailored to your dietary needs and preferences."),
        create_feature_card("Recipe Finder", "ri-book-open-line", "Discover new, healthy recipes based on your favorite ingredients and dietary restrictions."),
        create_feature_card("NutriQuiz", "ri-question-line", "Test your nutrition knowledge with our AI-generated quizzes."),
        create_feature_card("Ingredient Checker", "ri-search-line", "Quickly check the nutritional value and potential allergens in any ingredient."),
        create_feature_card("NutriChat", "ri-message-3-line", "Chat with our AI nutritionist for personalized advice and answers to your nutrition questions."),
        create_feature_card("NutriCalc", "ri-calculator-line", "Calculate your BMI and maintenance calories for personalized health insights."),
        create_feature_card("About Us", "ri-information-line", "Learn more about NutriAI and our mission to revolutionize nutrition with AI."),
        create_feature_card("NutriAI Articles", "ri-article-line", "Read our latest articles on nutrition, AI, and healthy living.")
    )

    st.markdown(feature_cards, unsafe_allow_html=True)

    # Footer
    st.markdown("""
        <div style='position: fixed; left: 10px; bottom: 10px;'>
            <img src="https://raw.githubusercontent.com/gaurav21s/nutriai/v2/style/nutriai-favicon-color.png" alt="NutriAI Logo" width="50" height="50">
        </div>
        <div style='position: fixed; right: 10px; bottom: 10px;'>
            <a href="https://github.com/gaurav21s" target="_blank">@gaurav21s</a>
        </div>
    """, unsafe_allow_html=True)

    # Add JavaScript to handle card clicks
    st.markdown("""
    <script>
    function handleCardClick(feature) {
        const baseUrl = window.location.href.split('?')[0];
        window.location.href = baseUrl + '?nav=' + feature;
    }
    </script>
    """, unsafe_allow_html=True)

    # Add Remix icon CSS
    st.markdown('<link href="https://cdn.jsdelivr.net/npm/remixicon@2.5.0/fonts/remixicon.css" rel="stylesheet">', unsafe_allow_html=True)
