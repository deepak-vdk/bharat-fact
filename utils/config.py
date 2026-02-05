"""Configuration settings for Bharat Fact application."""

import os
import streamlit as st


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

