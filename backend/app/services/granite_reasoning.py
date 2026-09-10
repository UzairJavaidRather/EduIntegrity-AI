"""
EduIntegrity AI — IBM Granite Reasoning Service

Sends structured analysis evidence to IBM Granite (via watsonx.ai)
and returns a natural-language integrity assessment.

The prompt is designed so Granite:
  - Explains the evidence in plain language
  - Identifies specific suspicious patterns
  - Does NOT accuse the student
  - Uses language like "indicators suggest" and "warrants review"
  - Recommends instructor follow-up steps

IBM watsonx.ai SDK reference:
  https://ibm.github.io/watson-machine-learning-py-client/

IMPORTANT: Verify the exact GRANITE_MODEL_ID from IBM watsonx Prompt Lab
before use. Do not hardcode unverified model IDs.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _build_client():
    """
    Create and return a Granite ModelInference client.
    Reads credentials from environment variables — never from code.

    Raises:
        KeyError: If required environment variables are not set.
        Exception: If IBM watsonx.ai connection fails.
    """
    # Import here so the module can be imported even without ibm_watsonx_ai
    # installed — useful for testing the rest of the pipeline offline.
    from ibm_watsonx_ai import Credentials, APIClient
    from ibm_watsonx_ai.foundation_models import ModelInference

    credentials = Credentials(
        url=os.environ["WATSONX_URL"],
        api_key=os.environ["IBM_CLOUD_API_KEY"],
    )
    client = APIClient(credentials)
    client.set.default_project(os.environ["WATSONX_PROJECT_ID"])

    return ModelInference(
        model_id=os.environ["GRANITE_MODEL_ID"],
        api_client=client,
    )


def _build_prompt(evidence: dict) -> str:
    """
    Build a structured prompt from the analysis evidence dict.

    The prompt instructs Granite to act as an academic integrity advisor,
    interpret the evidence, and produce an explanatory assessment without
    making accusations.
    """
    return f"""You are an academic integrity advisor assisting an instructor.
Your role is to explain analysis findings clearly and objectively.
Do not accuse the student of any wrongdoing.
Use language such as "indicators suggest", "patterns warrant review", "may indicate".
The instructor will make the final decision.

SUBMISSION DETAILS:
- Filename: {evidence.get('filename', 'Unknown')}
- Word count: {evidence.get('word_count', 'Unknown')}

ANALYSIS RESULTS:
- Lexical similarity score: {evidence.get('lexical_similarity', 0):.2f} / 1.00
  (Measures direct text overlap using TF-IDF. Higher = more textual overlap.)
- Semantic similarity score: {evidence.get('semantic_similarity', 0):.2f} / 1.00
  (Measures meaning similarity using embeddings. Detects paraphrasing.)
- Overall risk score: {evidence.get('risk_score', 0):.1f} / 100
- Risk level: {evidence.get('risk_level', 'UNKNOWN')}

MATCHED PASSAGES (top lexical matches found):
{evidence.get('matched_passages', 'No passage data available.')}

TASK:
1. In 2-3 sentences, explain what these scores indicate in plain language.
2. Identify the most notable pattern or concern from the evidence above.
3. Suggest one specific follow-up action the instructor could take.

Keep your response under 200 words. Be factual and balanced."""


def generate_assessment(evidence: dict) -> str:
    """
    Send analysis evidence to IBM Granite and return its assessment.

    Args:
        evidence: dict containing analysis results with keys:
            - filename (str)
            - word_count (int)
            - lexical_similarity (float)
            - semantic_similarity (float)
            - risk_score (float)
            - risk_level (str)
            - matched_passages (str)

    Returns:
        A natural-language assessment string from Granite.
        Falls back to a structured summary if Granite is unavailable.
    """
    # Check if credentials are configured
    required = ["WATSONX_URL", "IBM_CLOUD_API_KEY", "WATSONX_PROJECT_ID", "GRANITE_MODEL_ID"]
    missing = [k for k in required if not os.getenv(k) or "your_" in os.getenv(k, "")]

    if missing:
        # Return a fallback summary so the rest of the pipeline still works
        # even without IBM credentials configured
        return _fallback_assessment(evidence)

    try:
        model = _build_client()
        prompt = _build_prompt(evidence)
        response = model.generate_text(
            prompt=prompt,
            params={"max_new_tokens": 300, "temperature": 0.3}
        )

        # SDK may return a string directly or a dict with results
        if isinstance(response, dict):
            return response.get("results", [{}])[0].get("generated_text", "").strip()

        return str(response).strip()

    except Exception as exc:
        # Do not let a Granite failure crash the entire analysis pipeline.
        # Log the error and return the fallback.
        print(f"[granite_reasoning] Granite unavailable: {exc}")
        return _fallback_assessment(evidence)


def _fallback_assessment(evidence: dict) -> str:
    """
    Returns a rule-based assessment when Granite is not available.
    This ensures the UI always shows something meaningful.
    """
    lex  = evidence.get("lexical_similarity", 0)
    sem  = evidence.get("semantic_similarity", 0)
    risk = evidence.get("risk_score", 0)
    level = evidence.get("risk_level", "UNKNOWN")

    observations = []

    if lex > 0.7:
        observations.append(
            f"High lexical similarity ({lex:.0%}) indicates substantial direct text overlap "
            "with the reference corpus. This pattern warrants closer review of the source material."
        )
    elif lex > 0.4:
        observations.append(
            f"Moderate lexical similarity ({lex:.0%}) detected. Some shared phrasing is present."
        )

    if sem > 0.75:
        observations.append(
            f"High semantic similarity ({sem:.0%}) suggests the submission may express ideas "
            "that closely mirror existing content, even where wording differs."
        )
    elif sem > 0.5:
        observations.append(
            f"Moderate semantic similarity ({sem:.0%}) detected. Conceptual overlap is present."
        )

    if not observations:
        observations.append("No strong similarity indicators were detected in this submission.")

    observations.append(
        f"The overall risk score is {risk:.1f}/100 ({level}). "
        "This is a system-generated indicator. "
        "The instructor should review the evidence and make the final determination."
    )

    return " ".join(observations)


if __name__ == "__main__":
    sample_evidence = {
        "filename": "sample_essay.txt",
        "word_count": 309,
        "lexical_similarity": 0.72,
        "semantic_similarity": 0.81,
        "risk_score": 55.4,
        "risk_level": "MODERATE",
        "matched_passages": "- 'academic integrity is the foundation'\n- 'honesty and original work'",
    }
    print(generate_assessment(sample_evidence))
