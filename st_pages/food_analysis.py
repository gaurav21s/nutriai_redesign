"""
Food Analysis page module for NutriAI.

This module contains the functionality for food analysis,
allowing users to input food items via text or image for nutritional analysis.
"""

import streamlit as st
import re
from streamlit_option_menu import option_menu
from utils.food_analysis import FoodAnalysis, FoodAnalysisConfig
from utils.logger import logger
from PIL import Image

def show():
    """
    Display the Food Analysis page of the NutriAI application.

    This function handles the layout and functionality of the food analysis page,
    including input methods for food analysis and result display.
    """
    st.markdown("""
    <h1 style='text-align: center; color: #15627D;'>Food Analysis with NutriAI</h1>
    <h3 style='text-align: center; color: #333;'>Uncover the nutritional secrets of your food🥗</h3>
    """, unsafe_allow_html=True)

    # Options menu for input selection
    selected = option_menu(
        menu_title=None,
        options=["Text Input", "Image Input"],
        icons=["pencil-square", "camera-fill"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#dbf3e7"},
            "icon": {"color": "#d62176", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#E9ECEF"},
            "nav-link-selected": {"background-color": "#F4AB4F", "color": "#F8F9FA"},
        }
    )

    if selected == "Text Input":
        st.subheader("📝 Enter Your Food Items")
        input_text = st.text_input("Enter food items with quantity", key="input_text", 
                                   placeholder='E.g., 2 slices of pizza, 1 apple', 
                                   value="" if st.session_state.get('clear_inputs', False) else None)
        uploaded_file = None
    else:  # Image Input
        st.subheader("📸 Upload Food Picture")
        uploaded_file = st.file_uploader("Upload a clear food picture", 
                                         type=FoodAnalysisConfig.UPLOAD_TYPES, 
                                         key=f"uploaded_file_{st.session_state.get('file_uploader_key', 0)}")
        input_text = ""

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.session_state.get('clear_inputs', False):
        st.session_state.clear_inputs = False
        st.session_state.file_uploader_key = st.session_state.get('file_uploader_key', 0) + 1
        st.rerun()

    if st.button("Analyze My Food", type="primary"):
        if (selected == "Text Input" and not input_text) or (selected == "Image Input" and not uploaded_file):
            st.warning(f"Please provide {'text input' if selected == 'Text Input' else 'an image'} for analysis.")
        else:
            with st.spinner("Analyzing your food..."):
                food_analysis = FoodAnalysis()
                result = food_analysis.analyze_food(input_text, uploaded_file)
                st.session_state.analysis_result = result

    if st.session_state.get('analysis_result'):
        st.success("Analysis complete!")
        display_results(st.session_state.analysis_result)
        st.session_state.clear_inputs = True
        st.session_state.analysis_result = None
        st.session_state.file_uploader_key = st.session_state.get('file_uploader_key', 0) + 1

        if st.button("Clear Output and Start New Analysis", key="clear_button"):
            st.rerun()
            
    st.markdown("""
        <div style='position: fixed; left: 10px; bottom: 10px;'>
            <img src="https://raw.githubusercontent.com/gaurav21s/nutriai/v2/style/nutriai-favicon-color.png" alt="NutriAI Logo" width="50" height="50">
        </div>
        <div style='position: fixed; right: 10px; bottom: 10px;'>
            <a href="https://github.com/gaurav21s" target="_blank">@gaurav21s</a>
        </div>
    """, unsafe_allow_html=True)

def display_results(response: str):
    """Display the nutrition analysis results."""
    logger.info('Displaying Food analysis result')
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