"""
Bharat Fact - Indian News Verifier (Refactored)
Modular architecture with separated concerns:
- ui: layout, forms, results
- core: verification logic, prompts
- data: news fetching, APIs
- utils: caching, helpers
"""

from textwrap import dedent

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

from ui.layout import BeautifulUI
from ui.results import EnhancedUI
from core.verifier import HybridNewsVerifier


def main():
    """Main application entry point."""
    BeautifulUI.setup_page_config()
    
    if 'hybrid_verifier' not in st.session_state:
        st.session_state['hybrid_verifier'] = HybridNewsVerifier()
    
    BeautifulUI.render_header()
    BeautifulUI.render_sidebar()
    
    news_text, verify_clicked, is_example = BeautifulUI.render_verification_form()
    
    if (verify_clicked and news_text.strip()) or is_example:
        st.session_state['last_query'] = news_text
        verifier = st.session_state['hybrid_verifier']
        
        with st.spinner("Hybrid verification in progress: Searching live sources + AI analysis..."):
            result = verifier.verify_news(news_text)
        
        EnhancedUI.render_enhanced_results(result, news_text)
    
    elif verify_clicked and not news_text.strip():
        st.warning("Please enter some news text to verify.")
    
    # Clean footer
    st.markdown("---")
    footer_html = dedent(f"""
    <div style='
        text-align: center; 
        color: #718096; 
        padding: 2rem 0 1rem 0; 
        font-size: 0.9rem;
    '>
        <p style='margin: 0;'><strong>Bharat Fact</strong> • AI-Powered News Verification</p>
    </div>
    """).lstrip()
    components.html(footer_html, height=70, scrolling=False)


if __name__ == "__main__":
    main()
