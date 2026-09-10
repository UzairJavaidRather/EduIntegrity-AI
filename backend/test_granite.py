
import os
from dotenv import load_dotenv
from ibm_watsonx_ai import Credentials, APIClient
from ibm_watsonx_ai.foundation_models import ModelInference

load_dotenv()

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

response = model.generate_text(
    prompt="In one sentence, what is academic integrity?"
)

print("SUCCESS. Granite responded:")
print(response)