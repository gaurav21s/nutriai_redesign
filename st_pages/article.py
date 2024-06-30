import streamlit as st
from streamlit_modal import Modal
import yaml
import os
from utils.logger import logger

def load_articles():
    """
    Load articles from the YAML file.
    
    Returns:
    --------
    list
        A list of dictionaries, each containing article details.
    """
    yaml_path = os.path.join('yaml', 'article.yml')
    
    if not os.path.exists(yaml_path):
        st.error(f"Article file not found at {yaml_path}. Please check the file path.")
        return []

    try:
        with open(yaml_path, 'r') as file:
            articles = yaml.safe_load(file)
        return articles
    except Exception as e:
        st.error(f"Error loading articles: {str(e)}")
        return []

def show():
    """
    Display the Articles page of the application.

    This function handles the layout and functionality of the articles page,
    including article listing and detailed view.
    """
    logger.info("Started Article page")
    st.title("NutriAI Articles")
    st.subheader("Explore our collection of nutritional articles 📚")

    # Load articles from YAML file
    articles = load_articles()

    # Display article list
    for i, article in enumerate(articles):
        st.subheader(article["title"])
        st.write(article["summary"])
        if st.button(f"Read More", key=f"button_{i}"):
            show_article_details(article)

    st.write("More articles coming soon ....")

def show_article_details(article):
    """
    Display the full details of an article in a modal popup.
    article : dict
        A dictionary containing the article details (title, content).
    """
    modal = Modal(f"Article: {article['title']}", key=f"modal_{article['title']}")
    with modal.container():
        st.markdown(f"<div style='max-height: 20vh; overflow-y: auto;'>", unsafe_allow_html=True)
        st.markdown(f"### {article['title']}")
        st.markdown(article['content'])
        st.markdown("</div>", unsafe_allow_html=True)
