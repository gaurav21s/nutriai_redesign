"""
Home page module for NutriAI.

This module contains the content for the home page of the NutriAI application,
providing an introduction and overview of the app's features.
"""

import streamlit as st
from utils.logger import logger

def show():
    """
    Display the home page of the NutriAI application.

    This function presents a modern and engaging introduction to NutriAI,
    highlighting its key features and benefits.
    """
    logger.info("Started Home page")
    st.title("Welcome to NutriAI: Your Personal Nutrition Companion 🌱🤝")

    st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">Discover the power of AI-driven nutritional insights!</p>', unsafe_allow_html=True)

    st.write("""
    NutriAI is your intelligent guide on the path to better health and nutrition.
    Leveraging advanced artificial intelligence, we provide you with detailed analysis of your food choices,
    personalized meal plans, and smart recommendations.
    """)

    st.subheader("🚀 Key Features:")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("✅ **Food Insight**")
        st.write("Get instant nutritional breakdown of your meals through text or image input.")

        st.markdown("✅ **Meal Planner**")
        st.write("Receive tailored meal suggestions based on your nutritional needs and preferences.")

    with col2:
        st.markdown("✅ **Recipe Recommender**")
        st.write("Discover new and healthy recipes to spice up your meals.")

        st.markdown("✅ **NutriQuiz**")
        st.write("Test your nutrition knowledge with our interactive quiz.")

    st.subheader("🎯 Start Your Journey to Better Nutrition")
    st.write("""
    Whether you're looking to maintain a balanced diet, achieve specific health goals, or simply curious about
    what's on your plate, NutriAI is here to support you every step of the way.

    Navigate through our features using the sidebar and embark on your path to nutritional wellness!
    """)

    st.markdown("**Ready to dive in? Select 'Food Insight' from the sidebar to analyze your first meal!**")
