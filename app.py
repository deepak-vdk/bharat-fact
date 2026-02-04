"""
🇮🇳 INDIAN NEWS VERIFIER - HYBRID (AI + Live News Feeds)
Date: 2025-11-05
Author: deepak
Notes:
- Uses multiple real-time news APIs + Gemini analysis
- Combines live evidence with AI reasoning
"""

import os
import re
import time
from datetime import datetime, timedelta
import json

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import requests
from bs4 import BeautifulSoup

# =========================
# ENHANCED CONFIG
# =========================

def get_api_key(service_name):
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
    
    APP_TITLE = "🇮🇳 Indian News Verifier - Hybrid AI"
    VERSION = "3.0"

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
# ORIGINAL UI COMPONENTS (Keep the same interface)
# =========================

class BeautifulUI:
    @staticmethod
    def setup_page_config():
        st.set_page_config(page_title=EnhancedAppConfig.APP_TITLE, page_icon="🇮🇳", layout="wide", initial_sidebar_state="collapsed")
        hide_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """
        st.markdown(hide_style, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        st.markdown(f"""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: {EnhancedAppConfig.COLORS["primary"]}; font-size: 3rem; margin-bottom: 0;'>🇮🇳 Indian News Verifier</h1>
            <p style='color: {EnhancedAppConfig.COLORS["secondary"]}; font-size: 1.1rem; margin-top: 0;'>AI-Powered Fake News Detection • Advanced AI Technology</p>
            <hr style='width: 50%; margin: 1.5rem auto; border: 2px solid {EnhancedAppConfig.COLORS["primary"]};'>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_sidebar():
        with st.sidebar:
            st.markdown("### 🛠️ How It Works")
            st.markdown("1. Enter news\n2. AI analysis\n3. Cross-check with trusted sources")
            st.markdown("---")
            st.markdown("### ⚠️ Note")
            st.markdown("This tool assists verification. Always cross-check important claims.")
            st.markdown("---")
            st.markdown(f"**Version {EnhancedAppConfig.VERSION}** 🇮🇳")

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
            resp = requests.get(url, headers=headers, timeout=8)
            resp.raise_for_status()
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

        st.markdown("### 📝 Enter News to Verify")
        input_method = st.radio("Choose input method:", ["✏️ Type/Paste Text", "🔗 News URL"], horizontal=True)
        news_text = ""

        if input_method == "✏️ Type/Paste Text":
            key = f"news_input_{st.session_state.clear_counter}"
            news_text = st.text_area("Enter the news claim:", height=150, placeholder="Example: PM Modi announced new education policy today...", key=key)
        else:
            url_key = f"url_input_{st.session_state.clear_counter}"
            url = st.text_input("Enter news article URL:", placeholder="https://example.com/news-article", key=url_key)
            if url:
                if BeautifulUI.valid_url(url):
                    with st.spinner("🔎 Extracting text from URL..."):
                        text = BeautifulUI.extract_text_from_url(url)
                        if text:
                            news_text = text
                            st.success("✅ Text extracted successfully (truncated).")
                            st.text_area("Extracted text (truncated):", value=news_text, height=120, disabled=True)
                        else:
                            st.error("❌ Could not extract usable text from the URL. Try another source or paste text manually.")
                else:
                    st.warning("⚠️ Please enter a valid URL starting with http:// or https://")

        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            verify_clicked = st.button("🔍 Verify News", type="primary")
        with col2:
            example_clicked = st.button("🧪 Try Example")
        with col3:
            clear_clicked = st.button("🔄 Clear")
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
    
    @st.cache_data(ttl=1800)  # 30 minutes cache
    def fetch_google_news_rss(_self, query: str, max_results: int = 8):
        """Enhanced Google News RSS with better Indian sources."""
        if not query or not query.strip():
            return []
        
        q = query.strip().replace(" ", "+")
        trusted_sites = [
            "ndtv.com", "thehindu.com", "indiatoday.in", "indiatimes.com",
            "indianexpress.com", "boomlive.in", "altnews.in", "thequint.com",
            "firstpost.com", "news18.com", "republicworld.com"
        ]
        
        site_part = "+OR+".join([f"site:{s}" for s in trusted_sites])
        rss_url = f"https://news.google.com/rss/search?q={q}+({site_part})&hl=en-IN&gl=IN&ceid=IN:en"
        
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(rss_url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")[:max_results]
            
            results = []
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
            return results
        except Exception as e:
            st.error(f"Google News RSS error: {e}")
            return []
    
    @st.cache_data(ttl=1800)
    def fetch_newsapi(_self, query: str, max_results: int = 8):
        """Fetch from NewsAPI with Indian focus."""
        if not _self.newsapi_key:
            return []
        
        try:
            # NewsAPI with Indian sources and language filter
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': max_results,
                'apiKey': _self.newsapi_key,
                'from': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')  # Last 30 days
            }
            
            headers = {"User-Agent": "IndianNewsVerifier/3.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            articles = data.get('articles', [])[:max_results]
            
            results = []
            for article in articles:
                if article.get('title') and article.get('url'):
                    results.append({
                        "title": article['title'],
                        "link": article['url'],
                        "published": article.get('publishedAt', ''),
                        "source": article.get('source', {}).get('name', ''),
                        "api": "NewsAPI"
                    })
            return results
        except Exception as e:
            st.error(f"NewsAPI error: {e}")
            return []
    
    @st.cache_data(ttl=1800)
    def fetch_gdelt(_self, query: str, max_results: int = 6):
        """Fetch from GDELT Project for global coverage including Indian media."""
        try:
            # GDELT GKG API - simplified version
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
            
            results = []
            for article in articles:
                results.append({
                    "title": article.get('title', ''),
                    "link": article.get('url', ''),
                    "published": article.get('seendate', ''),
                    "source": article.get('domain', ''),
                    "api": "GDELT"
                })
            return results
        except Exception:
            # GDELT can be unstable, fail gracefully
            return []
    
    def fetch_all_news_sources(self, query: str, max_total: int = 15):
        """Fetch from all available news sources in parallel."""
        if not query.strip():
            return []
        
        # Run all fetchers
        with st.spinner("🔍 Searching live news sources..."):
            all_results = []
            
            # Google News RSS (most reliable for Indian sources)
            google_results = self.fetch_google_news_rss(query, max_results=8)
            all_results.extend(google_results)
            
            # NewsAPI (if available)
            if self.newsapi_key:
                newsapi_results = self.fetch_newsapi(query, max_results=6)
                all_results.extend(newsapi_results)
            
            # GDELT (global coverage)
            gdelt_results = self.fetch_gdelt(query, max_results=4)
            all_results.extend(gdelt_results)
        
        # Remove duplicates by URL
        seen_urls = set()
        unique_results = []
        
        for result in all_results:
            url = result['link']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results[:max_total]

# =========================
# ENHANCED HYBRID VERIFIER
# =========================

class HybridNewsVerifier:
    def __init__(self):
        self.model = None
        self.is_ready = False
        self.initialization_error = None
        self.news_fetcher = LiveNewsFetcher()
        self._setup_gemini_ai()
    
    def _setup_gemini_ai(self):
        """Configure Gemini AI client."""
        try:
            import google.generativeai as genai
            
            api_key = EnhancedAppConfig.GEMINI_API_KEY
            if not api_key:
                self.initialization_error = "No GEMINI_API_KEY found"
                return
            
            genai.configure(api_key=api_key)
            
            # Build a robust candidate list: known-stable + discovered
            known_models = ['gemini-1.5-flash', 'gemini-1.5-pro']
            discovered = []
            try:
                for m in genai.list_models():
                    supported = getattr(m, 'supported_generation_methods', []) or []
                    if 'generateContent' in supported:
                        name = getattr(m, 'name', '')
                        if name:
                            discovered.append(name.split('/')[-1])
            except Exception:
                pass

            # Deduplicate while preserving order
            model_names = []
            seen = set()
            for nm in known_models + discovered:
                if nm and nm not in seen:
                    seen.add(nm)
                    model_names.append(nm)

            init_errors = []
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    # Quick test
                    response = self.model.generate_content("hello")
                    if getattr(response, 'text', None):
                        self.is_ready = True
                        break
                except Exception as e:
                    init_errors.append(f"{model_name}: {e}")
                    continue
            
            if not self.is_ready:
                detail = "\n".join(init_errors[:6]) if 'init_errors' in locals() and init_errors else "No models responded"
                self.initialization_error = f"Could not initialize Gemini model. Details: {detail}"
                
        except Exception as e:
            self.initialization_error = f"Gemini setup failed: {str(e)}"
    
    def verify_news(self, news_claim: str):
        """Hybrid verification: Fetch live evidence + AI analysis."""
        if not self.is_ready:
            return self._create_error_response(self.initialization_error or "AI engine not ready")
        
        # Step 1: Fetch live news evidence
        live_evidence = self.news_fetcher.fetch_all_news_sources(news_claim)
        
        # Step 2: Create enhanced prompt with live evidence
        prompt = self._create_hybrid_prompt(news_claim, live_evidence)
        
        try:
            import google.generativeai as genai
        except Exception:
            return self._create_error_response("AI client library not available")
        
        try:
            # Generate analysis
            response = self.model.generate_content(prompt)
            ai_text = response.text
            
            if not ai_text:
                return self._create_error_response("No response from AI")
            
            # Parse response with live evidence context
            return self._parse_hybrid_response(ai_text, live_evidence)
            
        except Exception as e:
            return self._create_error_response(f"AI analysis failed: {e}")

    @st.cache_data(show_spinner=False)
    def tag_evidence_support(_self, news_claim: str, live_evidence: list):
        """Classify each evidence headline as supportive, contradictory, or irrelevant using Gemini.
        Returns list of {index, title, tag, rationale} and counts per tag.
        """
        try:
            import google.generativeai as genai
        except Exception:
            return {"items": [], "counts": {"supportive": 0, "contradictory": 0, "irrelevant": 0}}

        if not live_evidence:
            return {"items": [], "counts": {"supportive": 0, "contradictory": 0, "irrelevant": 0}}

        # Prepare headline list with indices
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

        try:
            model = _self.model if _self and getattr(_self, 'model', None) else None
            if not model:
                # Fallback: create a short-lived model client
                model = genai.GenerativeModel('gemini-1.5-flash')
            gen = model.generate_content(instruction)
            raw = getattr(gen, 'text', '') or ''
        except Exception:
            return {"items": [], "counts": {"supportive": 0, "contradictory": 0, "irrelevant": 0}}

        # Parse JSON safely
        items = []
        try:
            data = json.loads(raw)
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
        except Exception:
            items = []

        counts = {"supportive": 0, "contradictory": 0, "irrelevant": 0}
        for it in items:
            counts[it['tag']] = counts.get(it['tag'], 0) + 1

        return {"items": items, "counts": counts}
    
    def _create_hybrid_prompt(self, news_claim: str, live_evidence: list):
        """Create prompt that includes live news evidence."""
        
        # Format live evidence for the prompt
        evidence_text = ""
        if live_evidence:
            evidence_text = "LIVE NEWS EVIDENCE FOUND:\n"
            for i, article in enumerate(live_evidence[:8], 1):  # Top 8 articles
                evidence_text += f"{i}. {article['title']}\n"
                if article.get('source'):
                    evidence_text += f"   Source: {article['source']}\n"
                if article.get('published'):
                    evidence_text += f"   Published: {article['published']}\n"
                evidence_text += f"   URL: {article['link']}\n\n"
        else:
            evidence_text = "LIVE NEWS EVIDENCE: No recent articles found from trusted sources.\n"
        
        return f"""
🇮🇳 INDIAN NEWS FACT-CHECK ANALYSIS WITH LIVE EVIDENCE
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
        """Parse AI response with live evidence context."""
        status = "UNVERIFIED"
        confidence = 50
        txt = ai_text.upper()
        
        # Status extraction
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
        
        # Confidence extraction
        m = re.search(r'CONFIDENCE_SCORE:\s*([0-9]{1,3})', ai_text, flags=re.IGNORECASE)
        if m:
            try:
                extracted = int(m.group(1))
                confidence = max(0, min(100, extracted))
            except Exception:
                pass
        
        # Adjust confidence based on evidence availability
        if not live_evidence and confidence > 50:
            confidence = max(30, confidence - 20)  # Penalize when no evidence
        
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
            "analysis": f"❌ {msg}",
            "live_evidence": [],
            "evidence_count": 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sources": [],
            "success": False
        }

# =========================
# ENHANCED RESULTS DISPLAY (Keep UI same but with enhanced data)
# =========================

class EnhancedUI:
    @staticmethod
    def render_enhanced_results(result_data, query_text):
        if not result_data.get('success', False):
            st.error(result_data.get('analysis', 'Unknown error'))
            return
        
        st.markdown("### 📊 Verification Results")
        
        # Status with evidence context - using same UI as before
        status_icons = {
            'TRUE': ('🟢', EnhancedAppConfig.COLORS['success']),
            'FALSE': ('🔴', EnhancedAppConfig.COLORS['danger']),
            'PARTIALLY_TRUE': ('🟡', EnhancedAppConfig.COLORS['warning']),
            'MISLEADING': ('🟠', '#E67E22'),
            'UNVERIFIED': ('⚪', '#95A5A6'),
            'ERROR': ('⚫', '#34495E')
        }
        
        icon, color = status_icons.get(result_data['status'], ('⚪', '#95A5A6'))
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Verification Status", f"{icon} {result_data['status']}")
        with col2:
            st.metric("🎯 Confidence Level", f"{result_data['confidence']}%")
        with col3:
            st.metric("📰 Evidence Found", f"{result_data['evidence_count']} articles")
        with col4:
            st.metric("⏰ Analysis Time", result_data['timestamp'].split(' ')[1])
        
        # Confidence indicator with evidence context
        if result_data['evidence_count'] == 0:
            st.warning("⚠️ No live evidence found - analysis based on AI knowledge only")
        elif result_data['evidence_count'] < 3:
            st.info("ℹ️ Limited evidence available - consider additional verification")
        else:
            st.success(f"✅ Analyzed {result_data['evidence_count']} recent articles")
        
        st.markdown("### 🧠 Detailed AI Analysis")
        with st.expander("📖 Click to view full analysis", expanded=True):
            st.text_area("AI Analysis:", value=result_data['analysis'], height=400, disabled=True)
        
        # Enhanced Evidence Section with Classification
        st.markdown("### 📰 Evidence Analysis")
        live_evidence = result_data.get('live_evidence', [])
        
        if not live_evidence:
            st.info("No direct online evidence found from trusted sources.")
        else:
            # Get evidence classification
            with st.spinner("🔍 Analyzing evidence alignment..."):
                verifier = st.session_state.get('hybrid_verifier')
                if verifier:
                    tags_result = verifier.tag_evidence_support(query_text, live_evidence)
                else:
                    tags_result = {"items": [], "counts": {}}
            
            # Show evidence alignment summary
            if tags_result and tags_result.get('items'):
                counts = tags_result.get('counts', {})
                supportive = counts.get('supportive', 0)
                contradictory = counts.get('contradictory', 0)
                irrelevant = counts.get('irrelevant', 0)
                total = len(live_evidence)
                
                st.markdown("#### 🧩 Evidence Alignment with Claim")
                
                # Create columns for the summary
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
                
                # Visualize with a bar chart (fallback if altair not available)
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
                    
                except ImportError:
                    # Simple text-based visualization as fallback
                    st.markdown("**Evidence Distribution:**")
                    if supportive > 0:
                        st.markdown(f"🟢 Supportive: {'█' * supportive} ({supportive})")
                    if contradictory > 0:
                        st.markdown(f"🔴 Contradictory: {'█' * contradictory} ({contradictory})")
                    if irrelevant > 0:
                        st.markdown(f"⚪ Irrelevant: {'█' * irrelevant} ({irrelevant})")
                
                # Detailed evidence breakdown
                with st.expander("📋 View Detailed Evidence Analysis", expanded=True):
                    st.markdown("#### 🔍 Article-by-Article Analysis")
                    
                    # Sort by relevance (supportive first, then contradictory, then irrelevant)
                    sorted_items = sorted(tags_result['items'], 
                                        key=lambda x: ['supportive', 'contradictory', 'irrelevant'].index(x['tag']))
                    
                    for item in sorted_items:
                        idx = item['index']
                        if 0 <= idx-1 < len(live_evidence):
                            article = live_evidence[idx-1]
                            
                            # Color coding and icons
                            tag_config = {
                                'supportive': {'icon': '🟢', 'color': '#2ECC71', 'label': 'Supports Claim'},
                                'contradictory': {'icon': '🔴', 'color': '#E74C3C', 'label': 'Contradicts Claim'},
                                'irrelevant': {'icon': '⚪', 'color': '#95A5A6', 'label': 'Not Directly Related'}
                            }
                            
                            config = tag_config.get(item['tag'], tag_config['irrelevant'])
                            
                            # Create a nice card for each article
                            st.markdown(f"""
                            <div style="border-left: 4px solid {config['color']}; padding: 10px; margin: 10px 0; background: #f8f9fa;">
                                <div style="display: flex; justify-content: between; align-items: start;">
                                    <div style="flex: 1;">
                                        <strong>{config['icon']} {config['label']}</strong><br/>
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
                            """, unsafe_allow_html=True)
            else:
                # Fallback to simple list if classification failed
                st.success(f"✅ Found {len(live_evidence)} related article(s):")
                for e in live_evidence:
                    pub = e.get('published', '')
                    source_info = f" ({e.get('source', '')})" if e.get('source') else ""
                    if pub:
                        st.markdown(f"- 📰 [{e['title']}]({e['link']}){source_info}  \n  <small>{pub}</small>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"- 📰 [{e['title']}]({e['link']}){source_info}")

        st.markdown("### 📰 Recommended Sources for Cross-checking")
        for s in EnhancedAppConfig.TRUSTED_SOURCES:
            st.markdown(f"- {s}")

        EnhancedUI.render_download_section(result_data)
    
    @staticmethod
    def render_download_section(result_data):
        st.markdown("### 📥 Download Verification Report")
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

            story.append(Paragraph("🇮🇳 Indian News Verifier", title_style))
            story.append(Paragraph("AI-Powered Fake News Detection Report", subtitle_style))
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

            # Add evidence summary
            if result_data.get('live_evidence'):
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph("<b>Live Evidence Sources Analyzed:</b>", styles['Heading3']))
                for evidence in result_data['live_evidence'][:5]:  # Top 5
                    story.append(Paragraph(f"• {evidence['title'][:80]}...", body_style))
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
                clean_name = re.sub(r'[^\w\s-]', '', news_claim)[:50].strip()
                clean_name = re.sub(r'\s+', '_', clean_name)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"fact_check_{clean_name}_{timestamp}.pdf"
            else:
                filename = f"fact_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            st.download_button("📄 Download PDF Report", data=pdf_bytes, file_name=filename, mime="application/pdf")
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
            st.info("Install reportlab: pip install reportlab")

# =========================
# MAIN APPLICATION
# =========================

def main():
    BeautifulUI.setup_page_config()
    
    # Initialize hybrid verifier
    if 'hybrid_verifier' not in st.session_state:
        st.session_state['hybrid_verifier'] = HybridNewsVerifier()
    
    BeautifulUI.render_header()
    BeautifulUI.render_sidebar()
    
    # Use the original verification form (same UI)
    news_text, verify_clicked, is_example = BeautifulUI.render_verification_form()
    
    if (verify_clicked and news_text.strip()) or is_example:
        st.session_state['last_query'] = news_text
        verifier = st.session_state['hybrid_verifier']
        
        with st.spinner("🔍 Hybrid verification in progress: Searching live sources + AI analysis..."):
            result = verifier.verify_news(news_text)
        
        EnhancedUI.render_enhanced_results(result, news_text)
    
    elif verify_clicked and not news_text.strip():
        st.warning("⚠️ Please enter some news text to verify!")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #7F8C8D; padding: 2rem 0;'>
        <p><strong>🇮🇳 Indian News Verifier</strong> • Fighting Misinformation with AI</p>
        <p><em>Made with ❤️ by deepak</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()