"""
Meal Plan page module for NutriAI.

This module contains the functionality for meal plan generation,
allowing users to input their preferences and receive a personalized meal plan.
"""
import re
import streamlit as st
from utils.meal_plan import MealPlan
from utils.logger import logger
from fpdf import FPDF
import base64

def show():
    """
    Display the Meal Plan page of the NutriAI application.

    This function handles the layout and functionality of the meal plan page,
    including user preference inputs and meal plan display.
    """
    logger.info("Started Meal plan page")
    st.title("Meal Planning with NutriAI")
    st.subheader("Get your personalized meal plan based on your preferences 🍽️📅")

    # User preferences input
    gender = st.radio("Your gender:",['Male','Female'])
    
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
    
    height = st.text_input("What's your height with unit?",
                           placeholder='E.g. 5 ft 11 inch, 1.8 meter, 180cm')

    weight = st.text_input("What's your weight with unit?",
                           placeholder='E.g. 69kg, 152 pounds')
    
    food_type = st.selectbox("What type of cuisine do you prefer?", 
                             ["Indian type", "Continental type","World wide type"])

    if st.button("Generate My Meal Plan", type="primary"):
        # if (not height) and (not weight):
        #     st.warning("Please enter your height and weight.")
        # else:
        with st.spinner("Generating your meal plan..."):
            meal_planner = MealPlan()
            result = meal_planner.create_meal_plan(gender, goal, diet_choice, issue, gym, height, weight, food_type)
            st.session_state.meal_plan_result = result

    if st.session_state.get('meal_plan_result'):
        st.success("Meal plan generated successfully!")
        display_meal_plan(st.session_state.meal_plan_result)

        if st.button("Generate New Meal Plan", key="new_plan_button"):
            st.session_state.meal_plan_result = None
            st.experimental_rerun()

        st.markdown("""
        <div style='padding: 10px; border-radius: 5px; background-color: #f0f2f6;'>
            <h4 style='color: #1f618d; text-align: center;'>
                Download your meal plan by submitting your name and age
            </h4>
        </div>
        <p></p>
        """, unsafe_allow_html=True)
    
        with st.form(key='download_form'):
            st.write('Download Form')
            name = st.text_input("Please enter your full name:", placeholder="Your name please")
            age = st.text_input("Please enter your age:", placeholder="Your age please")
            submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            if not name or not age:
                st.warning("Please enter both your name and age.")
            else:
                pdf_bytes = create_pdf(name, age, gender, goal, diet_choice, issue, gym, height, weight, food_type, st.session_state.meal_plan_result)
                
                st.download_button(
                    label="Download Meal Plan",
                    data=pdf_bytes,
                    file_name=f"NutriAI_Meal_Plan_{name}.pdf",
                    mime="application/pdf"
                )


def display_meal_plan(meal_plan: str):
    """Display the generated meal plan with styling."""
    logger.info("Displaying Meal plan results")
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

