"""
Ingredient Analysis page module for NutriAI.

This module contains the functionality for ingredient analysis,
allowing users to input ingredients via text or image for nutritional insights.
"""

import streamlit as st
from streamlit_option_menu import option_menu
from utils.nutri_info import NutriInfo, NutriInfoConfig, IngredientAnalysis
from utils.logger import logger
from PIL import Image

def show():
    """
    Display the Ingredient Analysis page of the NutriAI application.

    This function handles the layout and functionality of the ingredient analysis page,
    including input methods for ingredient analysis and result display.
    """
    
    st.markdown("""
    <h1 style='text-align: center; color: #15627D;'>Ingredient Analysis with NutriAI</h1>
    <h3 style='text-align: center; color: #333;'>Uncover the health impact of your ingredients🥬</h3>
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
        st.subheader("📝 Enter Your Ingredients")
        input_text = st.text_input("Enter ingredients (comma-separated)", key="input_text", 
                                   placeholder='E.g., spinach, chicken, olive oil, garlic', 
                                   value="" if st.session_state.get('clear_inputs', False) else None)
        uploaded_file = None
    else:  # Image Input
        st.subheader("📸 Upload Ingredient Image")
        st.warning("🚧 This feature is coming soon!")  # Coming soon message
        # Commenting out the file uploader for now
        # uploaded_file = st.file_uploader("Upload a clear ingredient picture", 
        #                                  type=NutriInfoConfig.UPLOAD_TYPES, 
        #                                  key=f"uploaded_file_{st.session_state.get('file_uploader_key', 0)}")
        uploaded_file = None  # No file uploader for now
        input_text = ""

    if st.session_state.get('clear_inputs', False):
        st.session_state.clear_inputs = False
        st.session_state.file_uploader_key = st.session_state.get('file_uploader_key', 0) + 1
        st.rerun()

    if st.button("Analyze Ingredients", type="primary"):
        if (selected == "Text Input" and not input_text) or (selected == "Image Input" and not uploaded_file):
            st.warning(f"Please provide {'text input' if selected == 'Text Input' else 'an image'} for analysis.")
        else:
            with st.spinner("Analyzing your ingredients..."):
                nutri_info = NutriInfo()
                result = nutri_info.analyze_nutrition(input_text, uploaded_file)
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

def display_results(result: IngredientAnalysis):
    """Display the ingredient analysis results."""
    logger.info('Displaying Ingredient analysis result')
    st.subheader("🍽️ Your Ingredient Analysis:")
    
    # Display healthy ingredients
    st.subheader("✅ Safe Ingredients:")
    if result.healthy_ingredients:
        st.success(", ".join(result.healthy_ingredients))
    else:
        st.info("No specifically healthy ingredients identified.")

    # Display unhealthy ingredients
    st.subheader("⚠️ Ingredients to Be Mindful Of:")
    if result.unhealthy_ingredients:
        st.warning(", ".join(result.unhealthy_ingredients))
    else:
        st.info("No particularly concerning ingredients identified.")

    # Display health issues
    if result.health_issues:
        st.subheader("🚫 Potential Health Concerns:")
        for ingredient, issues in result.health_issues.items():
            st.error(f"**{ingredient}**: {', '.join(issues)}")
    
    # Overall summary
    st.subheader("📊 Overall Nutritional Summary:")
    total_ingredients = len(result.healthy_ingredients) + len(result.unhealthy_ingredients)
    healthy_percentage = (len(result.healthy_ingredients) / total_ingredients) * 100 if total_ingredients > 0 else 0
    
    st.write(f"Your ingredient list contains {len(result.healthy_ingredients)} healthy ingredients "
             f"and {len(result.unhealthy_ingredients)} ingredients to be mindful of.")

if __name__ == "__main__":
    show()