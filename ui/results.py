"""Results display components."""

from datetime import datetime
from textwrap import dedent

import streamlit as st
import streamlit.components.v1 as components

from utils.config import EnhancedAppConfig
from utils.helpers import safe_filename


class EnhancedUI:
    """UI components for displaying verification results."""
    
    @staticmethod
    def render_enhanced_results(result_data, query_text):
        """Render the enhanced results display."""
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
        """Render the download section for PDF reports."""
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
                clean_name = safe_filename(news_claim)[:50]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"bharatfact_{clean_name}_{timestamp}.pdf"
            else:
                filename = f"bharatfact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            st.download_button("Download PDF Report", data=pdf_bytes, file_name=filename, mime="application/pdf")
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
            st.info("Install reportlab: pip install reportlab")

