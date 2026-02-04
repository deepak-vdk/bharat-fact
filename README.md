# Indian News Verifier

An AI-powered system designed for the verification of Indian news, providing reliable fake news detection.

**Developed by Deepak**

## Quick Start

### Prerequisites

* Python 3.8 or higher
* Internet connection
* Gemini API key (available for free from Google)

### Installation & Setup

1. **Clone the repository:**

```bash
git clone [your-repo-url]
cd "BharatFact"
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Setup API key:**

```bash
# Copy the template file
cp .env.example .env

# Edit the .env file and add your API key:
# GEMINI_API_KEY=your_actual_api_key_here
```

Obtain a free Gemini API key here: [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

4. **Run the application:**

```bash
streamlit run app.py
```

5. **Open in browser:**

* Local: [http://localhost:8501](http://localhost:8501)
* Network: http://[your-ip]:8501

## Features

* Real-time verification of Indian news claims
* AI-powered analysis with confidence scoring
* URL extraction from news websites
* Mobile-friendly, responsive design
* Context-aware for Indian news
* Professional display of results
* Downloadable reports

## Use Cases

* Political news verification
* Verification of forwarded messages on WhatsApp
* Social media claims validation
* Breaking news confirmation
* Academic presentations
* Journalism fact-checking

## How to Use

1. Choose the input method: Text or News URL
2. Enter your news claim or paste a news URL
3. Click "Verify News" to start AI analysis
4. Review results with confidence scores
5. Cross-check with recommended sources
6. Download reports for documentation

## Important Notes

* The tool provides AI-assisted analysis
* Always cross-reference results with multiple reliable sources
* Higher confidence scores indicate more reliable outcomes
* Suitable for presentations and demonstrations

## Technical Details

* Built with Streamlit for an intuitive user interface
* Advanced AI for intelligent analysis
* Real-time web scraping capabilities
* Integration with Indian news sources
* Professional confidence scoring system

## Security & Deployment

### GitHub

* The `.env` file is automatically ignored by Git
* API keys will not be pushed to GitHub
* Use `.env.example` as a template for collaborators

### Vercel Deployment

1. Push the repository to GitHub (API key remains secure)
2. In the Vercel dashboard:

   * Go to Project Settings → Environment Variables
   * Add `GEMINI_API_KEY` with your API key
3. Deploy – the API key remains secure

### Environment Variables

* `GEMINI_API_KEY` – Your Gemini API key (required)

## Support

For troubleshooting or questions:

* Ensure a stable internet connection for AI analysis
* Use valid news URLs for extraction
* Provide clear and specific news claims for optimal results

---
