"""
EduIntegrity AI — IBM Granite Connection Test

Verifies that the watsonx.ai credentials in .env are correct and
Granite is reachable. Run this before demoing to confirm IBM services work.

Usage:
    cd backend
    venv\\Scripts\\activate
    python test_granite.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

from ibm_watsonx_ai import Credentials, APIClient
from ibm_watsonx_ai.foundation_models import ModelInference

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

# Test with a realistic academic integrity advisory prompt
response = model.generate_text(
    prompt=(
        "You are an academic integrity advisor. A submission shows 72% lexical similarity "
        "and 85% semantic similarity with reference material. In two sentences, describe "
        "what these indicators suggest without accusing the student."
    ),
    params={"max_new_tokens": 150}
)

print("SUCCESS — IBM Granite responded:")
print(response)
