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

    st.markdown("""
    <h1 style='text-align: center; color: #15627D;'>Welcome to NutriAI</h1>
    <h3 style='text-align: center; color: #333;'>Your Personal Nutrition Companion 🌱</h3>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p style='text-align: center; font-size: 18px; color: #555;'>
    Discover the power of AI-driven nutritional insights for a healthier you.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <h4 style='color: #15627D;'>🔍 Food Insight</h4>
        <p>Instant nutritional analysis of your meals</p>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <h4 style='color: #15627D;'>🍽️ Meal Planner</h4>
        <p>Personalized meal suggestions tailored to you</p>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("""
        <h4 style='color: #15627D;'>👨‍🍳 Recipe Finder</h4>
        <p>Discover healthy and delicious recipes</p>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <h4 style='color: #15627D;'>🧠 NutriQuiz</h4>
        <p>Test and improve your nutrition knowledge</p>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <p style='text-align: center; font-size: 16px; color: #555;'>
    Ready to start your journey to better nutrition? Select a feature from the sidebar to begin!
    </p>
    """, unsafe_allow_html=True)
