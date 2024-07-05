import streamlit as st
from typing import List, Dict
from utils.mcq_quiz import NutritionQuiz
from utils.logger import logger

def show():
    """
    Display the Nutrition Quiz page of the NutriAI application.

    This function handles the layout and functionality of the quiz page,
    including question display, user input, and result presentation.
    """
    st.title("Nutrition Quiz with NutriAI")
    st.subheader("Test your food knowledge and learn fun facts! 🍎🧠")

    # Initialize session state variables
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = None
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False

    # Generate new quiz if not already generated
    if st.session_state.quiz_questions is None:
        with st.spinner("Preparing a delicious quiz for you..."):
            try:
                quiz = NutritionQuiz()
                st.session_state.quiz_questions = quiz.generate_quiz()
            except Exception as e:
                logger.error(f"Error generating quiz: {e}")
                st.error("An error occurred while generating the quiz. Please try again later.")
                st.stop()

    # Display quiz questions
    for i, question in enumerate(st.session_state.quiz_questions):
        st.subheader(f"Question {i+1}")
        st.write(question['question'])
        
        options = question['options']
        option_labels = ['A', 'B', 'C', 'D'][:len(options)]
        
        answer = st.radio(
            "Select your answer:",
            options=option_labels,
            format_func=lambda x: f"{x}. {options[option_labels.index(x)]}",
            key=f"q{i}",
            index=None,
            disabled=st.session_state.quiz_submitted
        )
        
        if answer:
            st.session_state.user_answers[i] = answer

        st.write("---")

    # Submit button
    if st.button("Submit Quiz", disabled=st.session_state.quiz_submitted):
        if len(st.session_state.user_answers) < len(st.session_state.quiz_questions):
            st.warning("Please answer all questions before submitting.")
        else:
            st.session_state.quiz_submitted = True
            st.experimental_rerun()

    if st.session_state.quiz_submitted:
        display_quiz_results(st.session_state.quiz_questions, st.session_state.user_answers)

    # Reset button
    if st.session_state.quiz_submitted:
        if st.button("Take Another Quiz"):
            reset_quiz()
            st.experimental_rerun()

def display_quiz_results(questions: List[Dict], user_answers: Dict):
    """
    Display the results of the quiz after submission.

    Args:
        questions (List[Dict]): List of question dictionaries.
        user_answers (Dict): Dictionary of user answers.
    """
    st.subheader("📊 Quiz Results")
    
    quiz = NutritionQuiz()
    correct_count = 0
    
    for i, question in enumerate(questions):
        user_answer = user_answers.get(i)
        correct_answer = question['correct_answer']

        # Debug prints
        # st.write(f"Debug: user_answer = {user_answer}, correct_answer = {correct_answer}")

        result = quiz.check_answer(question, user_answer)
        
        if result['is_correct']:
            correct_count += 1
            st.success(f"Question {i+1}: Correct!")
        else:
            st.error(f"Question {i+1}: Incorrect")
        
        # Check if user_answer and correct_answer are single characters
        if len(user_answer) != 1 or len(correct_answer) != 1:
            st.error(f"Error: user_answer or correct_answer is not a single character. user_answer: {user_answer}, correct_answer: {correct_answer}")
            return

        user_option = question['options'][ord(user_answer) - ord('A')]
        correct_option = question['options'][ord(correct_answer) - ord('A')]
        
        st.write(f"Your answer: {user_answer}. {user_option}")
        st.write(f"Correct answer: {correct_answer}. {correct_option}")
        st.info(f"Explanation: {question['explanation']}")
        st.write("---")

    score_percentage = (correct_count / len(questions)) * 100
    st.subheader(f"Your Score: {correct_count}/{len(questions)} ({score_percentage:.1f}%)")
    
    if score_percentage == 100:
        st.balloons()
        st.success("Perfect score! You're a nutrition expert! 🏆")
    elif score_percentage >= 80:
        st.success("Great job! You really know your food facts! 🌟")
    elif score_percentage >= 60:
        st.info("Good effort! Keep learning about nutrition! 📚")
    else:
        st.warning("There's room for improvement. Time to brush up on your nutrition knowledge! 💪")

def reset_quiz():
    """Reset the quiz state for a new attempt."""
    st.session_state.quiz_questions = None
    st.session_state.user_answers = {}
    st.session_state.quiz_submitted = False

if __name__ == "__main__":
    show()