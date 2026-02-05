"""Core verification logic using Gemini AI."""

import re
import time
from datetime import datetime
from typing import List, Dict, Any

import streamlit as st

from utils.config import EnhancedAppConfig
from utils.caching import (
    load_verification_cache,
    save_verification_cache,
    load_model_cache,
    save_model_cache,
    claim_hash,
    MODEL_CACHE_FILE
)
from utils.helpers import extract_first_json
from data.news_fetcher import LiveNewsFetcher
from core.prompts import create_hybrid_prompt, create_evidence_tagging_prompt


class HybridNewsVerifier:
    """Hybrid news verifier using AI and live news sources."""
    
    def __init__(self):
        self.model = None
        self.is_ready = False
        self.initialization_error = None
        self.news_fetcher = LiveNewsFetcher()
        self._setup_gemini_ai()
    
    def _setup_gemini_ai(self):
        """
        Initialize Gemini AI safely without making API calls at startup.
        Issue 1: Cache model discovery to avoid repeated list_models() calls.
        """
        try:
            import google.generativeai as genai
        except ImportError:
            self.initialization_error = "Gemini SDK not installed"
            return

        api_key = EnhancedAppConfig.GEMINI_API_KEY
        if not api_key:
            self.initialization_error = "GEMINI_API_KEY not found"
            return
        try:
            genai.configure(api_key=api_key)
            
            # Issue 1: Use session state cache first (fastest, no API call)
            if 'gemini_model_name' in st.session_state and st.session_state.gemini_model_name:
                try:
                    cached_model_name = st.session_state.gemini_model_name
                    test_model = genai.GenerativeModel(cached_model_name)
                    # Test if model actually works by checking it can be created
                    self.model = test_model
                    self.model_name = cached_model_name
                    self.is_ready = True
                    return  # Success with session cache - no API call!
                except Exception as e:
                    # Session cache invalid, clear it and try next cache
                    st.session_state.gemini_model_name = None
            
            # Try file cache (persists across sessions, 24h TTL)
            model_cache = load_model_cache()
            cached_model_name = model_cache.get("model_name")
            if cached_model_name:
                try:
                    test_model = genai.GenerativeModel(cached_model_name)
                    self.model = test_model
                    self.model_name = cached_model_name
                    self.is_ready = True
                    # Update session cache
                    st.session_state.gemini_model_name = cached_model_name
                    return  # Success with file cache - no list_models() call!
                except Exception as e:
                    # File cache invalid - clear it and try direct creation
                    # Delete the invalid cache file
                    try:
                        if MODEL_CACHE_FILE.exists():
                            MODEL_CACHE_FILE.unlink()
                    except Exception:
                        pass
            
            # Both caches failed - try direct model creation (no list_models call)
            # This avoids quota consumption from list_models()
            # Try multiple model variants that might be available
            preferred_models = [
                "gemini-1.5-flash",
                "gemini-1.5-pro", 
                "gemini-pro",
                "gemini-2.0-flash-exp"
            ]
            for model_name in preferred_models:
                try:
                    test_model = genai.GenerativeModel(model_name)
                    # If we get here, model creation succeeded
                    self.model = test_model
                    self.model_name = model_name
                    self.is_ready = True
                    # Cache the successful model
                    st.session_state.gemini_model_name = model_name
                    save_model_cache(model_name, [model_name])
                    return  # Success - no list_models() call!
                except Exception as e:
                    # Model not available, try next one
                    error_str = str(e)
                    if "404" in error_str or "not found" in error_str.lower():
                        # This model definitely doesn't exist, continue to next
                        continue
                    # Other errors might be temporary, but still try next model
                    continue
            
            # Last resort: only call list_models() if direct creation fails
            # This should rarely happen with valid API keys, and we cache the result
            model_name = None
            try:
                all_models = list(genai.list_models())
                available_models = []
                for m in all_models:
                    if hasattr(m, 'supported_generation_methods'):
                        if 'generateContent' in m.supported_generation_methods:
                            model_name_full = m.name
                            if "/" in model_name_full:
                                short_name = model_name_full.split("/")[-1]
                            else:
                                short_name = model_name_full
                            available_models.append({
                                'full_name': model_name_full,
                                'short_name': short_name,
                                'model_obj': m
                            })
                
                # Try preferred models first
                preferred_models = ["gemini-1.5-flash", "gemini-1.5-pro"]
                for preferred in preferred_models:
                    for model_info in available_models:
                        if preferred == model_info['short_name'] or preferred in model_info['full_name']:
                            try:
                                test_model = genai.GenerativeModel(model_info['short_name'])
                                model_name = model_info['short_name']
                                break
                            except Exception:
                                continue
                    if model_name:
                        break
                
                # If no preferred model, try any available
                if not model_name and available_models:
                    for model_info in available_models:
                        try:
                            test_model = genai.GenerativeModel(model_info['short_name'])
                            model_name = model_info['short_name']
                            break
                        except Exception:
                            continue
            except Exception:
                # If listing fails, model_name remains None
                pass
            
            if not model_name:
                error_msg = "No available Gemini models found. Please check your API key and ensure you have access to Gemini models at https://ai.google.dev/"
                raise Exception(error_msg)
            
            # Create the actual model instance and cache it
            self.model = genai.GenerativeModel(model_name)
            self.model_name = model_name
            self.is_ready = True
            # Cache the successful model (both session and file cache)
            st.session_state.gemini_model_name = model_name
            save_model_cache(model_name, [model_name])
        except Exception as e:
            self.initialization_error = f"Gemini initialization failed: {e}"

    def verify_news(self, news_claim: str):
        """Verify a news claim using AI and live sources."""
        if not self.is_ready:
            return self._create_error_response(self.initialization_error or "AI engine not ready")

        claim_key = claim_hash(news_claim)
        cache = load_verification_cache()

        # ✅ Return cached result if available
        if claim_key in cache:
            cached_copy = cache[claim_key].copy()
            cached_copy["cached"] = True
            return cached_copy

        # ❌ Not cached → full verification
        try:
            live_evidence = self.news_fetcher.fetch_all_news_sources(news_claim)
        except Exception:
            live_evidence = []

        # Issue 2: Include evidence tagging in main prompt to reduce API calls
        prompt = create_hybrid_prompt(news_claim, live_evidence, include_evidence_tags=True)

        # Retry logic for rate limits with exponential backoff
        max_retries = 3
        retry_delay = 2  # Start with 2 seconds
        ai_text = None
        
        for attempt in range(max_retries):
            try:
                gen = self.model.generate_content(prompt)
                ai_text = getattr(gen, "text", None) or (
                    gen.get("text") if isinstance(gen, dict) else None
                )
                if not ai_text:
                    return self._create_error_response("No response from AI")
                break  # Success, exit retry loop
            except Exception as e:
                error_str = str(e)
                # Check if it's a model not found error (404) - handle this first
                if "404" in error_str and ("not found" in error_str.lower() or "models/" in error_str):
                    # Model doesn't exist - clear invalid cache and reinitialize
                    if attempt == 0:  # Only try alternative models on first attempt
                        st.warning("Cached model is not available. Finding a working model...")
                        try:
                            # Clear invalid caches
                            st.session_state.gemini_model_name = None
                            try:
                                if MODEL_CACHE_FILE.exists():
                                    MODEL_CACHE_FILE.unlink()
                            except Exception:
                                pass
                            
                            # Reinitialize model discovery (this will try all available models)
                            import google.generativeai as genai
                            genai.configure(api_key=EnhancedAppConfig.GEMINI_API_KEY)
                            
                            # Try all possible models
                            alt_models = [
                                "gemini-1.5-flash",
                                "gemini-1.5-pro",
                                "gemini-pro",
                                "gemini-2.0-flash-exp"
                            ]
                            
                            for alt_model in alt_models:
                                try:
                                    alt_gen = genai.GenerativeModel(alt_model)
                                    # Test with a small prompt first
                                    test_prompt = "Test"
                                    test_response = alt_gen.generate_content(test_prompt)
                                    # If test works, try the actual prompt
                                    alt_response = alt_gen.generate_content(prompt)
                                    ai_text = getattr(alt_response, "text", None) or (
                                        alt_response.get("text") if isinstance(alt_response, dict) else None
                                    )
                                    if ai_text:
                                        # Update model for future use and cache it
                                        self.model = alt_gen
                                        self.model_name = alt_model
                                        st.session_state.gemini_model_name = alt_model
                                        save_model_cache(alt_model, [alt_model])
                                        st.success(f"Switched to model: {alt_model}")
                                        break
                                except Exception as model_error:
                                    # This model doesn't work, try next
                                    continue
                            
                            if ai_text:
                                break  # Success with alternative model
                            else:
                                # Try list_models as last resort
                                try:
                                    all_models = list(genai.list_models())
                                    for m in all_models:
                                        if hasattr(m, 'supported_generation_methods'):
                                            if 'generateContent' in m.supported_generation_methods:
                                                model_name_full = m.name.split("/")[-1] if "/" in m.name else m.name
                                                try:
                                                    alt_gen = genai.GenerativeModel(model_name_full)
                                                    alt_response = alt_gen.generate_content(prompt)
                                                    ai_text = getattr(alt_response, "text", None) or (
                                                        alt_response.get("text") if isinstance(alt_response, dict) else None
                                                    )
                                                    if ai_text:
                                                        self.model = alt_gen
                                                        self.model_name = model_name_full
                                                        st.session_state.gemini_model_name = model_name_full
                                                        save_model_cache(model_name_full, [model_name_full])
                                                        st.success(f"Using model: {model_name_full}")
                                                        break
                                                except Exception:
                                                    continue
                                    if ai_text:
                                        break
                                except Exception:
                                    pass
                                
                                if not ai_text:
                                    return self._create_error_response(
                                        f"No available Gemini models found. Please check your API key at https://ai.google.dev/. "
                                        f"Original error: {error_str[:200]}"
                                    )
                        except Exception as reinit_error:
                            return self._create_error_response(
                                f"Model initialization failed. Please check your API key. "
                                f"Error: {str(reinit_error)[:200]}"
                            )
                    else:
                        # Already tried alternative, give up
                        return self._create_error_response(
                            f"Model not available. Please check your API key. Error: {error_str[:200]}"
                        )
                # Check if it's a rate limit/quota error (429)
                elif "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Extract retry delay from error if available
                        delay_match = re.search(r'retry.*?(\d+)', error_str, re.IGNORECASE)
                        if delay_match:
                            retry_delay = int(delay_match.group(1)) + 5  # Add buffer
                        else:
                            retry_delay = retry_delay * (2 ** attempt)  # Exponential backoff
                        
                        st.warning(f"Rate limit hit. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        # Last attempt failed
                        return self._create_error_response(
                            f"Rate limit exceeded. Please wait a few minutes and try again. "
                            f"Error: {error_str[:200]}"
                        )
                else:
                    # Non-rate-limit, non-404 error, don't retry
                    return self._create_error_response(f"AI analysis failed: {e}")
        
        if not ai_text:
            return self._create_error_response("Failed to get AI response after retries")

        result = self._parse_hybrid_response(ai_text, live_evidence)

        # ✅ Save result to cache
        result["cached"] = False
        cache[claim_key] = result
        save_verification_cache(cache)

        return result

    @st.cache_data(show_spinner=False)
    def tag_evidence_support(self, news_claim: str, live_evidence: list):
        """Tag evidence articles as supportive, contradictory, or irrelevant."""
        # Convert evidence to stable, cacheable form
        evidence_titles = tuple(
            article.get("title", "") for article in live_evidence
        )

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
            if self.model:
                model = self.model
            else:
                # Fallback: try to use the same model as main verifier
                if hasattr(self, 'model_name') and self.model_name:
                    try:
                        model = genai.GenerativeModel(self.model_name)
                    except Exception:
                        # If stored model name doesn't work, try common ones
                        for model_name in ["gemini-1.5-flash", "gemini-1.5-pro"]:
                            try:
                                model = genai.GenerativeModel(model_name)
                                break
                            except Exception:
                                continue
                        if 'model' not in locals():
                            raise Exception("No available model")
                else:
                    # Try common free-tier models (removed gemini-pro)
                    for model_name in ["gemini-1.5-flash", "gemini-1.5-pro"]:
                        try:
                            model = genai.GenerativeModel(model_name)
                            break
                        except Exception:
                            continue
                    if 'model' not in locals():
                        raise Exception("No available model")
        except Exception:
            return {
                "items": [],
                "counts": {
                    "supportive": 0,
                    "contradictory": 0,
                    "irrelevant": 0
                }
            }

        prompt = create_evidence_tagging_prompt(news_claim, list(evidence_titles))

        # Retry logic for rate limits
        max_retries = 2
        retry_delay = 2
        raw = ""
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                raw = getattr(response, "text", "")
                break  # Success
            except Exception as e:
                error_str = str(e)
                if ("429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower()) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                # If not rate limit or last attempt, return empty
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

    def _parse_hybrid_response(self, ai_text: str, live_evidence: list):
        """Parse AI response into structured result."""
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
        """Create an error response."""
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

