# NutriAI: Your Nutrition Companion 🍽️🧠

NutriAI is a comprehensive, AI-powered nutrition application built with Streamlit. It offers a suite of tools to help users make informed dietary choices, plan meals, and learn about nutrition.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://nutriaiv2.streamlit.app/)

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Contributing](#contributing)
- [License](#license)

## Features

NutriAI offers a wide range of features to support your nutritional journey:

1. **Food Insight**: Analyze food items via text input or image upload for detailed nutritional information.
2. **Meal Planner**: Generate personalized meal plans based on dietary preferences and nutritional goals.
3. **Recipe Finder**: Discover and create new recipes tailored to your tastes and dietary requirements.
4. **NutriQuiz**: Test and expand your nutrition knowledge with an AI-generated quiz.
5. **Nutri Calc**: Calculate and track your daily nutritional intake.
6. **NutriChat**: Get instant answers to your nutrition-related questions from an AI assistant.
7. **NutriAI Articles**: Access a curated collection of informative articles on various nutrition topics.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/nutriai.git
   cd nutriai
   ```

2. Set up a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_API_KEY=your_google_api_key
   TOGETHER_API_KEY=your_together_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

## Usage

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your web browser and navigate to `http://localhost:8501`

3. Use the navigation menu to explore different features of NutriAI:
   - Analyze foods in the "Food Insight" section
   - Generate meal plans in the "Meal Planner" section
   - Find recipes in the "Recipe Finder" section
   - Take a nutrition quiz in the "NutriQuiz" section
   - Calculate nutritional intake in the "Nutri Calc" section
   - Chat with the AI assistant in the "NutriChat" section
   - Read nutrition articles in the "NutriAI Articles" section

## Project Structure

The project structure is designed to be modular and easy to navigate:

- `app.py`: The main entry point for the Streamlit application
- `requirements.txt`: Lists all project dependencies
- `.env`: Contains environment variables (not tracked by git)
- `README.md`: Provides project documentation and setup instructions

Key directories:
- `style/`: Houses UI components and custom CSS
- `st_pages/`: Contains individual feature pages (e.g., food analysis, meal planning)
- `utils/`: Includes utility functions and helpers for various features
- `yaml/`: Stores YAML configuration files, such as article data

This structure promotes separation of concerns and makes it easier to maintain and extend the application as it grows.


## Technologies Used

- [Python](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [OpenAI API](https://openai.com/api/)
- [Google Cloud Vision API](https://cloud.google.com/vision)
- [Together AI](https://www.together.ai/)
- [Groq](https://groq.com/)

## Contributing

We welcome contributions to NutriAI! Please follow these steps to contribute:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

Please ensure your code adheres to our coding standards and includes appropriate tests.

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Gaurav Shrivastav - [LinkedIn](https://www.linkedin.com/in/gaurav-shrivastav-gs/)

Project Link: [NutriAI](https://github.com/gaurav21s/nutriai/tree/v2)

## Acknowledgements

- [Streamlit](https://streamlit.io/)
- [OpenAI](https://openai.com/)
- [Google Cloud](https://cloud.google.com/)
- [Together AI](https://www.together.ai/)
- [Groq](https://groq.com/)