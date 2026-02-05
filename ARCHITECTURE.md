# Bharat Fact - Modular Architecture

This document describes the modular architecture of the Bharat Fact application after refactoring.

## Directory Structure

```
bharat-fact-working/
├── app.py                    # Main entry point (~60 lines)
├── utils/                    # Utility functions
│   ├── __init__.py
│   ├── config.py            # Configuration & API keys
│   ├── caching.py            # Cache management
│   └── helpers.py            # Helper functions
├── data/                     # Data fetching layer
│   ├── __init__.py
│   └── news_fetcher.py      # News API integrations
├── core/                     # Business logic
│   ├── __init__.py
│   ├── verifier.py          # Verification logic
│   └── prompts.py           # AI prompt templates
└── ui/                       # User interface
    ├── __init__.py
    ├── layout.py            # Header, sidebar, forms
    └── results.py           # Results display
```

## Module Responsibilities

### `utils/` - Utility Functions
- **`config.py`**: Application configuration, API key management, colors, trusted sources
- **`caching.py`**: Verification cache, model cache, cache file paths
- **`helpers.py`**: HTTP requests with retries, JSON extraction, filename sanitization

### `data/` - Data Fetching
- **`news_fetcher.py`**: 
  - Google News RSS integration
  - NewsAPI integration
  - GDELT API integration
  - Deduplication logic

### `core/` - Business Logic
- **`verifier.py`**: 
  - `HybridNewsVerifier` class
  - Gemini AI integration
  - Model initialization and caching
  - Verification workflow
  - Evidence tagging
- **`prompts.py`**: 
  - Prompt templates for AI verification
  - Evidence classification prompts

### `ui/` - User Interface
- **`layout.py`**: 
  - Page configuration and CSS
  - Header rendering
  - Sidebar rendering
  - Verification form
  - URL text extraction
- **`results.py`**: 
  - Results display
  - Evidence visualization
  - PDF report generation
  - Download functionality

## Import Flow

```
app.py
├── ui.layout (BeautifulUI)
├── ui.results (EnhancedUI)
└── core.verifier (HybridNewsVerifier)
    ├── utils.config (EnhancedAppConfig)
    ├── utils.caching (cache functions, MODEL_CACHE_FILE)
    ├── utils.helpers (extract_first_json)
    ├── data.news_fetcher (LiveNewsFetcher)
    └── core.prompts (prompt templates)
```

## Key Improvements

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Maintainability**: Code is easier to locate and modify
3. **Testability**: Modules can be tested independently
4. **Scalability**: Easy to add new features or modify existing ones
5. **Readability**: Clear organization makes the codebase easier to understand

## Usage

Run the application as before:
```bash
streamlit run app.py
```

All functionality remains the same, but the code is now better organized and easier to maintain.

