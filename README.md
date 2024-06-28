# NutriAI: Your Nutritional Sidekick 🍽️🔍

NutriAI is a Streamlit-powered application that leverages AI to analyze food items and provide detailed nutritional information. Whether you input text or upload an image, NutriAI gives you insights into your meal's nutritional content.

Visit the webapp here [NutriAI](https://nutriai-gemini.streamlit.app/).

## Features

- Analyze food items via text input or image upload
- Calculate total nutritional values including calories, macronutrients, etc.
- Provide a health verdict on the analyzed food
- Share interesting nutrition facts
- User-friendly interface with clear results presentation

## Installation

1. Clone the repository:
```shell
git clone https://github.com/gaurav21s/nutriai.git
cd nutriai
```

2. Install dependencies:
```shell
pip install -r requirements.txt
```
3. Set up environment variables:
Create a `.env` file in the project root and add your API key:
GOOGLE_API_KEY=your_api_key_here

## Usage

1. Run the Streamlit app:
```shell
streamlit run app.py
```
2. Open your web browser and navigate to `http://localhost:8501`

3. Use the application:
- Enter food items in the text input, or
- Upload a food image
- Click "Analyze My Food" to get results

## Code Structure

- `app.py`: Main application file containing the `NutriAIApp` class
- `nutriai.py`: Contains the `NutriAI` class for food analysis
- `logger.py`: Logging configuration

## Key Components

### NutriAIApp Class

The main application class with methods:

- `__init__()`: Initializes the app and session state
- `run()`: Main method to run the Streamlit application
- `analyze_food()`: Processes user input and calls NutriAI for analysis
- `display_results()`: Presents analysis results to the user
- `clear_inputs()`: Resets user inputs and results

### NutriAI Class

Handles the core food analysis functionality (implementation details in `nutriai.py`).

## Customization

You can customize the application by modifying:

- Page configuration in `configure_page()` method
- UI elements and layout in the `run()` method
- Results display in `display_results()` method

## Dependencies

- streamlit
- PIL (Python Imaging Library)
- Additional dependencies listed in `requirements.txt`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgements

- Google Generative AI for powering the food analysis
- Streamlit for the awesome web app framework
