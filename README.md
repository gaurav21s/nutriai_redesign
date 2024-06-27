# NutriAI: Your Fun Food Detective! 🕵️‍♂️🍔

NutriAI is a vibrant Streamlit application that calculates food nutrition values using Google's Generative AI. It analyzes food items from images or text input and provides nutritional information in an engaging manner.

## Features

- Analyze food items via text input or image upload
- Calculate total calories, macronutrients, and other nutritional values
- Provide a verdict on the healthiness of the food
- Share interesting nutrition facts about the analyzed items
- Fun and engaging user interface

## Installation

1. Clone this repository:
git clone https://github.com/yourusername/nutriai.git
cd nutriai

2. Install the required dependencies:
pip install -r requirements.txt

3. Set up your environment variables:
Create a `.env` file in the project root and add your Google API key:
GOOGLE_API_KEY=your_google_api_key_here

## Usage

Run the Streamlit app:
streamlit run nutriai.py

Then, open your web browser and go to `http://localhost:8501` to use the application.

## How it works

1. Input your food items:
   - Type in your food items in the text input, or
   - Upload a photo of your meal

2. Click "Analyze My Food!" to start the analysis

3. View the results:
   - List of food items detected
   - Total nutritional breakdown
   - Verdict on the healthiness of the meal
   - Fun nutrition facts

## Dependencies

- streamlit
- python-dotenv
- google-generativeai
- Pillow

## Environment Variables

- `GOOGLE_API_KEY`: API key for Google's Generative AI

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

- Google Generative AI for powering the food analysis
- Streamlit for the awesome web app framework
- All the food lovers out there who inspired this project! 🍕🥗
