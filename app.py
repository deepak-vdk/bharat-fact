"""
🇮🇳 INDIAN NEWS VERIFIER - BEAUTIFUL EDITION
============================================
Real-Time News Verification System powered by Advanced AI
Made with ❤️ by deepak
Date: November 2, 2025
Purpose: Fight fake news with AI-powered fact checking focused on Indian context
"""

import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Load environment variables
load_dotenv()

# Helper function to get API key safely
def get_api_key():
    """Safely get API key from secrets or environment variables"""
    # First try environment variable (from .env file)
    api_key = os.getenv('GEMINI_API_KEY', '')
    
    # Then try Streamlit secrets if available
    # Note: Accessing st.secrets can raise StreamlitSecretNotFoundError if secrets.toml doesn't exist
    try:
        secrets_key = st.secrets.get('GEMINI_API_KEY', '')
        if secrets_key:
            return secrets_key
    except (AttributeError, FileNotFoundError, Exception):
        # If secrets are not available (StreamlitSecretNotFoundError or any other error),
        # just use environment variable
        pass
    
    return api_key

# ============================================
# CONFIGURATION SECTION
# ============================================

class AppConfig:
    """Application configuration and settings"""
    
    # API Configuration - Load from environment variables or Streamlit secrets
    GEMINI_API_KEY = get_api_key()
    
    # Application Settings
    APP_TITLE = "🇮🇳 Indian News Verifier"
    APP_SUBTITLE = "AI-Powered Fake News Detection for India"
    VERSION = "2.0"
    
    # UI Theme Colors
    COLORS = {
        'primary': '#FF6B35',
        'secondary': '#004E89', 
        'success': '#2ECC71',
        'warning': '#F39C12',
        'danger': '#E74C3C',
        'info': '#3498DB'
    }
    
    # Indian News Sources
    TRUSTED_SOURCES = [
        "📺 Times of India - https://timesofindia.indiatimes.com",
        "📺 NDTV - https://www.ndtv.com", 
        "📺 The Hindu - https://www.thehindu.com",
        "📺 Indian Express - https://indianexpress.com",
        "📺 India Today - https://www.indiatoday.in",
        "🔍 Alt News (Fact-checker) - https://www.altnews.in",
        "🔍 Boom Live (Fact-checker) - https://www.boomlive.in",
        "🔍 The Quint WebQoof - https://www.thequint.com/news/webqoof"
    ]

# ============================================
# CORE VERIFICATION ENGINE
# ============================================

