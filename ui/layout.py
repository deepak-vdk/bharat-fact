"""Layout components: header, sidebar, and forms."""

import re
from textwrap import dedent

import streamlit as st
import streamlit.components.v1 as components
from bs4 import BeautifulSoup

from utils.config import EnhancedAppConfig
from utils.helpers import safe_requests_get


class BeautifulUI:
    """UI components for layout and forms."""
    
    @staticmethod
    def setup_page_config():
        """Setup Streamlit page configuration and custom CSS."""
        try:
            st.set_page_config(
                page_title=EnhancedAppConfig.APP_TITLE, 
                page_icon="", 
                layout="wide", 
                initial_sidebar_state="collapsed"
            )
        except Exception:
            pass
        
        # Professional, clean styling
        custom_css = dedent("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main container styling */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 1400px;
            padding-left: 3rem;
            padding-right: 3rem;
        }
        
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
        
        /* Text styling - adaptive colors */
        h1, h2, h3 {
            color: #E2E8F0;
            font-weight: 600;
        }
        
        /* Ensure readable text on dark background */
        .stMarkdown, p, label, div {
            color: #CBD5E0;
        }
        
        /* Button styling - enhanced */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 0.5rem 1.5rem;
            font-size: 1rem;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        /* Primary button special styling */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #2C5282 0%, #1E3A5F 100%);
            border: none;
        }
        
        /* Input styling - enhanced */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 2px solid rgba(226, 232, 240, 0.5);
            transition: all 0.3s ease;
            background-color: transparent;
            font-size: 0.95rem;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #2C5282;
            box-shadow: 0 0 0 3px rgba(44, 82, 130, 0.1);
            outline: none;
        }
        
        /* Radio button styling */
        .stRadio > div {
            background-color: transparent;
            padding: 14px 16px;
            border-radius: 8px;
            border: 2px solid rgba(226, 232, 240, 0.5);
            transition: all 0.3s ease;
        }
        
        .stRadio > div:hover {
            border-color: rgba(203, 213, 224, 0.7);
            background-color: rgba(247, 250, 252, 0.3);
        }
        
        /* Label styling */
        label {
            font-weight: 600;
            color: #2D3748;
            font-size: 0.95rem;
        }
        
        /* Metric cards */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
        }
        
        /* Spacing */
        .element-container {
            margin-bottom: 1rem;
        }
        
        /* Card-like container for form */
        .form-container {
            background: transparent;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06);
            border: 1px solid rgba(226, 232, 240, 0.3);
        }
        
        /* Make main background adaptive */
        .stApp {
            background: var(--background-color, #0E1117);
        }
        
        /* Ensure text is readable on dark background */
        .main h1, .main h2, .main h3 {
            color: #E2E8F0;
        }
        
        p, label, .stMarkdown {
            color: #CBD5E0;
        }
        </style>
        """).lstrip()
        st.markdown(custom_css, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        """Render the application header."""
        primary = EnhancedAppConfig.COLORS["primary"]
        secondary = EnhancedAppConfig.COLORS["secondary"]
        text_light = EnhancedAppConfig.COLORS["text_light"]

        html = dedent(f"""
        <div style="
            max-width: 1200px;
            margin: 0 auto 2rem auto;
            padding: 3.5rem 4rem 3rem 4rem;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%);
            border-radius: 24px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15), 0 4px 12px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(226, 232, 240, 0.15);
            backdrop-filter: blur(20px);
            position: relative;
            overflow: visible;
        ">
            <!-- Subtle background pattern -->
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: radial-gradient(circle at 20% 50%, rgba(44, 82, 130, 0.1) 0%, transparent 50%),
                            radial-gradient(circle at 80% 80%, rgba(30, 58, 95, 0.1) 0%, transparent 50%);
                pointer-events: none;
            "></div>
            
            <!-- Content wrapper -->
            <div style="position: relative; z-index: 1;">
                <!-- Top accent line -->
                <div style="
                    width: 100px;
                    height: 5px;
                    background: linear-gradient(90deg, {primary} 0%, {secondary} 100%);
                    border-radius: 3px;
                    margin: 0 auto 2.5rem auto;
                    box-shadow: 0 2px 8px rgba(44, 82, 130, 0.4);
                "></div>
                
                <!-- Header Section -->
                <div style="text-align: center; padding-bottom: 0.5rem;">
                    <h1 style="
                        background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                        font-size: 3.8rem;
                        margin: 0 0 1rem 0;
                        font-weight: 800;
                        line-height: 1.1;
                        letter-spacing: -0.06em;
                    ">{EnhancedAppConfig.APP_TITLE}</h1>

                    <p style="
                        color: {text_light};
                        font-size: 1.3rem;
                        margin: 0;
                        font-weight: 400;
                        letter-spacing: 0.03em;
                        opacity: 0.85;
                    ">AI-Powered News Verification Platform</p>
                </div>
            </div>
        </div>
        """).lstrip()

        components.html(html, height=280, scrolling=False)

    @staticmethod
    def render_sidebar():
        """Render the sidebar with instructions."""
        with st.sidebar:
            st.markdown("### How It Works")
            st.markdown("""
            1. **Enter** news claim or URL
            2. **Analyze** with AI verification
            3. **Review** evidence and results
            """)
            st.markdown("---")
            st.markdown("### Important")
            st.markdown("This tool provides AI-assisted analysis. Always verify important claims with multiple trusted sources.")
            st.markdown("---")
            st.caption(f"Version {EnhancedAppConfig.VERSION}")

    @staticmethod
    def valid_url(url: str) -> bool:
        """Check if a URL is valid."""
        return bool(re.match(r'^https?://', url))

    @staticmethod
    @st.cache_data(show_spinner=False)
    def extract_text_from_url(url: str, max_chars=2000) -> str:
        """Extract text from URL; use newspaper3k if available, otherwise BeautifulSoup fallback."""
        try:
            from newspaper import Article
            a = Article(url)
            a.download()
            a.parse()
            text = a.text or ""
            if text:
                return text.strip()[:max_chars]
        except Exception:
            pass

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}
            resp = safe_requests_get(url, headers=headers, timeout=8)
            if not resp:
                return ""
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                return ""
            soup = BeautifulSoup(resp.content, 'html.parser')
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            paragraphs = soup.find_all('p')
            extracted = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            if not extracted:
                meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
                if meta and meta.get('content'):
                    extracted = meta.get('content').strip()
            return extracted[:max_chars].strip()
        except Exception:
            return ""

    @staticmethod
    def render_verification_form():
        """Render the verification form and return user input."""
        if 'clear_counter' not in st.session_state:
            st.session_state.clear_counter = 0

        primary = EnhancedAppConfig.COLORS["primary"]
        secondary = EnhancedAppConfig.COLORS["secondary"]
        
        # Form content wrapper - aligned with header container
        form_wrapper = dedent(f"""
        <div style="
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 4rem;
        ">
        """).lstrip()
        st.markdown(form_wrapper, unsafe_allow_html=True)
        
        # Form content - now aligned with header
        # Select Input Method section with elegant styling
        input_method_header = dedent(f"""
            <div style="
                display: flex;
                align-items: center;
                margin-bottom: 1rem;
                margin-top: 0.5rem;
            ">
                <div style="
                    width: 5px;
                    height: 28px;
                    background: linear-gradient(180deg, {primary} 0%, {secondary} 100%);
                    border-radius: 3px;
                    margin-right: 1rem;
                    box-shadow: 0 2px 6px rgba(44, 82, 130, 0.3);
                "></div>
                <strong style="color: #E2E8F0; font-size: 1.2rem; font-weight: 600;">Select Input Method</strong>
            </div>
            """).lstrip()
        st.markdown(input_method_header, unsafe_allow_html=True)
        input_method = st.radio(
            "",
            ["Text", "URL"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        news_text = ""
        
        if input_method == "Text":
            key = f"news_input_{st.session_state.clear_counter}"
            news_claim_header = dedent(f"""
            <div style="
                display: flex;
                align-items: center;
                margin-bottom: 0.8rem;
                margin-top: 1rem;
            ">
                <div style="
                    width: 5px;
                    height: 28px;
                    background: linear-gradient(180deg, {primary} 0%, {secondary} 100%);
                    border-radius: 3px;
                    margin-right: 1rem;
                    box-shadow: 0 2px 6px rgba(44, 82, 130, 0.3);
                "></div>
                <strong style="color: #E2E8F0; font-size: 1.2rem; font-weight: 600;">Enter News Claim</strong>
            </div>
            """).lstrip()
            st.markdown(news_claim_header, unsafe_allow_html=True)
            news_text = st.text_area(
                "",
                height=160,
                placeholder="Paste the news claim or article text here for verification...",
                key=key,
                label_visibility="collapsed"
            )
        else:
            url_key = f"url_input_{st.session_state.clear_counter}"
            url_header = dedent(f"""
            <div style="
                display: flex;
                align-items: center;
                margin-bottom: 0.8rem;
                margin-top: 1rem;
            ">
                <div style="
                    width: 5px;
                    height: 28px;
                    background: linear-gradient(180deg, {primary} 0%, {secondary} 100%);
                    border-radius: 3px;
                    margin-right: 1rem;
                    box-shadow: 0 2px 6px rgba(44, 82, 130, 0.3);
                "></div>
                <strong style="color: #E2E8F0; font-size: 1.2rem; font-weight: 600;">Enter Article URL</strong>
            </div>
            """).lstrip()
            st.markdown(url_header, unsafe_allow_html=True)
            url = st.text_input(
                "",
                placeholder="https://example.com/news-article",
                key=url_key,
                label_visibility="collapsed"
            )
            if url:
                if BeautifulUI.valid_url(url):
                    with st.spinner("Extracting content..."):
                        text = BeautifulUI.extract_text_from_url(url)
                        if text:
                            news_text = text
                            st.success("✓ Content extracted")
                            st.text_area(
                                "Extracted text:",
                                value=news_text,
                                height=100,
                                disabled=True
                            )
                        else:
                            st.error("Unable to extract text. Please try another URL or paste text directly.")
                else:
                    st.warning("Please enter a valid URL (http:// or https://)")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Action buttons with better styling - centered
        col1, col2, col3, col4, col5 = st.columns([1, 1.5, 1.5, 1.5, 1])
        with col1:
            st.write("")  # Left spacer
        with col2:
            verify_clicked = st.button("🔍 Verify News", type="primary", use_container_width=True)
        with col3:
            example_clicked = st.button("📋 Try Example", use_container_width=True)
        with col4:
            clear_clicked = st.button("🗑️ Clear", use_container_width=True)
        with col5:
            st.write("")  # Right spacer
            if clear_clicked:
                st.session_state.clear_counter += 1
                for k in ["last_query"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()
        
        # Close the form wrapper
        st.markdown("</div>", unsafe_allow_html=True)

        if example_clicked:
            return "PM Modi is the current Prime Minister of India", verify_clicked, True

        return news_text or "", verify_clicked, False

