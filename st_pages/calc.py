import streamlit as st

def show():
    st.title('NutriAI Calculator')
    st.subheader("Calculate your BMI and maintenance Calorie")

    mode = st.radio('Choose a mode', ('BMI', 'Calorie Calculator'))

    if mode == 'BMI':
        weight = st.number_input('Enter your weight (in kg)', format='%f')
        height = st.number_input('Enter your height (in cm)', format='%f')

        if st.button('Calculate BMI'):
            if not weight or not height:
                st.error('Please fill in all the fields.')
            else:
                bmi = calculate_bmi(weight, height)

                st.subheader(f'Your BMI is: {bmi:.1f}')

                if bmi < 18.5:
                    st.warning('You are underweight.')
                elif 18.5 <= bmi < 24.9:
                    st.success('You are at a healthy weight.')
                elif 25.0 <= bmi < 29.9:
                    st.warning('You are overweight.')
                else:
                    st.error('You are obese.')

    elif mode == 'Calorie Calculator':
        gender = st.selectbox('Select your gender', ('Male', 'Female'))

        weight = st.number_input('Enter your weight (in kg)', format='%f')
        height = st.number_input('Enter your height (in cm)', format='%f')
        age = st.number_input('Enter your age', format='%f')

        activity_levels = {
            1.2: 'Sedentary (little or no exercise)',
            1.375: 'Lightly active (light exercise/sports 1-3 days/week)',
            1.55: 'Moderately active (moderate exercise/sports 3-5 days/week)',
            1.725: 'Very active (hard exercise/sports 6-7 days a week)',
            1.9: 'Extra active (very hard exercise/sports & physical job or 2x training)'
        }

        activity_level = st.selectbox('Select your activity level', activity_levels.keys(), format_func=lambda x: activity_levels[x])

        if st.button('Calculate Calories'):
            if not weight or not height or not age or not activity_level:
                st.error('Please fill in all the fields.')
            else:
                calories = calculate_calories(gender, weight, height, age, activity_level)

                st.info(f'You need to consume approximately {calories:.0f} calories per day.')

                st.warning('If you want to lose weight, consume less than this amount.')
                st.success('If you want to gain weight, consume more than this amount.')

def calculate_bmi(weight, height):
    bmi = weight / ((height / 100) ** 2)
    return bmi

def calculate_calories(gender, weight, height, age, activity_level):
    if gender == 'Male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age)
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    calories = bmr * activity_level
    return calories

if __name__ == '__main__':
    show()
