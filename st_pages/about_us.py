"""
About Us page module for NutriAI.

This module handles the display of the About Us page content,
which is loaded from an HTML template, and includes a Contact Us button.
"""

import streamlit as st
import webbrowser

def show():
    """
    Display the About Us page of the NutriAI application.

    This function loads the content from an HTML template, displays it
    using Streamlit's markdown functionality, and provides a Contact Us button.
    """
    st.title("About NutriAI")
    
    # Read and display the content of about_us.html
    with open('templates/about_us.html', 'r') as file:
        about_us_content = file.read()
    
    st.markdown(about_us_content, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # Create a Contact Us button
    if st.button("Contact Us"):
        email = "gaurav21js@gmail.com"
        mailto_link = f"mailto:{email}?subject=Inquiry%20about%20NutriAI"
        
        # Open the default email client
        webbrowser.open(mailto_link)

    st.success("Contact us if you want to help or collab with us in this amazing project!!")