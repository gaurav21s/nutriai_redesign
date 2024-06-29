"""
Food Analysis page module for NutriAI.

This module contains the functionality for food analysis,
allowing users to input food items via text or image for nutritional analysis.
"""

import streamlit as st
import re
from utils.food_analysis import FoodAnalysis, FoodAnalysisConfig
from PIL import Image

def show():
    """
    Display the Food Analysis page of the NutriAI application.

    This function handles the layout and functionality of the food analysis page,
    including input methods for food analysis and result display.
    """
    st.title("Food Analysis with NutriAI")
    st.subheader("Uncover the nutritional secrets of your food 🔍🥗")

    st.subheader("Choose your input method:")

    col1, col2 = st.columns(2)

    with col1:
        st.text("📝 Text Input")
        input_text = st.text_input("Enter food items with quantity", key="input_text", 
                                   placeholder='E.g., 2 slices of pizza, 1 apple', 
                                   value="" if st.session_state.clear_inputs else None)

    with col2:
        st.text("📸 Image Input")
        uploaded_file = st.file_uploader("Upload a clear food picture", 
                                         type=FoodAnalysisConfig.UPLOAD_TYPES, 
                                         key=f"uploaded_file_{st.session_state.file_uploader_key}")

    if st.session_state.clear_inputs:
        st.session_state.clear_inputs = False
        st.session_state.file_uploader_key += 1
        st.experimental_rerun()

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.button("Analyze My Food", type="primary"):
        if (input_text and uploaded_file) or (not input_text and not uploaded_file):
            st.warning("Please provide either text input OR image input, not both or neither.")
        else:
            food_analysis = FoodAnalysis()
            result = food_analysis.analyze_food(input_text, uploaded_file)
            st.session_state.analysis_result = result

    if st.session_state.analysis_result:
        st.success("Analysis complete!")
        display_results(st.session_state.analysis_result)

        if st.button("Clear Output and Start New Analysis", key="clear_button"):
            st.session_state.clear_inputs = True
            st.session_state.analysis_result = None
            st.session_state.file_uploader_key += 1
            st.experimental_rerun()

def display_results(response: str):
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