class IndianNewsVerifier:
    """
    Advanced Indian News Verification Engine
    Uses Advanced AI for intelligent fact-checking with Indian context
    """
    
    def __init__(self):
        """Initialize the verification engine"""
        self.model = None
        self.is_ready = False
        self._setup_gemini_ai()
    
    def _setup_gemini_ai(self):
        """Private method to setup Advanced AI with error handling"""
        try:
            if not AppConfig.GEMINI_API_KEY:
                st.error("🚫 No API key found!")
                st.warning("📝 **For Streamlit Cloud:** Add GEMINI_API_KEY in your app's Secrets (⚙️ Settings → Secrets)")
                st.info("💡 **For local development:** Create a .env file with: GEMINI_API_KEY=your_api_key_here")
                st.code("GEMINI_API_KEY = \"your_api_key_here\"", language="toml")
                return
            
            # Configure AI API
            genai.configure(api_key=AppConfig.GEMINI_API_KEY)
            
            # Try multiple model versions for reliability
            model_options = [
                'gemini-2.5-flash',
                'gemini-flash-latest',
                'models/gemini-2.5-flash',
                'models/gemini-flash-latest'
            ]
            
            for model_name in model_options:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    
                    # Test the model
                    test_response = self.model.generate_content("Test")
                    
                    if test_response and test_response.text:
                        self.is_ready = True
                        st.success(f"✅ AI Engine Ready!")
                        break
                        
                except Exception:
                    continue
            
            if not self.is_ready:
                st.error("❌ Could not initialize AI engine")
                
        except Exception as e:
            st.error(f"🚫 Setup Error: {str(e)}")
    
    def verify_news(self, news_claim):
        """
        Main verification method
        Returns comprehensive analysis of the news claim
        """
        if not self.is_ready:
            return self._create_error_response("AI engine not ready")
        
        try:
            # Create comprehensive analysis prompt
            analysis_prompt = self._create_analysis_prompt(news_claim)
            
            # Get AI response
            response = self.model.generate_content(analysis_prompt)
            
            if not response or not response.text:
                return self._create_error_response("No response from AI")
            
            # Parse and structure the response
            return self._parse_ai_response(response.text)
            
        except Exception as e:
            return self._create_error_response(f"Analysis failed: {str(e)}")
    
    def _create_analysis_prompt(self, news_claim):
        """Create a comprehensive prompt for Indian news analysis"""
        return f"""
        🇮🇳 INDIAN NEWS FACT-CHECK ANALYSIS
        =====================================
        
        You are an expert Indian news fact-checker with deep knowledge of:
        - Indian politics, government, and current affairs
        - Indian media landscape and reliable sources
        - Indian cultural and social context
        - Common misinformation patterns in India
        
        NEWS CLAIM TO ANALYZE:
        "{news_claim}"
        
        Please provide analysis in this EXACT format:
        
        VERIFICATION_STATUS: [TRUE/FALSE/PARTIALLY_TRUE/UNVERIFIED]
        CONFIDENCE_SCORE: [0-100]
        
        DETAILED_ANALYSIS:
        [Provide thorough explanation of why this claim is true/false]
        
        INDIAN_CONTEXT:
        [Explain relevance to Indian politics, society, current events]
        
        EVIDENCE_CHECK:
        [What evidence supports or contradicts this claim]
        
        RECOMMENDED_SOURCES:
        [List specific Indian news sources to verify this claim]
        
        RED_FLAGS:
        [Any warning signs or suspicious elements in this claim]
        
        CONCLUSION:
        [Final assessment with reasoning]
        """
    
    def _parse_ai_response(self, ai_text):
        """Parse AI response into structured format"""
        try:
            # Extract verification status
            status = "UNVERIFIED"
            confidence = 50
            
            # Look for status in AI response
            if "VERIFICATION_STATUS: TRUE" in ai_text:
                status = "TRUE"
                confidence = 85
            elif "VERIFICATION_STATUS: FALSE" in ai_text:
                status = "FALSE" 
                confidence = 90
            elif "VERIFICATION_STATUS: PARTIALLY_TRUE" in ai_text:
                status = "PARTIALLY_TRUE"
                confidence = 70
            elif "VERIFICATION_STATUS: UNVERIFIED" in ai_text:
                status = "UNVERIFIED"
                confidence = 30
            
            # Try to extract confidence score from AI response
            import re
            conf_match = re.search(r'CONFIDENCE_SCORE:\s*(\d+)', ai_text)
            if conf_match:
                extracted_confidence = int(conf_match.group(1))
                # Only use extracted confidence if it makes sense with the status
                if status == "UNVERIFIED" and extracted_confidence > 50:
                    confidence = min(extracted_confidence, 50)  # Cap at 50% for unverified
                elif status in ["TRUE", "FALSE", "PARTIALLY_TRUE"]:
                    confidence = extracted_confidence
            
            # Ensure logical confidence ranges
            if status == "UNVERIFIED" and confidence > 50:
                confidence = 30
            elif status == "TRUE" and confidence < 60:
                confidence = 75
            elif status == "FALSE" and confidence < 70:
                confidence = 80
            elif status == "PARTIALLY_TRUE" and confidence < 50:
                confidence = 65
            
            return {
                'status': status,
                'confidence': confidence,
                'analysis': ai_text,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'sources': AppConfig.TRUSTED_SOURCES[:4],  # Top 4 sources
                'success': True
            }
            
        except Exception as e:
            return self._create_error_response(f"Parse error: {str(e)}")
    
    def _create_error_response(self, error_message):
        """Create standardized error response"""
        return {
            'status': 'ERROR',
            'confidence': 0,
            'analysis': f"❌ {error_message}",
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'sources': [],
            'success': False
        }

# ============================================
# USER INTERFACE COMPONENTS
# ============================================

