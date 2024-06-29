"""
Meal Plan page module for NutriAI.

This module contains the functionality for meal plan generation,
allowing users to input their preferences and receive a personalized meal plan.
"""
import re
import streamlit as st
from utils.meal_plan import MealPlan
from fpdf import FPDF
import base64

def show():
    """
    Display the Meal Plan page of the NutriAI application.

    This function handles the layout and functionality of the meal plan page,
    including user preference inputs and meal plan display.
    """
    st.title("Meal Planning with NutriAI")
    st.subheader("Get your personalized meal plan based on your preferences 🍽️📅")

    # User preferences input
    goal = st.selectbox("What's your goal?", 
                        ["Gain Weight", "Loss fat", "Maintain weight", "Gain muscle", "Improve overall health"])
    
    diet_choice = st.selectbox("What's your dietary preference?", 
                               ["Vegetarian", "Vegan", "Non-vegetarian","Eggeterian"])
    
    issue = st.selectbox("Any dietary issues or allergies?",
                         options=["No issue", "Lactose intolerant", "Gluten-free", "Nut allergy", "Other"],
                         index=0)

    if issue == "Other":
        custom_issue = st.text_input("Please specify your dietary issue or allergy:")
        issue = custom_issue if custom_issue else "No issue"
        
    gym = st.radio("Work out routine?", ["do gym/workout", "do not gym/workout"])
    
    food_type = st.selectbox("What type of cuisine do you prefer?", 
                             ["Indian type", "Continental type","World wide type"])

    if st.button("Generate My Meal Plan", type="primary"):
        with st.spinner("Generating your meal plan..."):
            meal_planner = MealPlan()
            result = meal_planner.create_meal_plan(goal, diet_choice, issue, gym, food_type)
            st.session_state.meal_plan_result = result

    if st.session_state.get('meal_plan_result'):
        st.success("Meal plan generated successfully!")
        display_meal_plan(st.session_state.meal_plan_result)

        if st.button("Generate New Meal Plan", key="new_plan_button"):
            st.session_state.meal_plan_result = None
            st.experimental_rerun()

        st.success('Or Download your meal plan by submitting your name and age.')
        
        with st.form(key='download_form'):
            st.write('Download Form')
            name = st.text_input("Please enter your full name:")
            age = st.text_input("Please enter your age:")
            submit_button = st.form_submit_button(label='Submit')

        if submit_button and name:
            pdf_bytes = create_pdf(name, age, goal, diet_choice, issue, gym, food_type, st.session_state.meal_plan_result)
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:file/pdf;base64,{b64}" download="NutriAI_Meal_Plan_{name}.pdf">Download Meal Plan</a>'
            st.markdown(href, unsafe_allow_html=True)

def display_meal_plan(meal_plan: str):
    """Display the generated meal plan with styling."""
    st.subheader("🍳 Your Personalized Meal Plan:")
    
    # Define sections to find and style
    sections = ["Breakfast", "Lunch", "Pre-Workout", "Post-Workout", "Dinner"]
    
    # Split the meal plan into lines
    lines = meal_plan.split('\n')
    
    current_section = None
    meal_plan_dict = {section: [] for section in sections}
    
    # Use regex to identify sections and corresponding items
    section_pattern = re.compile(r'^(Breakfast|Lunch|Pre-Workout|Post-Workout|Dinner):$', re.IGNORECASE)
    
    for line in lines:
        line = line.strip()
        if section_pattern.match(line):
            current_section = section_pattern.match(line).group(1)
        elif current_section and line:
            meal_plan_dict[current_section].append(line)
    
    # Display the meal plan with styling
    for section, items in meal_plan_dict.items():
        if items:
            st.markdown(f"##### {section} options:")
            for item in items:
                item_cleaned = item.replace('[', '').replace(']', '')
                st.write(f"{item_cleaned}")
    st.text('')
    st.text('')
    st.warning("Remember to adjust portion sizes as needed and consult with a healthcare professional or registered dietitian for medical needs.")

def create_pdf(name, age, goal, diet_choice, issue, gym, food_type, meal_plan):
    """Create a PDF of the meal plan with user inputs and meal plan details."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    pdf.cell(200, 10, "NutriAI Meal Plan", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Name: {name}", ln=True)
    pdf.cell(200, 10, f"Age: {age}", ln=True)
    pdf.cell(200, 10, f"Goal: {goal}", ln=True)
    pdf.cell(200, 10, f"Dietary Preference: {diet_choice}", ln=True)
    pdf.cell(200, 10, f"Dietary Issues or Allergies: {issue}", ln=True)
    pdf.cell(200, 10, f"Workout Routine: {gym}", ln=True)
    pdf.cell(200, 10, f"Preferred Cuisine: {food_type}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Meal Plan", ln=True)
    pdf.set_font("Arial", size=12)
    
    sections = ["Breakfast", "Lunch", "Pre-Workout", "Post-Workout", "Dinner"]
    lines = meal_plan.split('\n')
    
    current_section = None
    meal_plan_dict = {section: [] for section in sections}
    
    section_pattern = re.compile(r'^(Breakfast|Lunch|Pre-Workout|Post-Workout|Dinner):$', re.IGNORECASE)
    
    for line in lines:
        line = line.strip()
        if section_pattern.match(line):
            current_section = section_pattern.match(line).group(1)
        elif current_section and line:
            meal_plan_dict[current_section].append(line)
    
    for section, items in meal_plan_dict.items():
        if items:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, f"{section} options:", ln=True)
            pdf.set_font("Arial", size=12)
            for item in items:
                item_cleaned = item.replace('[', '').replace(']', '')
                pdf.cell(200, 10, f" - {item_cleaned}", ln=True)
    
    return pdf.output(dest='S').encode('latin1')

# Initialize session state variables
if 'meal_plan_result' not in st.session_state:
    st.session_state.meal_plan_result = None
