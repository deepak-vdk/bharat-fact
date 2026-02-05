"""News fetching functionality from various APIs."""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

import streamlit as st
import requests
from bs4 import BeautifulSoup

from utils.config import EnhancedAppConfig
from utils.helpers import safe_requests_get


@st.cache_data(ttl=1800, show_spinner=False)
def cached_fetch_google_news_rss(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """Fetch news from Google News RSS feed."""
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
    except Exception as e:
        st.warning(f"Google News RSS fetch failed: {e}")
        return []
    return results


@st.cache_data(ttl=1800, show_spinner=False)
def cached_fetch_newsapi(query: str, newsapi_key: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """Fetch news from NewsAPI."""
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
            # Log error details for debugging
            if resp.status_code == 401:
                st.warning("NewsAPI: Invalid API key")
            elif resp.status_code == 429:
                st.warning("NewsAPI: Rate limit exceeded")
            else:
                st.warning(f"NewsAPI: HTTP {resp.status_code}")
            return []
        # Check if response has content before parsing JSON
        if not resp.text or not resp.text.strip():
            return []
        try:
            data = resp.json()
        except json.JSONDecodeError:
            st.warning(f"NewsAPI: Invalid JSON response")
            return []
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
    except Exception as e:
        # Suppress common JSON parsing errors (usually means empty/invalid API response)
        error_str = str(e)
        if "Expecting value" not in error_str and "JSON" not in error_str:
            # Only show warning for non-JSON errors (network, auth, etc.)
            st.warning(f"NewsAPI fetch failed: {e}")
        return []
    return results


@st.cache_data(ttl=1800, show_spinner=False)
def cached_fetch_gdelt(query: str, max_results: int = 6) -> List[Dict[str, Any]]:
    """Fetch news from GDELT API."""
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
    except Exception as e:
        st.warning(f"GDELT fetch failed: {e}")
        return []
    return results


class LiveNewsFetcher:
    """Fetches news from multiple sources."""
    
    def __init__(self):
        self.newsapi_key = EnhancedAppConfig.NEWSAPI_API_KEY
    
    def fetch_google_news_rss(self, query: str, max_results: int = 8):
        """Fetch from Google News RSS."""
        return cached_fetch_google_news_rss(query, max_results=max_results)
    
    def fetch_newsapi(self, query: str, max_results: int = 8):
        """Fetch from NewsAPI."""
        return cached_fetch_newsapi(query, newsapi_key=self.newsapi_key, max_results=max_results)
    
    def fetch_gdelt(self, query: str, max_results: int = 6):
        """Fetch from GDELT."""
        return cached_fetch_gdelt(query, max_results=max_results)
    
    def fetch_all_news_sources(self, query: str, max_total: int = 15):
        """Fetch from all available news sources and deduplicate."""
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

