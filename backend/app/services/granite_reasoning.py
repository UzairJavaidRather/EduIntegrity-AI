import os
from dotenv import load_dotenv
from ibm_watsonx_ai import Credentials, APIClient
from ibm_watsonx_ai.foundation_models import ModelInference


load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))


def build_client():
    credentials = Credentials(
        url=os.environ["WATSONX_URL"],
        api_key=os.environ["IBM_CLOUD_API_KEY"],
    )

    client = APIClient(credentials)
    client.set.default_project(os.environ["WATSONX_PROJECT_ID"])

    model = ModelInference(
        model_id=os.environ["GRANITE_MODEL_ID"],
        api_client=client,
    )
    return model


def generate_reasoning(summary: str) -> str:
    model = build_client()
    prompt = (
        "You are an AI analyst for an anti-corruption and project-monitoring system. "
        "Explain the following project summary in clear, evidence-based language. "
        "Do not accuse anyone. Focus on risk indicators, mismatches, and next steps.\n\n"
        f"Project summary:\n{summary}"
    )

    response = model.generate_text(
        prompt=prompt,
        params={"max_new_tokens": 200}
    )

    if isinstance(response, dict):
        return response.get("results", [{}])[0].get("generated_text", str(response))

    return str(response)


if __name__ == "__main__":
    sample = (
        "Project: Community Hall renovation. Approved budget: 25 lakh. "
        "Release: 20 lakh. Expenditure: 23 lakh. Reported progress: 70%. "
        "Evidence-supported progress: 48%. Missing inspection certificate. "
        "Potential duplicate work detected near same location."
    )

    print(generate_reasoning(sample))
