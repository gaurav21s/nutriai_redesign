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
    """Display the nutrition analysis results with modern design elements."""
    logger.info('Displaying Food analysis result')
    # print(response)
    # CSS for styling the new sections
    st.markdown("""
    <style>
        .food-items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        .food-items-table th, .food-items-table td {
            padding: 12px;
            border: 1px solid #ddd;
            text-align: left;
        }
        .food-items-table th {
            background-color: #F4AB4F;
            color: white;
        }
        .food-items-table tr:hover {
            background-color: rgba(214, 33, 118, 0.1);
        }

        .nutrition-cards {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .nutrition-card {
            background-color: #fff;
            border-radius: 10px;
            padding: 15px;
            width: 18%;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: all 0.3s ease;
        }
        .nutrition-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
        }
        .nutrition-card-title {
            font-size: 1rem;
            font-weight: bold;
            color: #15627D;
        }
        .nutrition-card-value {
            font-size: 1.2rem;
            font-weight: bold;
            color: #d62176;
        }

        .verdict-card {
            background-color: #fff;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            text-align: center;
        }
        .verdict-card.healthy {
            transition: background-color 0.3s ease;
        }
        .verdict-card.not-healthy {
            transition: background-color 0.3s ease;
        }
        .verdict-card.healthy:hover {
            background-color: rgba(0, 128, 0, 0.5);  /* Green hover for healthy */
        }
        .verdict-card.not-healthy:hover {
            background-color: rgba(244, 171, 79, 0.5);  /* #F4AB4F with opacity for not healthy */
        }
        .verdict-card-text {
            font-size: 1.2rem;
            font-weight: bold;
            color: #333;
        }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("🍽️ Your Nutrition Breakdown:")

    sections = re.split(r'(?:Total:|Verdict:|Facts:)', response)

    if len(sections) >= 3:
        # Food Items Section: Display as a modern table
        food_items_section = sections[0].strip()
        if food_items_section:
            food_items = food_items_section.split("\n")
            st.write("Food Items:")
            st.markdown("""
            <table class="food-items-table">
                <thead>
                    <tr>
                        <th>Food Item</th>
                        <th>Nutritional Information</th>
                    </tr>
                </thead>
                <tbody>
            """, unsafe_allow_html=True)
            
            for item in food_items:
                # Split based on the first hyphen to avoid issues with multi-hyphen values
                if '-' in item:
                    food_item, nutrition_info = item.split(' - ', 1)
                    st.markdown(f"""
                    <tr>
                        <td>{food_item.strip()}</td>
                        <td>{nutrition_info.strip()}</td>
                    </tr>
                    """, unsafe_allow_html=True)

            st.markdown("</tbody></table>", unsafe_allow_html=True)

        # Total Nutrition Section: Display 5 square cards
        total_nutrition_section = sections[1].strip()
        if total_nutrition_section:
            nutrition_values = re.findall(r'(\d+[-]\d+)\s*(calories|g\s*carbs|g\s*fiber|g\s*protein|g\s*fats)', total_nutrition_section)
            nutrition_dict = {nutrient: value for value, nutrient in nutrition_values}
            st.write("Total Nutrition:")
            st.markdown(f"""
            <div class="nutrition-cards">
                <div class="nutrition-card">
                    <div class="nutrition-card-title">Calories</div>
                    <div class="nutrition-card-value">{nutrition_dict.get('calories', 'N/A')}</div>
                </div>
                <div class="nutrition-card">
                    <div class="nutrition-card-title">Carbs</div>
                    <div class="nutrition-card-value">{nutrition_dict.get('g carbs', 'N/A')}</div>
                </div>
                <div class="nutrition-card">
                    <div class="nutrition-card-title">Fiber</div>
                    <div class="nutrition-card-value">{nutrition_dict.get('g fiber', 'N/A')}</div>
                </div>
                <div class="nutrition-card">
                    <div class="nutrition-card-title">Protein</div>
                    <div class="nutrition-card-value">{nutrition_dict.get('g protein', 'N/A')}</div>
                </div>
                <div class="nutrition-card">
                    <div class="nutrition-card-title">Fats</div>
                    <div class="nutrition-card-value">{nutrition_dict.get('g fats', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Verdict Section: Medium card with hover effect (green for healthy, #F4AB4F fading for not healthy)
        verdict_section = sections[2].strip()
        if verdict_section:
            verdict_class = "not-healthy" if "Not" in verdict_section else "healthy"
            st.markdown(f"""
            <div class="verdict-card {verdict_class}">
                <div class="verdict-card-text">{verdict_section}</div>
            </div>
            """, unsafe_allow_html=True)
        # Display facts
        if len(sections) > 3:
            facts_section = sections[3].strip()
            if facts_section:
                st.text("Interesting Facts:")
                st.info(facts_section)
    else:
        st.warning("Unable to get the nutrition value of this food item.")