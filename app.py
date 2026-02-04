"""
Bharat Fact - Indian News Verifier (final)
Patched: render header/footer/article cards via streamlit.components.v1.html to avoid raw-code display.
Date: 2025-11-05 (final)
Author: Deepak (patched by assistant)
"""

import os
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from textwrap import dedent

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

import time
from requests.exceptions import RequestException, Timeout

import requests
from bs4 import BeautifulSoup

import hashlib
from pathlib import Path


# =========================
# ENHANCED CONFIG
# =========================

def get_api_key(service_name: str) -> str:
    """
    Safely get API keys from Streamlit secrets or environment variables.
    """
    key_name = f"{service_name}_API_KEY"

    # 1 Try Streamlit secrets
    try:
        return st.secrets[key_name]
    except Exception:
        pass

    # 2 Fallback to environment variable
    return os.getenv(key_name, "")

class EnhancedAppConfig:
    GEMINI_API_KEY = get_api_key("GEMINI")
    NEWSAPI_API_KEY = get_api_key("NEWSAPI")
    
    APP_TITLE = "Bharat Fact"
    VERSION = "3.0"
    AUTHOR_CREDIT = "Deepak"

    COLORS = {
        'primary': '#1E3A5F',
        'secondary': '#2C5282',
        'success': '#38A169',
        'warning': '#D69E2E',
        'danger': '#E53E3E',
        'info': '#3182CE',
        'background': '#F7FAFC',
        'text': '#2D3748',
        'text_light': '#718096'
    }

    TRUSTED_SOURCES = [
        "Times of India - https://timesofindia.indiatimes.com",
        "NDTV - https://www.ndtv.com",
        "The Hindu - https://www.thehindu.com",
        "Indian Express - https://indianexpress.com",
        "India Today - https://www.indiatoday.in",
        "Alt News - https://www.altnews.in",
        "Boom Live - https://www.boomlive.in",
        "The Quint WebQoof - https://www.thequint.com/news/webqoof"
    ]

# =========================
# PERSISTENT VERIFICATION CACHE
# =========================

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_FILE = CACHE_DIR / "verification_cache.json"

# =========================
# UTILITIES
# =========================

def safe_requests_get(
    url: str,
    headers: dict = None,
    timeout: int = 10,
    retries: int = 3,
    backoff_factor: float = 1.0,
):
    """
    Robust HTTP GET with retries and exponential backoff.
    Backoff pattern: 1s → 2s → 4s
    """
    headers = headers or {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}

    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)

            # Retry on server-side errors
            if resp.status_code >= 500:
                raise RequestException(f"Server error: {resp.status_code}")

            resp.raise_for_status()
            return resp

        except (RequestException, Timeout):
            if attempt == retries - 1:
                return None
            time.sleep(backoff_factor * (2 ** attempt))


def extract_first_json(text: str):
    """Attempt to find and parse the first JSON object/array in text."""
    if not text or not isinstance(text, str):
        return None
    m = re.search(r'(\[.*\]|\{.*\})', text, flags=re.DOTALL)
    if not m:
        return None
    candidate = m.group(1)
    for trim_end in range(len(candidate), 0, -1):
        try:
            part = candidate[:trim_end]
            parsed = json.loads(part)
            return parsed
        except Exception:
            continue
    try:
        return json.loads(candidate)
    except Exception:
        return None

def _safe_filename(s: str, maxlen: int = 50) -> str:
    if not s:
        return "fact_check"
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'\s+', '_', s).strip('_')
    return s[:maxlen] or "fact_check"

def _normalize_claim(text: str) -> str:
    """Normalize claim text for consistent hashing."""
    return re.sub(r'\s+', ' ', text.strip().lower())


