"""Prompt templates for AI verification."""


def create_hybrid_prompt(news_claim: str, live_evidence: list, include_evidence_tags: bool = True) -> str:
    """
    Create prompt that combines verification and evidence tagging in one call.
    This reduces API calls from 2 to 1 per verification.
    """
    evidence_text = ""
    evidence_list_for_tagging = ""
    if live_evidence:
        evidence_text = "LIVE NEWS EVIDENCE FOUND:\n"
        evidence_list_for_tagging = "EVIDENCE ARTICLES TO CLASSIFY:\n"
        for i, article in enumerate(live_evidence[:8], 1):
            title = article.get('title', '')
            evidence_text += f"{i}. {title}\n"
            if article.get('source'):
                evidence_text += f"   Source: {article.get('source')}\n"
            if article.get('published'):
                evidence_text += f"   Published: {article.get('published')}\n"
            evidence_text += f"   URL: {article.get('link')}\n\n"
            # For tagging, just include titles with index
            evidence_list_for_tagging += f"{i}. {title}\n"
    else:
        evidence_text = "LIVE NEWS EVIDENCE: No recent articles found from trusted sources.\n"
    
    # Issue 2: Include evidence tagging in the main prompt to avoid second API call
    tagging_instruction = ""
    if include_evidence_tags and live_evidence:
        tagging_instruction = f"""

EVIDENCE CLASSIFICATION (include this in your response):
After your main analysis, classify each evidence article as supportive, contradictory, or irrelevant.
Return a JSON array like: [{{"index":1,"tag":"supportive","rationale":"brief reason"}}, ...]
{evidence_list_for_tagging}
"""
    
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
{tagging_instruction}
"""


def create_evidence_tagging_prompt(news_claim: str, evidence_titles: list) -> str:
    """Create prompt for evidence tagging."""
    headlines = []
    for i, title in enumerate(evidence_titles, 1):
        headlines.append(f"{i}. {title}")

    return f"""
Claim:
"{news_claim}"

Headlines:
{chr(10).join(headlines)}

Classify each headline as:
supportive, contradictory, or irrelevant.

Return STRICT JSON like:
[
  {{"index":1,"tag":"supportive","rationale":"short reason"}}
]
"""

