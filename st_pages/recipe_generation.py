import streamlit as st
import os
from utils.logger import logger
from utils.recipe_generation import RecipeGenerator
from utils.shopping_link_generation import ShoppingLinkGenerator

def show():
    """
    Display the Recipe generation page of the NutriAI application.

    This function handles the layout and functionality of the recipe generation page,
    including user inputs and recipe display.
    """
    logger.info("Started Recipe generation page")
    st.title("NutriAI Recipe Recommender")
    st.subheader("Get recipe recommendation based on your preferences 🍳👨‍🍳")

    # User inputs
    dish_name = st.text_input("Enter a dish name or cuisine type:", placeholder="e.g., Milkshake, Paratha, Bread Sandwich")
    
    recipe_type = st.selectbox("What type of recipe would you like?", 
                               ["Normal", "Healthier alternative", "New healthy and trendy recipe"])

    if st.button("Generate Recipe", type="primary"):
        if not dish_name:
            st.warning("Please enter a dish name or cuisine type.")
        else:
            with st.spinner("Generating your recipe..."):
                recipe_generator = RecipeGenerator()
                recipe_type_map = {
                    "Normal": "normal",
                    "Healthier alternative": "healthier",
                    "New healthy and trendy recipe": "new_healthy"
                }
                result = recipe_generator.generate_recipe(dish_name, recipe_type_map[recipe_type])
                st.session_state.recipe_result = result

    if st.session_state.get('recipe_result'):
        st.success("Recipe generated successfully!")
        display_recipe(st.session_state.recipe_result)

        if st.button("Generate New Recipe", key="new_recipe_button"):
            st.session_state.recipe_result = None
            st.experimental_rerun()

def display_recipe(recipe: str):
    """Display the generated recipe with simple formatting and shopping links."""
    logger.info("Displaying Recipe generation results")
    st.subheader("🍽️ Your Generated Recipe:")
    
    # Split the recipe into sections
    print(recipe)
    sections = recipe.split('\n\n')
    
    ingredients = []
    for section in sections:
        if section.strip():
            # Extract the section title (if present)
            if "List" in section:
                # Extract the ingredient list without quantities
                ingredient_list = section.replace("Ingredient List:", "").strip()
                ingredients = [ing.strip().title() for ing in ingredient_list.split(',')]
            elif 'Name' in section:
                title, content = section.split(':', 1)
                st.markdown(f"##### {title.strip()}:")
                lines = content.strip().split('\n')
                for line in lines:
                    st.info(line.strip())
            elif ':' in section.split('\n')[0]:
                title, content = section.split(':', 1)
                st.markdown(f"##### {title.strip()}:")
                lines = content.strip().split('\n')
                for line in lines:
                    st.write(line.strip())
            else:
                # If no title, just display the content
                st.write(section)
            
            st.text('')  # Add some space between sections

    if ingredients:
        show_shopping_links(ingredients)
    
    st.warning("Remember to adjust ingredients and cooking times as needed. Always follow proper food safety guidelines.")

def show_shopping_links(ingredients):
    """Display shopping links for the given ingredients."""
    st.subheader("🛒 Shopping Links for Ingredients:")
    
    shopping_generator = ShoppingLinkGenerator()
    links = shopping_generator.get_links(ingredients)
    
    num_columns = 3  # Number of columns to display ingredients and links
    
    # Calculate number of rows based on ingredients count and number of columns
    num_rows = (len(ingredients) + num_columns - 1) // num_columns
    
    for row in range(num_rows):
        row_index = row * num_columns
        cols = st.columns(num_columns)
        
        for col_index in range(num_columns):
            if row_index + col_index < len(ingredients):
                ingredient = ingredients[row_index + col_index]
                with cols[col_index]:
                    st.markdown(f"**{ingredient}**")
                    st.markdown(f"[Amazon]({links[ingredient]['Amazon']}) | [Blinkit]({links[ingredient]['Blinkit']})")


            
# Initialize session state variables
if 'recipe_result' not in st.session_state:
    st.session_state.recipe_result = None
