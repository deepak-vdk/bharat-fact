"""Helper utility functions."""

import json
import re
import time
import requests
from requests.exceptions import RequestException, Timeout
import streamlit as st


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

        except (RequestException, Timeout) as e:
            if attempt == retries - 1:
                st.warning(f"Request failed: {e}")
                return None
            time.sleep(backoff_factor * (2 ** attempt))


def extract_first_json(text: str):
    """
    Safely extract the first valid JSON object or array from text.
    """
    if not text or not isinstance(text, str):
        return None

    text = text.strip()

    # Try to find JSON object or array start positions
    starts = []
    for i, ch in enumerate(text):
        if ch == '{' or ch == '[':
            starts.append(i)

    for start in starts:
        for end in range(start + 1, len(text) + 1):
            try:
                candidate = text[start:end]
                return json.loads(candidate)
            except Exception:
                continue

    return None


def safe_filename(s: str, maxlen: int = 50) -> str:
    """Generate a safe filename from a string."""
    if not s:
        return "fact_check"
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'\s+', '_', s).strip('_')
    return s[:maxlen] or "fact_check"