def create_pdf(name, age, gender,goal, diet_choice, issue, gym, height, weight, food_type, meal_plan):
    """
    Create a PDF document containing the user's personalized meal plan.

    This function generates a professionally formatted PDF with the user's information
    and their customized meal plan. It uses a modern design with carefully chosen fonts
    and color schemes to enhance readability and visual appeal.
    Returns:
    --------
    bytes
        The PDF document as a byte string.
    """
    logger.info('Creating PDF for Meal plan')
    class PDF(FPDF):
        def footer(self):
            self.set_y(-10)
            self.set_font('Helvetica', 'I', 9)  # Increased font size
            self.set_text_color(127, 140, 141)
            self.cell(60, 10, 'NutriAI', 0, 0, 'L')
            self.cell(60, 10, f'Page {self.page_no()}', 0, 0, 'C')
            self.cell(60, 10, 'Created by Gaurav Shrivastav', 0, 0, 'R')

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Color scheme
    primary_color = (52, 152, 219)  # Blue
    secondary_color = (46, 204, 113)  # Green
    text_color = (44, 62, 80)  # Dark Blue
    
    # Add decorative element first
    pdf.set_draw_color(*secondary_color)
    pdf.set_fill_color(*secondary_color)
    pdf.rect(10, 10, 190, 18, 'F')  # Increased height
    
    # Add title over the green rectangle
    pdf.set_font('Helvetica', 'B', 24)  # Increased font size
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.cell(0, 18, 'NutriAI Meal Plan', 0, 1, 'C', 0)
    
    pdf.ln(5)  # Reduced space after the title
    
    # User Information Section
    pdf.set_font("Helvetica", 'B', 15)  # Increased font size
    pdf.set_text_color(*text_color)
    pdf.cell(0, 10, "User Information:", 0, 1, 'L')
    
    pdf.set_font("Helvetica", '', 11)  # Increased font size
    user_info = [
        f"Name: {name}", f"Age: {age}", f"Gender: {gender}",f"Height: {height}", f"Weight: {weight}",
        f"Goal: {goal}", f"Dietary Preference: {diet_choice}", 
        f"Dietary Issues or Allergies: {issue}", f"Workout Routine: {gym}",
        f"Preferred Cuisine: {food_type}"
    ]
    
    for i, info in enumerate(user_info):
        pdf.cell(95, 8, info, 0, 1 if i % 2 else 0)
    pdf.ln(5)  # Reduced space after user info
    
    # Meal Plan Section
    pdf.set_font("Helvetica", 'B', 15)  # Increased font size
    pdf.cell(0, 10, "Your Personalized Meal Plan:", 0, 1, 'L')
    pdf.ln(5)
    sections = ["Breakfast", "Lunch", "Pre-Workout", "Post-Workout", "Dinner"]
    lines = meal_plan.split('\n')
    
    meal_plan_dict = _parse_meal_plan(lines, sections)
    
    for section, items in meal_plan_dict.items():
        if items:
            pdf.set_font("Helvetica", 'B', 13)  # Increased font size
            pdf.set_fill_color(*primary_color)
            pdf.cell(0, 8, f"{section} options:", 0, 1, 'L', 1)
            pdf.set_font("Helvetica", '', 10)  # Increased font size
            for item in items:
                item_cleaned = item.replace('[', '').replace(']', '')
                pdf.cell(5)
                pdf.ln(2)
                pdf.multi_cell(0, 6, f"- {item_cleaned}", 0, 'L')
            pdf.ln(4)  # Reduced space between meal sections
    
    # Add a note at the end
    pdf.set_font("Helvetica", 'I', 10)  # Increased font size
    pdf.set_text_color(127, 140, 141)
    pdf.multi_cell(0, 5, "Note: Remember to adjust portion sizes as needed and consult with a healthcare professional or registered dietitian for medical needs.", 0, 'L')
    
    return pdf.output(dest='S').encode('latin1')

def _parse_meal_plan(lines, sections):
    """
    Parse the meal plan string into a structured dictionary.

    Parameters:
    -----------
    lines : list
        List of strings representing each line of the meal plan.
    sections : list
        List of meal plan sections to look for.

    Returns:
    --------
    dict
        A dictionary with sections as keys and lists of meal items as values.
    """
    current_section = None
    meal_plan_dict = {section: [] for section in sections}
    
    section_pattern = re.compile(r'^(Breakfast|Lunch|Pre-Workout|Post-Workout|Dinner):$', re.IGNORECASE)
    
    for line in lines:
        line = line.strip()
        if section_pattern.match(line):
            current_section = section_pattern.match(line).group(1)
        elif current_section and line:
            meal_plan_dict[current_section].append(line)
    
    return meal_plan_dict

# Initialize session state variables
if 'meal_plan_result' not in st.session_state:
    st.session_state.meal_plan_result = None