def _claim_hash(text: str) -> str:
    """Generate SHA256 hash for a news claim."""
    normalized = _normalize_claim(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _load_verification_cache() -> Dict[str, Any]:
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_verification_cache(cache: Dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# =========================
# CACHED TOP-LEVEL FETCH HELPERS
# =========================

@st.cache_data(ttl=1800, show_spinner=False)
def cached_fetch_google_news_rss(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    results = []
    try:
        if not query or not query.strip():
            return results
        q = query.strip().replace(" ", "+")
        trusted_sites = [
            "ndtv.com", "thehindu.com", "indiatoday.in", "indiatimes.com",
            "indianexpress.com", "boomlive.in", "altnews.in", "thequint.com",
            "firstpost.com", "news18.com", "republicworld.com"
        ]
        site_part = "+OR+".join([f"site:{s}" for s in trusted_sites])
        rss_url = f"https://news.google.com/rss/search?q={q}+({site_part})&hl=en-IN&gl=IN&ceid=IN:en"
        resp = safe_requests_get(rss_url, timeout=10)
        if resp is None:
            return []
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")[:max_results]
        for item in items:
            title = item.title.text if item.title else ""
            link = item.link.text if item.link else ""
            pub = item.pubDate.text if item.pubDate else ""
            source = item.source.text if item.source else ""
            if title and link:
                results.append({
                    "title": title.strip(),
                    "link": link.strip(),
                    "published": pub,
                    "source": source,
                    "api": "Google News RSS"
                })
    except Exception:
        return []
    return results

@st.cache_data(ttl=1800, show_spinner=False)
def cached_fetch_newsapi(query: str, newsapi_key: str, max_results: int = 8) -> List[Dict[str, Any]]:
    results = []
    if not newsapi_key:
        return results
    try:
        if not query or not query.strip():
            return results
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': max_results,
            'apiKey': newsapi_key,
            'from': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        }
        headers = {"User-Agent": "BharatFact/3.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=12)
        if resp.status_code != 200:
            return []
        data = resp.json()
        articles = data.get('articles', [])[:max_results]
        for article in articles:
            if article.get('title') and article.get('url'):
                results.append({
                    "title": article['title'],
                    "link": article['url'],
                    "published": article.get('publishedAt', ''),
                    "source": article.get('source', {}).get('name', ''),
                    "api": "NewsAPI"
                })
    except Exception:
        return []
    return results

@st.cache_data(ttl=1800, show_spinner=False)
def cached_fetch_gdelt(query: str, max_results: int = 6) -> List[Dict[str, Any]]:
    results = []
    try:
        if not query or not query.strip():
            return results
        gdelt_url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            'query': f'{query} sourcecountry:IN',
            'mode': 'artlist',
            'format': 'json',
            'maxrecords': max_results
        }
        resp = requests.get(gdelt_url, params=params, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
        articles = data.get('articles', [])[:max_results]
        for article in articles:
            results.append({
                "title": article.get('title', ''),
                "link": article.get('url', ''),
                "published": article.get('seendate', ''),
                "source": article.get('domain', ''),
                "api": "GDELT"
            })
    except Exception:
        return []
    return results

# =========================
# ORIGINAL UI COMPONENTS (Keep the same interface, professional wording)
# =========================

class BeautifulUI:
    @staticmethod
    def setup_page_config():
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

# =========================
# ENHANCED LIVE NEWS FETCHER
# =========================

class LiveNewsFetcher:
    def __init__(self):
        self.newsapi_key = EnhancedAppConfig.NEWSAPI_API_KEY
    
    def fetch_google_news_rss(self, query: str, max_results: int = 8):
        return cached_fetch_google_news_rss(query, max_results=max_results)
    
    def fetch_newsapi(self, query: str, max_results: int = 8):
        return cached_fetch_newsapi(query, newsapi_key=self.newsapi_key, max_results=max_results)
    
    def fetch_gdelt(self, query: str, max_results: int = 6):
        return cached_fetch_gdelt(query, max_results=max_results)
    
    def fetch_all_news_sources(self, query: str, max_total: int = 15):
        if not query or not query.strip():
            return []
        with st.spinner("Searching live news sources..."):
            all_results = []
            google_results = []
            try:
                google_results = self.fetch_google_news_rss(query, max_results=8) or []
            except Exception:
                google_results = []
            all_results.extend(google_results)
            if self.newsapi_key:
                try:
                    newsapi_results = self.fetch_newsapi(query, max_results=6) or []
                    all_results.extend(newsapi_results)
                except Exception:
                    pass
            try:
                gdelt_results = self.fetch_gdelt(query, max_results=4) or []
                all_results.extend(gdelt_results)
            except Exception:
                pass

        # Deduplicate by link
        seen = set()
        unique = []
        for r in all_results:
            link = (r.get('link') or '').strip()
            if not link:
                continue
            if link not in seen:
                seen.add(link)
                unique.append(r)
        return unique[:max_total]

# =========================
# HYBRID NEWS VERIFIER
# =========================

class HybridNewsVerifier:
    def __init__(self):
        self.model = None
        self.is_ready = False
        self.initialization_error = None
        self.news_fetcher = LiveNewsFetcher()
        self._setup_gemini_ai()
    
    def _setup_gemini_ai(self):
        try:
            import google.generativeai as genai
        except Exception as e:
            self.initialization_error = f"Gemini SDK import failed: {e}"
            return

        api_key = EnhancedAppConfig.GEMINI_API_KEY
        if not api_key:
            self.initialization_error = "No GEMINI_API_KEY found"
            return

        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            self.initialization_error = f"Gemini configure failed: {e}"
            return

        known_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.5-mini', 'gemini-1.0']
        init_errors = []
        for model_name in known_models:
            try:
                model = genai.GenerativeModel(model_name)
                try:
                    gen = model.generate_content("Hello")
                    text = getattr(gen, 'text', None) or (gen.get('text') if isinstance(gen, dict) else None)
                    if text:
                        self.model = model
                        self.is_ready = True
                        return
                except Exception as e:
                    init_errors.append(f"{model_name}: {e}")
                    continue
            except Exception as e:
                init_errors.append(f"{model_name}: {e}")
                continue

        try:
            listed = []
            for m in genai.list_models():
                name = getattr(m, 'name', None) or (m.get('name') if isinstance(m, dict) else None)
                if name:
                    listed.append(name.split('/')[-1])
            for nm in listed:
                if nm in known_models:
                    continue
                try:
                    model = genai.GenerativeModel(nm)
                    gen = model.generate_content("Hello")
                    text = getattr(gen, 'text', None) or (gen.get('text') if isinstance(gen, dict) else None)
                    if text:
                        self.model = model
                        self.is_ready = True
                        return
                except Exception:
                    continue
        except Exception:
            pass

        self.initialization_error = "Could not initialize Gemini model. " + ("; ".join(init_errors[:6]) if init_errors else "")

    def verify_news(self, news_claim: str):
        if not self.is_ready:
            return self._create_error_response(self.initialization_error or "AI engine not ready")

        claim_key = _claim_hash(news_claim)
        cache = _load_verification_cache()

        # ✅ Return cached result if available
        if claim_key in cache:
            cached = cache[claim_key]
            cached["cached"] = True
            return cached

        # ❌ Not cached → full verification
        try:
            live_evidence = self.news_fetcher.fetch_all_news_sources(news_claim)
        except Exception:
            live_evidence = []

        prompt = self._create_hybrid_prompt(news_claim, live_evidence)

        try:
            gen = self.model.generate_content(prompt)
            ai_text = getattr(gen, "text", None) or (
                gen.get("text") if isinstance(gen, dict) else None
            )
            if not ai_text:
                return self._create_error_response("No response from AI")
        except Exception as e:
            return self._create_error_response(f"AI analysis failed: {e}")

        result = self._parse_hybrid_response(ai_text, live_evidence)

        # ✅ Save result to cache
        result["cached"] = False
        cache[claim_key] = result
        _save_verification_cache(cache)


        return result
    # @st.cache_data(show_spinner=False)
    def tag_evidence_support(self, news_claim: str, live_evidence: list):
        if not live_evidence:
            return {
                "items": [],
                "counts": {
                    "supportive": 0,
                    "contradictory": 0,
                    "irrelevant": 0
                }
            }

        try:
            import google.generativeai as genai
            model = self.model or genai.GenerativeModel("gemini-1.5-flash")
        except Exception:
            return {
                "items": [],
                "counts": {
                    "supportive": 0,
                    "contradictory": 0,
                    "irrelevant": 0
                }
            }

        headlines = []
        for i, article in enumerate(live_evidence, 1):
            headlines.append(f"{i}. {article.get('title','')}")

        prompt = f"""
Claim:
"{news_claim}"

Headlines:
{chr(10).join(headlines)}

Classify each headline as:
supportive, contradictory, or irrelevant.

Return STRICT JSON like:
[
  {{"index":1,"tag":"supportive","rationale":"short reason"}}
]
"""

        try:
            response = model.generate_content(prompt)
            raw = getattr(response, "text", "")
        except Exception:
            return {
                "items": [],
                "counts": {
                    "supportive": 0,
                    "contradictory": 0,
                    "irrelevant": 0
                }
            }

        data = extract_first_json(raw)

        counts = {
            "supportive": 0,
            "contradictory": 0,
            "irrelevant": 0
        }
        items = []

        if isinstance(data, list):
            for obj in data:
                tag = obj.get("tag", "irrelevant")
                if tag not in counts:
                    tag = "irrelevant"
                counts[tag] += 1
                items.append(obj)

        return {
            "items": items,
            "counts": counts
        }

    def _create_hybrid_prompt(self, news_claim: str, live_evidence: list):
        evidence_text = ""
        if live_evidence:
            evidence_text = "LIVE NEWS EVIDENCE FOUND:\n"
            for i, article in enumerate(live_evidence[:8], 1):
                evidence_text += f"{i}. {article.get('title','')}\n"
                if article.get('source'):
                    evidence_text += f"   Source: {article.get('source')}\n"
                if article.get('published'):
                    evidence_text += f"   Published: {article.get('published')}\n"
                evidence_text += f"   URL: {article.get('link')}\n\n"
        else:
            evidence_text = "LIVE NEWS EVIDENCE: No recent articles found from trusted sources.\n"
        
        return f"""
Bharat Fact - INDIAN NEWS FACT-CHECK ANALYSIS WITH LIVE EVIDENCE
========================================================

You are an expert Indian news fact-checker. Analyze the claim below using both your knowledge and the provided live news evidence from trusted sources.

NEWS CLAIM TO VERIFY:
\"\"\"{news_claim}\"\"\"


{evidence_text}

ANALYSIS INSTRUCTIONS:
1. First check if the live evidence supports or contradicts the claim
2. Consider the credibility of sources in the evidence
3. Look for consensus or disagreement among sources
4. Note if evidence is recent or outdated
5. Identify any missing context or conflicting reports

Please provide analysis in this EXACT format:

VERIFICATION_STATUS: [TRUE/FALSE/PARTIALLY_TRUE/MISLEADING/UNVERIFIED]
CONFIDENCE_SCORE: [0-100]

EVIDENCE_BASED_ANALYSIS:
[Analyze how the live evidence relates to the claim. Which sources support/contradict?]

CONTEXTUAL_ANALYSIS:
[Broader context about this topic in India]

CONSENSUS_LEVEL:
[High/Medium/Low - based on agreement among sources]

RED_FLAGS:
[Suspicious elements, missing evidence, or credibility concerns]

RECOMMENDATION:
[Final assessment and advice for readers]
"""

    def _parse_hybrid_response(self, ai_text: str, live_evidence: list):
        status = "UNVERIFIED"
        confidence = 50
        txt = ai_text.upper() if isinstance(ai_text, str) else ""
        
        status_patterns = [
            ("VERIFICATION_STATUS: TRUE", "TRUE"),
            ("VERIFICATION_STATUS: FALSE", "FALSE"), 
            ("VERIFICATION_STATUS: PARTIALLY_TRUE", "PARTIALLY_TRUE"),
            ("VERIFICATION_STATUS: MISLEADING", "MISLEADING"),
            ("VERIFICATION_STATUS: UNVERIFIED", "UNVERIFIED")
        ]
        
        for pattern, status_val in status_patterns:
            if pattern in txt:
                status = status_val
                break
        
        m = re.search(r'CONFIDENCE_SCORE:\s*([0-9]{1,3})', ai_text, flags=re.IGNORECASE) if isinstance(ai_text, str) else None
        if m:
            try:
                extracted = int(m.group(1))
                confidence = max(0, min(100, extracted))
            except Exception:
                pass
        
        if not live_evidence and confidence > 50:
            confidence = max(30, confidence - 20)
        
        return {
            "status": status,
            "confidence": confidence,
            "analysis": ai_text,
            "live_evidence": live_evidence,
            "evidence_count": len(live_evidence),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sources": EnhancedAppConfig.TRUSTED_SOURCES[:4],
            "success": True
        }
    
    def _create_error_response(self, msg: str):
        return {
            "status": "ERROR",
            "confidence": 0,
            "analysis": f"ERROR: {msg}",
            "live_evidence": [],
            "evidence_count": 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sources": [],
            "success": False
        }

# =========================
# ENHANCED RESULTS DISPLAY
# =========================

class EnhancedUI:
    @staticmethod
    def render_enhanced_results(result_data, query_text):
        if not result_data.get('success', False):
            st.error(result_data.get('analysis', 'Unknown error'))
            return
        
        primary = EnhancedAppConfig.COLORS["primary"]
        secondary = EnhancedAppConfig.COLORS["secondary"]
        text_light = EnhancedAppConfig.COLORS["text_light"]
        
        # Elegant results container - matching header style
        results_header_html = dedent(f"""
        <div style="
            max-width: 1200px;
            margin: 2.5rem auto 0 auto;
            padding: 3.5rem 4rem;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%);
            border-radius: 24px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15), 0 4px 12px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(226, 232, 240, 0.15);
            backdrop-filter: blur(20px);
            position: relative;
            overflow: hidden;
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
                    margin: 0 auto 2rem auto;
                    box-shadow: 0 2px 8px rgba(44, 82, 130, 0.4);
                "></div>
                
                <!-- Results Title Section -->
                <div style="text-align: center; margin-bottom: 2.5rem; padding-bottom: 2rem; border-bottom: 1px solid rgba(226, 232, 240, 0.12);">
                    <h2 style="
                        background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                        font-size: 3rem;
                        margin: 0;
                        font-weight: 700;
                        line-height: 1.1;
                        letter-spacing: -0.04em;
                    ">Verification Results</h2>
                </div>
            </div>
        </div>
        """).lstrip()
        
        components.html(results_header_html, height=200, scrolling=False)
        
        # Content wrapper with same max-width - using container
        with st.container():
            st.markdown('<div style="max-width: 1200px; margin: 0 auto; padding: 0 4rem 2rem 4rem;">', unsafe_allow_html=True)
        
        # Status badge with color
        status_config = {
            'TRUE': ('✓ Verified', EnhancedAppConfig.COLORS['success']),
            'FALSE': ('✗ False', EnhancedAppConfig.COLORS['danger']),
            'PARTIALLY_TRUE': ('⚠ Partially True', EnhancedAppConfig.COLORS['warning']),
            'MISLEADING': ('⚠ Misleading', '#D69E2E'),
            'UNVERIFIED': ('? Unverified', '#718096'),
            'ERROR': ('Error', '#4A5568')
        }
        
        status_label, status_color = status_config.get(
            result_data['status'], 
            ('Unverified', '#718096')
        )
        
        # Key metrics in elegant cards
        metrics_html = dedent(f"""
        <div style="
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            margin: 2rem 0;
        ">
            <div style="
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.4) 100%);
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid rgba(226, 232, 240, 0.1);
                text-align: center;
            ">
                <div style="color: #CBD5E0; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">Status</div>
                <div style="color: {status_color}; font-size: 1.8rem; font-weight: 700;">{status_label}</div>
            </div>
            <div style="
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.4) 100%);
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid rgba(226, 232, 240, 0.1);
                text-align: center;
            ">
                <div style="color: #CBD5E0; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">Confidence</div>
                <div style="color: {primary}; font-size: 1.8rem; font-weight: 700;">{result_data['confidence']}%</div>
            </div>
            <div style="
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.4) 100%);
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid rgba(226, 232, 240, 0.1);
                text-align: center;
            ">
                <div style="color: #CBD5E0; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">Evidence</div>
                <div style="color: {primary}; font-size: 1.8rem; font-weight: 700;">{result_data['evidence_count']} articles</div>
            </div>
            <div style="
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.4) 100%);
                padding: 1.5rem;
                border-radius: 12px;
                border: 1px solid rgba(226, 232, 240, 0.1);
                text-align: center;
            ">
                <div style="color: #CBD5E0; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem;">Time</div>
                <div style="color: {primary}; font-size: 1.4rem; font-weight: 700;">{result_data['timestamp'].split(' ')[1] if 'timestamp' in result_data else 'N/A'}</div>
            </div>
        </div>
        """).lstrip()
        st.markdown(metrics_html, unsafe_allow_html=True)
        
        st.markdown("")
        
        # Evidence status message
        if result_data['evidence_count'] == 0:
            st.info("ℹ Analysis based on AI knowledge only - no live evidence found")
        elif result_data['evidence_count'] < 3:
            st.info("ℹ Limited evidence available - consider additional verification")
        else:
            st.success(f"✓ Analyzed {result_data['evidence_count']} recent articles from trusted sources")
        
        st.markdown("")
        
        # Analysis section with elegant styling
        analysis_header_html = dedent(f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: flex-start;
            margin: 2rem 0 1.5rem 0;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(226, 232, 240, 0.12);
        ">
            <div style="
                width: 6px;
                height: 36px;
                background: linear-gradient(180deg, {primary} 0%, {secondary} 100%);
                border-radius: 4px;
                margin-right: 1.5rem;
                box-shadow: 0 4px 8px rgba(44, 82, 130, 0.3);
            "></div>
            <h3 style="
                color: #E2E8F0;
                font-size: 1.8rem;
                font-weight: 600;
                margin: 0;
                letter-spacing: -0.02em;
            ">Analysis</h3>
            <span style="
                color: {text_light};
                font-size: 0.9rem;
                margin-left: auto;
                opacity: 0.7;
            ">Analyzed at {result_data.get('timestamp', 'N/A')}</span>
        </div>
        """).lstrip()
        st.markdown(analysis_header_html, unsafe_allow_html=True)
        
        with st.expander("View detailed analysis", expanded=True):
            st.text_area(
                "AI Analysis:",
                value=result_data['analysis'],
                height=300,
                disabled=True,
                label_visibility="collapsed"
            )
        
        st.markdown("")
        
        # Evidence section with elegant styling
        evidence_header_html = dedent(f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: flex-start;
            margin: 2rem 0 1.5rem 0;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(226, 232, 240, 0.12);
        ">
            <div style="
                width: 6px;
                height: 36px;
                background: linear-gradient(180deg, {primary} 0%, {secondary} 100%);
                border-radius: 4px;
                margin-right: 1.5rem;
                box-shadow: 0 4px 8px rgba(44, 82, 130, 0.3);
            "></div>
            <h3 style="
                color: #E2E8F0;
                font-size: 1.8rem;
                font-weight: 600;
                margin: 0;
                letter-spacing: -0.02em;
            ">Evidence</h3>
        </div>
        """).lstrip()
        st.markdown(evidence_header_html, unsafe_allow_html=True)
        
        live_evidence = result_data.get('live_evidence', [])
        
        if not live_evidence:
            st.info("No direct online evidence found from trusted sources.")
        else:
            with st.spinner("Analyzing evidence alignment..."):
                verifier = st.session_state.get('hybrid_verifier')
                if verifier:
                    try:
                        tags_result = verifier.tag_evidence_support(query_text, live_evidence)
                    except Exception:
                        tags_result = {"items": [], "counts": {}}
                else:
                    tags_result = {"items": [], "counts": {}}
            
            if tags_result and tags_result.get('items'):
                counts = tags_result.get('counts', {})
                supportive = counts.get('supportive', 0)
                contradictory = counts.get('contradictory', 0)
                irrelevant = counts.get('irrelevant', 0)
                total = len(live_evidence)
                
                st.markdown("**Evidence Alignment**")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Supportive", supportive, delta=f"{(supportive/total)*100:.0f}%" if total > 0 else "0%")
                with col2:
                    st.metric("Contradictory", contradictory, delta=f"{(contradictory/total)*100:.0f}%" if total > 0 else "0%", delta_color="inverse")
                with col3:
                    st.metric("Irrelevant", irrelevant, delta=f"{(irrelevant/total)*100:.0f}%" if total > 0 else "0%")
                with col4:
                    consensus = "High" if supportive > contradictory * 2 else "Medium" if supportive > contradictory else "Low" if contradictory > supportive else "Mixed"
                    st.metric("Consensus", consensus)
                
                try:
                    import pandas as pd
                    import altair as alt
                    
                    chart_data = pd.DataFrame({
                        'Type': ['Supportive', 'Contradictory', 'Irrelevant'],
                        'Count': [supportive, contradictory, irrelevant]
                    })
                    
                    bar_chart = alt.Chart(chart_data).mark_bar().encode(
                        x=alt.X('Type:N', sort=None, title='Evidence Type', axis=alt.Axis(labelAngle=0)),
                        y=alt.Y('Count:Q', title='Number of Articles'),
                        color=alt.Color('Type:N', scale=alt.Scale(
                            domain=['Supportive', 'Contradictory', 'Irrelevant'],
                            range=[EnhancedAppConfig.COLORS['success'], EnhancedAppConfig.COLORS['danger'], '#718096']
                        ), legend=None),
                        tooltip=[alt.Tooltip('Type:N', title='Type'), alt.Tooltip('Count:Q', title='Count')]
                    ).properties(
                        height=250,
                        title="Evidence Alignment Distribution"
                    )
                    
                    st.altair_chart(bar_chart, use_container_width=True)
                    
                except Exception:
                    st.markdown("**Evidence Distribution:**")
                    if supportive > 0:
                        st.markdown(f"Supportive: {'█' * supportive} ({supportive})")
                    if contradictory > 0:
                        st.markdown(f"Contradictory: {'█' * contradictory} ({contradictory})")
                    if irrelevant > 0:
                        st.markdown(f"Irrelevant: {'█' * irrelevant} ({irrelevant})")
                
                with st.expander("View detailed evidence", expanded=False):
                    sorted_items = sorted(tags_result['items'], 
                                        key=lambda x: ['supportive', 'contradictory', 'irrelevant'].index(x['tag']))
                    
                    for item in sorted_items:
                        idx = item['index']
                        if 0 <= idx-1 < len(live_evidence):
                            article = live_evidence[idx-1]
                            
                            tag_config = {
                                'supportive': {'label': '✓ Supports', 'color': EnhancedAppConfig.COLORS['success']},
                                'contradictory': {'label': '✗ Contradicts', 'color': EnhancedAppConfig.COLORS['danger']},
                                'irrelevant': {'label': '○ Not Related', 'color': '#718096'}
                            }
                            
                            config = tag_config.get(item['tag'], tag_config['irrelevant'])
                            
                            card_html = dedent(f"""
                            <div style="
                                border-left: 3px solid {config['color']}; 
                                padding: 12px 16px; 
                                margin: 12px 0; 
                                background: #F7FAFC;
                                border-radius: 4px;
                            ">
                                <div style="margin-bottom: 8px;">
                                    <span style="
                                        color: {config['color']}; 
                                        font-weight: 600; 
                                        font-size: 13px;
                                    ">{config['label']}</span>
                                </div>
                                <div style="margin-bottom: 6px;">
                                    <a href="{article['link']}" target="_blank" style="
                                        font-size: 15px; 
                                        color: #2C5282; 
                                        text-decoration: none;
                                        font-weight: 500;
                                    ">{article['title']}</a>
                                </div>
                                <div style="font-size: 12px; color: #718096; margin-bottom: 8px;">
                                    {article.get('source', 'Unknown')} • {article.get('published', 'Unknown date')[:10] if article.get('published') else 'Unknown date'}
                                </div>
                                <div style="font-size: 13px; color: #4A5568; margin-top: 8px; padding-top: 8px; border-top: 1px solid #E2E8F0;">
                                    <strong>Rationale:</strong> {item['rationale']}
                                </div>
                            </div>
                            """).lstrip()

                            components.html(card_html, height=160, scrolling=False)
            else:
                st.markdown(f"**Found {len(live_evidence)} related article(s):**")
                for e in live_evidence:
                    pub = e.get('published', '')[:10] if e.get('published') else ''
                    source_info = f" • {e.get('source', '')}" if e.get('source') else ""
                    pub_info = f" • {pub}" if pub else ""
                    st.markdown(f"- [{e['title']}]({e['link']}){source_info}{pub_info}")

        st.markdown("")
        
        # Recommended Sources section with elegant styling
        sources_header_html = dedent(f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: flex-start;
            margin: 2rem 0 1.5rem 0;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(226, 232, 240, 0.12);
        ">
            <div style="
                width: 6px;
                height: 36px;
                background: linear-gradient(180deg, {primary} 0%, {secondary} 100%);
                border-radius: 4px;
                margin-right: 1.5rem;
                box-shadow: 0 4px 8px rgba(44, 82, 130, 0.3);
            "></div>
            <h3 style="
                color: #E2E8F0;
                font-size: 1.8rem;
                font-weight: 600;
                margin: 0;
                letter-spacing: -0.02em;
            ">Recommended Sources</h3>
        </div>
        """).lstrip()
        st.markdown(sources_header_html, unsafe_allow_html=True)
        st.markdown('<p style="color: #CBD5E0; margin-bottom: 1rem;">For additional verification, check these trusted sources:</p>', unsafe_allow_html=True)
        for s in EnhancedAppConfig.TRUSTED_SOURCES:
            st.markdown(f'<p style="color: #CBD5E0; margin: 0.5rem 0;">• {s}</p>', unsafe_allow_html=True)

        st.markdown("")
        EnhancedUI.render_download_section(result_data)

        if result_data.get("cached"):
            st.info("⚡ Result loaded from cache (no new API calls)")

        
        # Close the wrapper div
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_download_section(result_data):
        primary = EnhancedAppConfig.COLORS["primary"]
        secondary = EnhancedAppConfig.COLORS["secondary"]
        
        # Download section with elegant styling
        download_header_html = dedent(f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: flex-start;
            margin: 2rem 0 1.5rem 0;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(226, 232, 240, 0.12);
        ">
            <div style="
                width: 6px;
                height: 36px;
                background: linear-gradient(180deg, {primary} 0%, {secondary} 100%);
                border-radius: 4px;
                margin-right: 1.5rem;
                box-shadow: 0 4px 8px rgba(44, 82, 130, 0.3);
            "></div>
            <h3 style="
                color: #E2E8F0;
                font-size: 1.8rem;
                font-weight: 600;
                margin: 0;
                letter-spacing: -0.02em;
            ">Download Report</h3>
        </div>
        """).lstrip()
        st.markdown(download_header_html, unsafe_allow_html=True)
        def generate_pdf_report_bytes():
            from io import BytesIO
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
            story = []
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor(EnhancedAppConfig.COLORS['primary']), alignment=TA_CENTER)
            subtitle_style = ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor(EnhancedAppConfig.COLORS['secondary']), alignment=TA_CENTER)
            body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, alignment=TA_JUSTIFY, leading=14)

            story.append(Paragraph("Bharat Fact", title_style))
            story.append(Paragraph("AI-Powered Fact Checking Report", subtitle_style))
            story.append(Spacer(1, 0.2*inch))

            news_claim = st.session_state.get('last_query', 'Not available')
            story.append(Paragraph("<b>News Claim Verified:</b>", styles['Heading3']))
            story.append(Paragraph(f'"{news_claim}"', body_style))
            story.append(Spacer(1, 0.1*inch))

            verification_data = [
                ['Verification Status', result_data['status']],
                ['Confidence Level', f"{result_data['confidence']}%"],
                ['Evidence Analyzed', f"{result_data['evidence_count']} articles"],
                ['Analysis Date', result_data['timestamp']]
            ]
            table = Table(verification_data, colWidths=[2.5*inch, 3.5*inch])
            table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#ECF0F1')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(table)
            story.append(Spacer(1, 0.2*inch))

            analysis_text = result_data.get('analysis', '')
            analysis_chunks = [c.strip() for c in analysis_text.split('\n') if c.strip()]
            for para in analysis_chunks[:40]:
                story.append(Paragraph(para, body_style))
                story.append(Spacer(1, 0.05*inch))

            if result_data.get('live_evidence'):
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("<b>Live Evidence Sources Analyzed:</b>", styles['Heading3']))
                for evidence in result_data['live_evidence'][:5]:
                    story.append(Paragraph(f"• {evidence.get('title','')[:120]}...", body_style))
                    story.append(Spacer(1, 0.02*inch))

            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>Recommended Sources</b>", styles['Heading3']))
            for s in EnhancedAppConfig.TRUSTED_SOURCES:
                story.append(Paragraph(f"• {s}", body_style))

            disclaimer = Paragraph("<i>This is an AI-assisted analysis with live evidence. Always verify important news with multiple reliable sources.</i>", ParagraphStyle('disclaimer', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER))
            story.append(Spacer(1, 0.2*inch))
            story.append(disclaimer)
            story.append(Spacer(1, 0.1*inch))
            story.append(
                Paragraph(
                    f"<i>Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>",
                    ParagraphStyle(
                        'meta',
                        parent=styles['Normal'],
                        fontSize=9,
                        alignment=TA_CENTER
                    )
                )
            )


            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()

        try:
            pdf_bytes = generate_pdf_report_bytes()
            news_claim = st.session_state.get('last_query', '')
            if news_claim:
                clean_name = _safe_filename(news_claim)[:50]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"bharatfact_{clean_name}_{timestamp}.pdf"
            else:
                filename = f"bharatfact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            st.download_button("Download PDF Report", data=pdf_bytes, file_name=filename, mime="application/pdf")
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
            st.info("Install reportlab: pip install reportlab")

# =========================
# MAIN APPLICATION
# =========================

def main():
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
