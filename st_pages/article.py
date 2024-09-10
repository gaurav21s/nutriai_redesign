import streamlit as st
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
    including article listing, search functionality, and detailed view.
    """
    logger.info("Started Article page")
    st.markdown("""
    <h1 style='text-align: center; color: #15627D;'>NutriAI Articles</h1>
    <h3 style='text-align: center; color: #333;'>Explore our collection of nutritional articles 📚</h3>
    """, unsafe_allow_html=True)

    # Load articles from YAML file
    articles = load_articles()

    # Search functionality
    search_query = st.text_input("Search articles", "")
    filtered_articles = [
        article for article in articles
        if search_query.lower() in article["title"].lower() or search_query.lower() in article["summary"].lower()
    ]

    # Display article list
    for i, article in enumerate(filtered_articles):
        with st.container():
            st.markdown(f"### {article['title']}")
            st.markdown(f"<p style='color: #666;'>{article['summary']}</p>", unsafe_allow_html=True)
            if st.button(f"Read More", key=f"button_{i}", type="primary"):
                show_article_popup(article)

        st.markdown("---")

    if not filtered_articles:
        st.info("No articles found matching your search.")
        
    st.markdown("""
        <div style='position: fixed; left: 10px; bottom: 10px;'>
            <img src="https://raw.githubusercontent.com/gaurav21s/nutriai/v2/style/nutriai-favicon-color.png" alt="NutriAI Logo" width="50" height="50">
        </div>
        <div style='position: fixed; right: 10px; bottom: 10px;'>
            <a href="https://github.com/gaurav21s" target="_blank">@gaurav21s</a>
        </div>
    """, unsafe_allow_html=True)

def show_article_popup(article):
    """
    Display the full details of an article in a popup.
    
    Parameters:
    -----------
    article : dict
        A dictionary containing the article details (title, content).
    """
    popup = st.empty()
    with popup.container():
        st.markdown(f"<h2 style='text-align: center; color: #15627D;'>{article['title']}</h2>", unsafe_allow_html=True)
        st.markdown(article['content'])
        if st.button("Close"):
            popup.empty()