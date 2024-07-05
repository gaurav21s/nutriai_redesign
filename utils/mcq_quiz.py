import os
import re
from typing import List, Dict
from dotenv import load_dotenv
from llama_index.llms.groq import Groq
from llama_index.core.llms import ChatMessage
from utils.logger import logger
from typing import List, Dict


# Load environment variables
load_dotenv()

class QuizConfig:
    """Configuration class for MCQ Quiz application."""

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    NUM_QUESTIONS = 5  # Number of questions per quiz

class GroqHandler:
    """Handler for Groq LLM interactions."""

    def configure_api(self):
        """Configure the Groq LLM."""
        logger.info("Configuring Groq LLM")
        if not QuizConfig.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        self.llm = Groq(model="llama3-8b-8192", api_key=QuizConfig.GROQ_API_KEY, temperature=0.7)

    def get_groq_response(self) -> str:
        """
        Get response from Groq LLM.

        Args:
            prompt (str): The prompt for the model.

        Returns:
            str: The generated response text.
        """
        logger.info("Sending request to Groq LLM")

        # Set the system prompt and user messages differently
        system_prompt = "You are a quiz creator specializing in fun, interesting, and challenging multiple-choice quizzes on various topics."
        user_message = f"""Your task is to generate a quiz about food, fitness and nutrition consisting of {QuizConfig.NUM_QUESTIONS} number of questions in given specific format.
        Each question should have either two or four answer options. Two-option questions should be formatted as true/false, while four-option questions should be labeled A, B, C, and D. The questions should be engaging and include elements of humor or interesting facts in either the questions or answers.

        For each question, please provide the following:
        1. The question text
        2. The answer options (labeled appropriately), give true and false as options according to the question
        3. The correct answer 
        4. A brief, interesting explanation for the correct answer

        Please adhere strictly to the following format:

        Q1. [Question text only]
        A. [Option A Text] (or True Option for True/False question)
        B. [Option B Text] (or False Option for True/False question)
        C. [Option C Text] (if applicable)
        D. [Option D Text] (if applicable)

        Correct Answer: [A/B/C/D or A/B (incase of True/False)] (Give only A/B/C/D as answer not any other text)

        Explanation: [Brief, interesting explanation in 2-3 lines]
        
        Please repeat this format for all questions and refrain from adding any extra text or clarification.
        """

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_message),
        ]
        response = self.llm.chat(messages)
        # print(response)
        return str(response)

class QuizHandler:
    @staticmethod
    def parse_quiz_response(response: str) -> List[Dict]:
        response = response.replace('assistant: ', '')
        # print(response)
        questions = []
        current_question = {}
        question_pattern = re.compile(r'^Q(\d+)\.\s*(.+)$')
        option_pattern = re.compile(r'^([A-D])\.\s*(.+)$')
        true_false_pattern = re.compile(r'^(True|False):\s*(.+)$', re.IGNORECASE)
        correct_answer_pattern = re.compile(r'^Correct Answer:\s*([A-D]|True|False)$', re.IGNORECASE)
        explanation_pattern = re.compile(r'^Explanation:\s*(.+)$')

        for line in response.split('\n'):
            line = line.strip()
            
            if question_match := question_pattern.match(line):
                if current_question:
                    questions.append(QuizHandler._validate_question(current_question))
                current_question = {"question": question_match.group(2), "options": []}
            
            elif option_match := option_pattern.match(line):
                current_question.setdefault("options", []).append(option_match.group(2))
            
            elif true_false_match := true_false_pattern.match(line):
                current_question.setdefault("options", []).append(true_false_match.group(2))
            
            elif correct_answer_match := correct_answer_pattern.match(line):
                current_question["correct_answer"] = correct_answer_match.group(1).upper()
            
            elif explanation_match := explanation_pattern.match(line):
                current_question["explanation"] = explanation_match.group(1)
            
            elif line and current_question:  # Handle multi-line questions or explanations
                if "question" in current_question and not current_question["options"]:
                    current_question["question"] += " " + line
                elif "explanation" in current_question:
                    current_question["explanation"] += " " + line

        if current_question:
            questions.append(QuizHandler._validate_question(current_question))

        if not questions:
            raise ValueError("No valid questions were parsed from the response.")

        return questions

    @staticmethod
    def _validate_question(question: Dict) -> Dict:
        required_keys = ["question", "options", "correct_answer", "explanation"]
        if not all(key in question for key in required_keys):
            raise ValueError(f"Invalid question format: missing required fields. Question: {question}")

        if len(question["options"]) not in [2, 4]:
            raise ValueError(f"Invalid number of options. Question: {question}")

        if question["correct_answer"] not in ["A", "B", "C", "D", "TRUE", "FALSE"]:
            raise ValueError(f"Invalid correct answer. Question: {question}")
        print(question)
        return question

class NutritionQuiz:
    """Main class for NutritionQuiz functionality."""

    def __init__(self):
        """Initialize the NutritionQuiz application."""
        logger.info("Initializing NutritionQuiz application")
        self.google_ai = GroqHandler()
        self.google_ai.configure_api()

    def generate_quiz(self) -> List[Dict]:
        """
        Generate a nutrition quiz.

        Returns:
            List[Dict]: A list of dictionaries, each containing a question, options, correct answer, and explanation.
        """
        logger.info("Generating nutrition quiz")
        response = self.google_ai.get_groq_response()
        parsed_questions = QuizHandler.parse_quiz_response(response)
        print(parsed_questions)
        # Validate parsed questions
        valid_questions = []
        for q in parsed_questions:
            if all(key in q for key in ["question", "options", "correct_answer", "explanation"]) and len(q["options"]) in [2, 4]:
                valid_questions.append(q)
            else:
                logger.warning(f"Invalid question format: {q}")
        
        if not valid_questions:
            logger.error("No valid questions were generated. Raw response: " + response)
            raise ValueError("No valid questions were generated. Please try again.")
        
        return valid_questions

    def check_answer(self, question: Dict, user_answer: str) -> Dict:
        """
        Check the user's answer and provide feedback.

        Args:
            question (Dict): The question dictionary.
            user_answer (str): The user's answer (A, B, C, D, True, or False).

        Returns:
            Dict: A dictionary containing whether the answer is correct and the explanation.
        """
        is_correct = user_answer.lower() == question['correct_answer'].lower()
        return {
            "is_correct": is_correct,
            "correct_answer": question['correct_answer'],
            "explanation": question['explanation']
        }

# Example usage
if __name__ == "__main__":
    quiz = NutritionQuiz()
    try:
        questions = quiz.generate_quiz()
        for q in questions:
            print(q['question'])
            for i, option in enumerate(q['options']):
                print(f"{chr(65 + i)}. {option}")
            user_answer = input("Your answer: ").lower()
            result = quiz.check_answer(q, user_answer)
            print("Correct!" if result['is_correct'] else "Incorrect.")
            print(f"The correct answer is {result['correct_answer']}")
            print(f"Explanation: {result['explanation']}\n")
    except Exception as e:
        print(f"An error occurred: {e}")
        logger.error(f"Quiz generation failed: {e}")
