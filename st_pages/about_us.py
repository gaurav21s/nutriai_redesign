"""
About Us page module for NutriAI.

This module handles the display of the About Us page content,
which is loaded from an HTML template, and includes interactive elements.
"""

import streamlit as st
from utils.logger import logger

def show():
    """
    Display the About Us page of the NutriAI application.

    This function loads the content from an HTML template, displays it
    using Streamlit's markdown functionality, and provides interactive elements.
    """
    logger.info("Started About Us Page")
    
    # Modern header with custom CSS
    st.markdown("""
    <style>
    .big-font {
        font-size:50px !important;
        color: #15627D;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
    }
    .subheader {
        font-size: 24px;
        color: #333;
        text-align: center;
        margin-bottom: 40px;
    }
    .content {
        background-color: #f0f2f6;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <h1 style='text-align: center; color: #15627D;'>About NutriAI</h1>
        <h3 style='text-align: center; color: #333;'>Empowering Your Nutritional Journey</h3>
        """, unsafe_allow_html=True)
    
    # Read and display the content of about_us.html
    with open('templates/about_us.html', 'r') as file:
        about_us_content = file.read()
    
    st.markdown(f'<div class="content">{about_us_content}</div>', unsafe_allow_html=True)

    # Interactive contact section
    st.markdown("## Get in Touch", unsafe_allow_html=True)
    st.markdown("#### Contact Us")
    st.markdown("📧 Email: gaurav21js@gmail.com")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Want to Discuss?")
        if st.button("📞 Schedule a Call"):
            st.info("Our team will contact you shortly to schedule a call.")
    with col2:
        st.markdown("#### Join Our Community")
        if st.button("🤝 Collaborate with Us"):
            st.success("Thank you for your interest! We'll reach out with collaboration opportunities.")

    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888;'>Made with ❤️ by Gaurav Shrivastav | © 2023 NutriAI</p>",
        unsafe_allow_html=True
    )
    
    st.markdown("""
        <div style='position: fixed; left: 10px; bottom: 10px;'>
            <img src="https://raw.githubusercontent.com/gaurav21s/nutriai/v2/style/nutriai-favicon-color.png" alt="NutriAI Logo" width="50" height="50">
        </div>
        <div style='position: fixed; right: 10px; bottom: 10px;'>
            <a href="https://github.com/gaurav21s" target="_blank">@gaurav21s</a>
        </div>
    """, unsafe_allow_html=True)
