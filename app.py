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

import requests
from bs4 import BeautifulSoup

# =========================
# ENHANCED CONFIG
# =========================

def get_api_key(service_name: str) -> str:
    """Get API keys from Streamlit secrets or environment."""
    try:
        if isinstance(st.secrets, dict) and f"{service_name}_API_KEY" in st.secrets:
            return st.secrets[f"{service_name}_API_KEY"]
    except Exception:
        pass
    return os.getenv(f"{service_name}_API_KEY", "")

class EnhancedAppConfig:
    GEMINI_API_KEY = get_api_key("GEMINI")
    NEWSAPI_API_KEY = get_api_key("NEWSAPI")
    
    APP_TITLE = "Bharat Fact"
    VERSION = "3.0"
    AUTHOR_CREDIT = "Deepak"

    COLORS = {
        'primary': '#FF6B35',
        'secondary': '#004E89',
        'success': '#2ECC71',
        'warning': '#F39C12',
        'danger': '#E74C3C',
        'info': '#3498DB'
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
# UTILITIES
# =========================

def safe_requests_get(url: str, headers: dict = None, timeout: int = 10):
    """Simple wrapper with basic exception handling for requests.get"""
    headers = headers or {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp
    except Exception:
        return None

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
        # no emoji in page icon
        try:
            st.set_page_config(page_title=EnhancedAppConfig.APP_TITLE, page_icon="", layout="wide", initial_sidebar_state="collapsed")
        except Exception:
            # ignore if already set
            pass
        hide_style = dedent("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """).lstrip()
        st.markdown(hide_style, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        # Centered, compact and professional header rendered via components.html
        primary = EnhancedAppConfig.COLORS["primary"]
        secondary = EnhancedAppConfig.COLORS["secondary"]
        author = EnhancedAppConfig.AUTHOR_CREDIT

        html = dedent(f"""
        <div style="
            max-width: 900px;
            margin: 12px auto 18px auto;
            text-align: center;
            padding: 6px 16px;
        ">
            <h1 style="
                color: {primary};
                font-size: 2.2rem;
                margin: 0;
                font-weight: 700;
                line-height: 1.1;
                letter-spacing: -0.5px;
            ">{EnhancedAppConfig.APP_TITLE}</h1>

            <p style="
                color: {secondary};
                font-size: 1rem;
                margin: 8px 0 4px 0;
            ">AI-powered fact checking and verification</p>

            <p style="
                color: #7F8C8D;
                font-size: 0.85rem;
                margin: 4px 0 10px 0;
            ">Author: {author}</p>

            <hr style="
                border: none;
                height: 2px;
                background: {primary};
                margin-top: 8px;
                opacity: 0.12;
            " />
        </div>
        """).lstrip()

        # Use components.html to ensure raw HTML is injected (avoids markdown interpreting it)
        components.html(html, height=140, scrolling=False)

    @staticmethod
    def render_sidebar():
        with st.sidebar:
            st.markdown("### How It Works")
            st.markdown("1. Enter the news claim or article URL")
            st.markdown("2. AI-assisted analysis")
            st.markdown("3. Cross-check with trusted sources")
            st.markdown("---")
            st.markdown("### Note")
            st.markdown("This tool assists verification. Always cross-check important claims.")
            st.markdown("---")
            st.markdown(f"**Version {EnhancedAppConfig.VERSION}**")

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

        st.markdown("### Enter News to Verify")
        input_method = st.radio("Choose input method:", ["Type/Paste Text", "News URL"], horizontal=True)
        news_text = ""

        if input_method == "Type/Paste Text":
            key = f"news_input_{st.session_state.clear_counter}"
            news_text = st.text_area("Enter the news claim:", height=150, placeholder="Example: The government announced a new education policy today...", key=key)
        else:
            url_key = f"url_input_{st.session_state.clear_counter}"
            url = st.text_input("Enter news article URL:", placeholder="https://example.com/news-article", key=url_key)
            if url:
                if BeautifulUI.valid_url(url):
                    with st.spinner("Extracting text from URL..."):
                        text = BeautifulUI.extract_text_from_url(url)
                        if text:
                            news_text = text
                            st.success("Text extracted successfully (truncated).")
                            st.text_area("Extracted text (truncated):", value=news_text, height=120, disabled=True)
                        else:
                            st.error("Could not extract usable text from the URL. Try another source or paste text manually.")
                else:
                    st.warning("Please enter a valid URL starting with http:// or https://")

        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            verify_clicked = st.button("Verify News", type="primary")
        with col2:
            example_clicked = st.button("Try Example")
        with col3:
            clear_clicked = st.button("Clear")
            if clear_clicked:
                st.session_state.clear_counter += 1
                for k in ["last_query"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.experimental_rerun()

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

        live_evidence = []
        try:
            live_evidence = self.news_fetcher.fetch_all_news_sources(news_claim)
        except Exception:
            live_evidence = []

        prompt = self._create_hybrid_prompt(news_claim, live_evidence)

        try:
            gen = self.model.generate_content(prompt)
            ai_text = getattr(gen, 'text', None) or (gen.get('text') if isinstance(gen, dict) else None)
            if not ai_text:
                return self._create_error_response("No response from AI")
        except Exception as e:
            return self._create_error_response(f"AI analysis failed: {e}")

        return self._parse_hybrid_response(ai_text, live_evidence)

    @st.cache_data(show_spinner=False)
    def tag_evidence_support(_self, news_claim: str, live_evidence: list):
        try:
            import google.generativeai as genai
        except Exception:
            return {"items": [], "counts": {"supportive": 0, "contradictory": 0, "irrelevant": 0}}

        if not live_evidence:
            return {"items": [], "counts": {"supportive": 0, "contradictory": 0, "irrelevant": 0}}

        lines = []
        for idx, art in enumerate(live_evidence, 1):
            title = art.get('title', '').strip()
            src = art.get('source', '')
            title_line = f"{idx}. {title}"
            if src:
                title_line += f" (Source: {src})"
            lines.append(title_line)

        headlines_block = "\n".join(lines)

        instruction = f"""
You will classify news headlines relative to the CLAIM.

CLAIM:
"{news_claim}"

HEADLINES:
{headlines_block}

For each headline, decide:
- supportive: directly supports the claim
- contradictory: directly contradicts the claim
- irrelevant: not directly related or insufficient to judge

Return STRICT JSON (array) with objects: {{"index": <int>, "tag": "supportive|contradictory|irrelevant", "rationale": "short reason"}}. No extra text.
"""

        model = _self.model if _self and getattr(_self, 'model', None) else None
        try:
            if not model:
                model = genai.GenerativeModel('gemini-1.5-flash')
            gen = model.generate_content(instruction)
            raw = getattr(gen, 'text', '') or (gen.get('text') if isinstance(gen, dict) else '')
        except Exception:
            return {"items": [], "counts": {"supportive": 0, "contradictory": 0, "irrelevant": 0}}

        data = extract_first_json(raw)
        items = []
        if isinstance(data, list):
            for obj in data:
                try:
                    idx = int(obj.get('index'))
                    tag = str(obj.get('tag', '')).strip().lower()
                    rationale = str(obj.get('rationale', '')).strip()
                    if tag not in ("supportive", "contradictory", "irrelevant"):
                        tag = "irrelevant"
                    title = live_evidence[idx-1]['title'] if 1 <= idx <= len(live_evidence) else ''
                    items.append({"index": idx, "title": title, "tag": tag, "rationale": rationale})
                except Exception:
                    continue

        counts = {"supportive": 0, "contradictory": 0, "irrelevant": 0}
        for it in items:
            counts[it['tag']] = counts.get(it['tag'], 0) + 1

        return {"items": items, "counts": counts}

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
        
        st.markdown("### Verification Results")
        
        status_icons = {
            'TRUE': ('TRUE', EnhancedAppConfig.COLORS['success']),
            'FALSE': ('FALSE', EnhancedAppConfig.COLORS['danger']),
            'PARTIALLY_TRUE': ('PARTIALLY_TRUE', EnhancedAppConfig.COLORS['warning']),
            'MISLEADING': ('MISLEADING', '#E67E22'),
            'UNVERIFIED': ('UNVERIFIED', '#95A5A6'),
            'ERROR': ('ERROR', '#34495E')
        }
        
        icon, color = status_icons.get(result_data['status'], ('UNVERIFIED', '#95A5A6'))
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Verification Status", f"{icon}")
        with col2:
            st.metric("Confidence Level", f"{result_data['confidence']}%")
        with col3:
            st.metric("Evidence Found", f"{result_data['evidence_count']} articles")
        with col4:
            st.metric("Analysis Time", result_data['timestamp'].split(' ')[1])
        
        if result_data['evidence_count'] == 0:
            st.warning("No live evidence found - analysis based on AI knowledge only")
        elif result_data['evidence_count'] < 3:
            st.info("Limited evidence available - consider additional verification")
        else:
            st.success(f"Analyzed {result_data['evidence_count']} recent articles")
        
        st.markdown("### Detailed AI Analysis")
        with st.expander("Click to view full analysis", expanded=True):
            st.text_area("AI Analysis:", value=result_data['analysis'], height=400, disabled=True)
        
        st.markdown("### Evidence Analysis")
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
                
                st.markdown("#### Evidence Alignment with Claim")
                
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
                        'Alignment': ['Supportive', 'Contradictory', 'Irrelevant'],
                        'Count': [supportive, contradictory, irrelevant],
                        'Color': ['#2ECC71', '#E74C3C', '#95A5A6']
                    })
                    
                    bar_chart = alt.Chart(chart_data).mark_bar().encode(
                        x=alt.X('Alignment:N', sort=None),
                        y=alt.Y('Count:Q'),
                        color=alt.Color('Alignment:N', scale=alt.Scale(
                            domain=['Supportive', 'Contradictory', 'Irrelevant'],
                            range=['#2ECC71', '#E74C3C', '#95A5A6']
                        ), legend=None),
                        tooltip=['Alignment', 'Count']
                    ).properties(height=200, title="Evidence Alignment Distribution")
                    
                    st.altair_chart(bar_chart, use_container_width=True)
                    
                except Exception:
                    st.markdown("**Evidence Distribution:**")
                    if supportive > 0:
                        st.markdown(f"Supportive: {'█' * supportive} ({supportive})")
                    if contradictory > 0:
                        st.markdown(f"Contradictory: {'█' * contradictory} ({contradictory})")
                    if irrelevant > 0:
                        st.markdown(f"Irrelevant: {'█' * irrelevant} ({irrelevant})")
                
                with st.expander("View Detailed Evidence Analysis", expanded=True):
                    st.markdown("#### Article-by-Article Analysis")
                    
                    sorted_items = sorted(tags_result['items'], 
                                        key=lambda x: ['supportive', 'contradictory', 'irrelevant'].index(x['tag']))
                    
                    for item in sorted_items:
                        idx = item['index']
                        if 0 <= idx-1 < len(live_evidence):
                            article = live_evidence[idx-1]
                            
                            tag_config = {
                                'supportive': {'label': 'Supports Claim', 'color': '#2ECC71'},
                                'contradictory': {'label': 'Contradicts Claim', 'color': '#E74C3C'},
                                'irrelevant': {'label': 'Not Directly Related', 'color': '#95A5A6'}
                            }
                            
                            config = tag_config.get(item['tag'], tag_config['irrelevant'])
                            
                            card_html = dedent(f"""
                            <div style="border-left: 4px solid {config['color']}; padding: 10px; margin: 10px 0; background: #f8f9fa;">
                                <div style="display: flex; justify-content: space-between; align-items: start;">
                                    <div style="flex: 1;">
                                        <strong>{config['label']}</strong><br/>
                                        <a href="{article['link']}" target="_blank" style="font-size: 14px; color: #0066cc;">{article['title']}</a><br/>
                                        <small style="color: #666;">
                                            Source: {article.get('source', 'Unknown')} | 
                                            Published: {article.get('published', 'Unknown date')}
                                        </small>
                                    </div>
                                </div>
                                <div style="margin-top: 8px; font-size: 13px; color: #555;">
                                    <strong>AI Rationale:</strong> {item['rationale']}
                                </div>
                            </div>
                            """).lstrip()

                            # render card via components.html (height adjusted to approximate content)
                            components.html(card_html, height=140, scrolling=False)
            else:
                st.success(f"Found {len(live_evidence)} related article(s):")
                for e in live_evidence:
                    pub = e.get('published', '')
                    source_info = f" ({e.get('source', '')})" if e.get('source') else ""
                    if pub:
                        st.markdown(f"- [{e['title']}]({e['link']}){source_info}  \n  <small>{pub}</small>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"- [{e['title']}]({e['link']}){source_info}")

        st.markdown("### Recommended Sources for Cross-checking")
        for s in EnhancedAppConfig.TRUSTED_SOURCES:
            st.markdown(f"- {s}")

        EnhancedUI.render_download_section(result_data)
    
    @staticmethod
    def render_download_section(result_data):
        st.markdown("### Download Verification Report")
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
            story.append(Paragraph(f"<i>Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>", ParagraphStyle('meta', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER)))

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
    
    # footer rendered via components.html to avoid markdown code rendering
    footer_html = dedent(f"""
    <div style='text-align: center; color: #7F8C8D; padding: 8px 0 12px 0; font-size: 0.9rem;'>
        <p><strong>Bharat Fact</strong> • Fighting Misinformation with AI</p>
    </div>
    """).lstrip()
    st.markdown("---")
    components.html(footer_html, height=60, scrolling=False)

if __name__ == "__main__":
    main()