class BeautifulUI:
    """Beautiful and responsive user interface components"""
    
    @staticmethod
    def setup_page_config():
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title=AppConfig.APP_TITLE,
            page_icon="🇮🇳",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Hide Streamlit watermark and menu
        hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        div[data-testid="stToolbar"] {visibility: hidden;}
        .stActionButton {display:none;}
        </style>
        """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    @staticmethod
    def render_header():
        """Render beautiful header section"""
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #FF6B35; font-size: 3rem; margin-bottom: 0;'>
                🇮🇳 Indian News Verifier
            </h1>
            <p style='color: #004E89; font-size: 1.2rem; margin-top: 0;'>
                AI-Powered Fake News Detection • Advanced AI Technology
            </p>
            <hr style='width: 50%; margin: 2rem auto; border: 2px solid #FF6B35;'>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_sidebar():
        """Render simple sidebar"""
        with st.sidebar:
            st.markdown("### 🛠️ How It Works")
            st.markdown("""
            1. **Enter News** 📝
            2. **AI Analysis** 🤖  
            3. **Get Results** ✅
            """)
            
            st.markdown("---")
            st.markdown("### ⚠️ Note")
            st.markdown("Always verify with multiple sources")
            
            st.markdown("---")
            st.markdown(f"**Version {AppConfig.VERSION}** 🇮🇳")
    
    @staticmethod
    def render_verification_form():
        """Render news input form"""
        # Initialize clear flag in session state
        if 'clear_form' not in st.session_state:
            st.session_state.clear_form = False
        
        st.markdown("### 📝 Enter News to Verify")
        
        # Input methods
        input_method = st.radio(
            "Choose input method:",
            ["✏️ Type/Paste Text", "🔗 News URL"],
            horizontal=True
        )
        
        news_text = ""
        
        # Initialize clear counter
        if 'clear_counter' not in st.session_state:
            st.session_state.clear_counter = 0
        
        # If clearing, use different keys to force reset
        if st.session_state.get('clear_form', False):
            # Counter already incremented when button was clicked, just use it
            pass
        
        if input_method == "✏️ Type/Paste Text":
            text_key = f"news_input_{st.session_state.clear_counter}"
            news_text = st.text_area(
                "Enter the news claim:",
                height=150,
                placeholder="Example: PM Modi announced new education policy today...",
                help="Paste the news text you want to verify",
                key=text_key
            )
        else:
            url_key = f"url_input_{st.session_state.clear_counter}"
            url = st.text_input(
                "Enter news article URL:",
                placeholder="https://example.com/news-article",
                key=url_key
            )
            if url:
                # Extract text from URL
                try:
                    import requests
                    from bs4 import BeautifulSoup
                    
                    with st.spinner("� Extracting text from URL..."):
                        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Extract text from paragraphs
                        paragraphs = soup.find_all('p')
                        extracted_text = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                        
                        if extracted_text:
                            news_text = extracted_text[:1000]  # Limit to 1000 characters
                            st.success("✅ Text extracted successfully!")
                            st.text_area("Extracted text:", value=news_text, height=100, disabled=True)
                        else:
                            st.error("❌ Could not extract text from this URL")
                            news_text = ""
                except Exception as e:
                    st.error(f"❌ Error extracting URL: {str(e)}")
                    news_text = ""
        # Action buttons
        col1, col2, col3 = st.columns([2, 2, 3])
        
        with col1:
            verify_clicked = st.button("🔍 Verify News", type="primary")
        
        with col2:
            example_clicked = st.button("🧪 Try Example")
        
        with col3:
            clear_clicked = st.button("🔄 Clear")
            if clear_clicked:
                st.session_state.clear_form = True
                if 'clear_counter' not in st.session_state:
                    st.session_state.clear_counter = 0
                st.session_state.clear_counter += 1
                st.rerun()
        
        # Reset clear flag after rerun
        if st.session_state.get('clear_form', False):
            st.session_state.clear_form = False
        
        # Handle example button
        if example_clicked:
            return "PM Modi is the current Prime Minister of India", verify_clicked, True
        
        return news_text, verify_clicked, False
    
    @staticmethod
    def render_results(result_data):
        """Render verification results beautifully"""
        if not result_data['success']:
            st.error(result_data['analysis'])
            return
        
        st.markdown("### 📊 Verification Results")
        
        # Status indicators
        status_icons = {
            'TRUE': ('🟢', '#2ECC71'),
            'FALSE': ('🔴', '#E74C3C'),
            'PARTIALLY_TRUE': ('🟡', '#F39C12'),
            'UNVERIFIED': ('⚪', '#95A5A6'),
            'ERROR': ('⚫', '#34495E')
        }
        
        icon, color = status_icons.get(result_data['status'], ('⚪', '#95A5A6'))
        
        # Metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📊 Verification Status",
                f"{icon} {result_data['status']}",
                help="AI assessment of the news claim"
            )
        
        with col2:
            confidence_color = "#2ECC71" if result_data['confidence'] >= 70 else "#F39C12" if result_data['confidence'] >= 50 else "#E74C3C"
            st.metric(
                "🎯 Confidence Level", 
                f"{result_data['confidence']}%",
                help=f"AI confidence in this assessment. {result_data['confidence']}% means the AI is {'very confident' if result_data['confidence'] >= 70 else 'moderately confident' if result_data['confidence'] >= 50 else 'not very confident'} in this result."
            )
        
        with col3:
            st.metric(
                "⏰ Analysis Time",
                result_data['timestamp'].split(' ')[1],
                help="When this analysis was performed"
            )
        
        # Detailed analysis
        st.markdown("### 🧠 Detailed AI Analysis")
        with st.expander("📖 Click to view full analysis", expanded=True):
            st.text_area(
                "AI Analysis:",
                value=result_data['analysis'],
                height=400,
                disabled=True
            )
        
        # Confidence explanation
        if result_data['confidence'] <= 50:
            st.info("ℹ️ **Low Confidence**: The AI couldn't find enough reliable information to make a strong determination. Please verify with multiple sources.")
        elif result_data['confidence'] <= 70:
            st.warning("⚠️ **Moderate Confidence**: The AI has some evidence but recommends additional verification from trusted sources.")
        else:
            st.success("✅ **High Confidence**: The AI found strong evidence to support this assessment, but always cross-check important news.")
        
        # Recommended sources
        st.markdown("### 📰 Recommended Sources for Cross-checking")
        for source in AppConfig.TRUSTED_SOURCES:
            st.markdown(f"- {source}")
        
        # Download report
        BeautifulUI.render_download_section(result_data)
    
    @staticmethod
    def render_download_section(result_data):
        """Render download report section"""
        st.markdown("### 📥 Download Verification Report")
        
        def generate_pdf_report():
            """Generate a beautifully formatted PDF report"""
            from io import BytesIO
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
            
            # Container for PDF content
            story = []
            
            # Define custom styles
            styles = getSampleStyleSheet()
            
            # Title style
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#FF6B35'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            # Subtitle style
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#004E89'),
                spaceAfter=20,
                alignment=TA_CENTER
            )
            
            # Heading style
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#004E89'),
                spaceAfter=12,
                spaceBefore=12,
                fontName='Helvetica-Bold'
            )
            
            # Body style
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#2C3E50'),
                spaceAfter=10,
                alignment=TA_JUSTIFY,
                leading=14
            )
            
            # Status color mapping
            status_colors = {
                'TRUE': colors.HexColor('#2ECC71'),
                'FALSE': colors.HexColor('#E74C3C'),
                'PARTIALLY_TRUE': colors.HexColor('#F39C12'),
                'UNVERIFIED': colors.HexColor('#95A5A6'),
                'ERROR': colors.HexColor('#34495E')
            }
            
            status_icons = {
                'TRUE': '🟢',
                'FALSE': '🔴',
                'PARTIALLY_TRUE': '🟡',
                'UNVERIFIED': '⚪',
                'ERROR': '⚫'
            }
            
            # Title
            story.append(Paragraph("🇮🇳 Indian News Verifier", title_style))
            story.append(Paragraph("AI-Powered Fake News Detection Report", subtitle_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Report metadata
            news_claim = st.session_state.get('last_query', 'Not available')
            story.append(Paragraph("<b>News Claim Verified:</b>", heading_style))
            story.append(Paragraph(f'"{news_claim}"', body_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Verification Results Table
            status_color = status_colors.get(result_data['status'], colors.HexColor('#95A5A6'))
            icon = status_icons.get(result_data['status'], '⚪')
            
            verification_data = [
                ['Verification Status', f'{icon} {result_data["status"]}'],
                ['Confidence Level', f'{result_data["confidence"]}%'],
                ['Analysis Date', result_data['timestamp']]
            ]
            
            verification_table = Table(verification_data, colWidths=[2.5*inch, 4*inch])
            verification_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
                ('BACKGROUND', (1, 0), (1, 0), status_color),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(Paragraph("<b>Verification Results:</b>", heading_style))
            story.append(verification_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Detailed Analysis
            story.append(Paragraph("<b>Detailed AI Analysis:</b>", heading_style))
            # Split analysis into paragraphs if it contains line breaks
            analysis_text = result_data['analysis']
            # Clean up the analysis text and split into paragraphs
            paragraphs = [p.strip() for p in analysis_text.split('\n') if p.strip()]
            for para in paragraphs:
                if para:
                    story.append(Paragraph(para, body_style))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Recommended Sources
            story.append(Paragraph("<b>Recommended Sources for Cross-checking:</b>", heading_style))
            for source in AppConfig.TRUSTED_SOURCES:
                story.append(Paragraph(f"• {source}", body_style))
            
            story.append(Spacer(1, 0.3*inch))
            
            # Disclaimer
            disclaimer_style = ParagraphStyle(
                'Disclaimer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#7F8C8D'),
                spaceAfter=10,
                alignment=TA_CENTER,
                fontStyle='Italic'
            )
            story.append(Paragraph(
                "<i>This is an AI-assisted analysis. Always verify important news with multiple reliable sources.</i>",
                disclaimer_style
            ))
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph(
                f"<i>Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} • Made with ❤️ by deepak</i>",
                disclaimer_style
            ))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        
        try:
            pdf_data = generate_pdf_report()
            
            # Create filename from news claim
            news_claim = st.session_state.get('last_query', '')
            if news_claim:
                # Clean the news claim to create a valid filename
                import re
                # Remove special characters, keep only alphanumeric and spaces
                clean_name = re.sub(r'[^\w\s-]', '', news_claim)
                # Replace multiple spaces with single space
                clean_name = re.sub(r'\s+', ' ', clean_name)
                # Replace spaces with underscores
                clean_name = clean_name.replace(' ', '_')
                # Limit to 50 characters to avoid too long filenames
                clean_name = clean_name[:50].strip('_')
                # Remove trailing underscores
                clean_name = clean_name.rstrip('_')
                # Add timestamp for uniqueness
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"fact_check_{clean_name}_{timestamp}.pdf"
            else:
                # Fallback if no news claim
                filename = f"fact_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            st.download_button(
                "📄 Download PDF Report",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                help="Download detailed verification report as PDF",
                type="primary"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            st.info("Please install reportlab: pip install reportlab")

# ============================================
# MAIN APPLICATION
# ============================================

def main():
    """Main application entry point"""
    
    # Setup page
    BeautifulUI.setup_page_config()
    
    # Initialize session state
    if 'verifier' not in st.session_state:
        st.session_state.verifier = IndianNewsVerifier()
    
    # Render UI components
    BeautifulUI.render_header()
    BeautifulUI.render_sidebar()
    
    # Main content area
    news_text, verify_clicked, is_example = BeautifulUI.render_verification_form()
    
    # Process verification
    if (verify_clicked and news_text.strip()) or is_example:
        st.session_state.last_query = news_text
        
        with st.spinner("🤖 AI is analyzing the news claim..."):
            # Add realistic delay for better UX
            time.sleep(1)
            
            # Perform verification
            result = st.session_state.verifier.verify_news(news_text)
            
        # Display results
        BeautifulUI.render_results(result)
    
    elif verify_clicked and not news_text.strip():
        st.warning("⚠️ Please enter some news text to verify!")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #7F8C8D; padding: 2rem 0;'>
        <p><strong>🇮🇳 Indian News Verifier</strong> • Fighting Misinformation with AI</p>
        <p>Built with Streamlit • Powered by Advanced AI • Version 2.0</p>
        <p><em>Made with ❤️ by deepak</em></p>
        <p><small>Always cross-reference important news with multiple reliable sources</small></p>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# APPLICATION ENTRY POINT
# ============================================

if __name__ == "__main__":
    main()

# ============================================
# END OF FILE
# ============================================
