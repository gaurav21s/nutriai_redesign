### NutriAI APP
from dotenv import load_dotenv

load_dotenv() ## load all the environment variables

import streamlit as st
import os
import google.generativeai as genai
from PIL import Image

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

## Function to load Google Gemini Pro Vision API And get response

def get_gemini_repsonse(input,image,prompt):
    model=genai.GenerativeModel('gemini-pro-vision')
    response=model.generate_content([input,image[0],prompt],
                                    generation_config=genai.types.GenerationConfig(
                                        temperature=0.001)
                                    )
    return response.text

def get_gemini_text(prompt):
    input = prompt
    model=genai.GenerativeModel('gemini-pro')
    response=model.generate_content(input,
                                    generation_config=genai.types.GenerationConfig(
                                        temperature=0.001)
                                    )
    return response.text


def input_image_setup(uploaded_file):
    # Check if a file has been uploaded
    if uploaded_file is not None:
        # Read the file into bytes
        bytes_data = uploaded_file.getvalue()

        image_parts = [
            {
                "mime_type": uploaded_file.type,  # Get the mime type of the uploaded file
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")
    
##initialize our streamlit app

st.set_page_config(page_title="NutriAI WebApp",
                   page_icon='🍱')

st.header("NutriAI WebApp")
st.subheader('Calculate the food nutrition value' )

st.write('-----------------------------------------------------------------------------------------')
st.write('Please upload image or enter the input')

input=st.text_input("Input items: ",key="input",placeholder='Specify the quantity and items (not necessary)')
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
image=""   
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image.", use_column_width=True)


submit=st.button("Calculate")

img_input_prompt="""
You are an expert nutritionist where you need to see the food items from the image
               and calculate the total calories, and all other nutrition value like carbs, fibre, protein, fats also provide the details of every food items according to proportion or quantity with calories intake
               is below format

               1. Item 1 (quantity)- no of calories, carbs, fibre, protein, fats and other details(if available)
               2. Item 2 (quantity)- no of calories, carbs, fibre, protein, fats and other details(if available)
               ----
               ----

            Total: calories, carbs, fibre, protein, fats
            Verdict: Healthy or Not Healthy
            Facts: Interesting and Fun nutrition facts about dish 
"""
text_input_prompt = f"""
You are an expert nutritionist and you have to calculate nutrition value from these food items or dish list = [{input}] only
Follow this format strictly and dont add extra things.

               1. Item 1 (quantity)- no of calories, carbs, fibre, protein, fats and other details(if available)
               2. Item 2 (quantity)- no of calories, carbs, fibre, protein, fats and other details(if available)
               ----
               ----

            Total: calories, carbs, fibre, protein, fats
            Verdict: Healthy or Not Healthy
            Facts: Interesting and Fun nutrition facts about dish 
"""
## If submit button is clicked

if image:
    if submit:
        image_data=input_image_setup(uploaded_file)
        response=get_gemini_repsonse(img_input_prompt,image_data,input)
        st.subheader("Here are the Nutrition values:\n")
        st.write(response)

elif submit and input:
    response=get_gemini_text(text_input_prompt)
    st.subheader("Here are the Nutrition values:\n")
    st.write(response)
