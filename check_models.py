import os
from openai import OpenAI

# Load API Key
config_path = os.path.join(os.path.dirname(__file__), 'api.config')
api_key = None
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('KEY'):
                parts = line.split('=')
                if len(parts) >= 2:
                    api_key = parts[1].strip()
                    break

if not api_key:
    print("API Key not found")
    exit(1)

client = OpenAI(
    api_key=api_key,
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

try:
    print(f"Attempting to list models with Key: {api_key[:5]}...")
    models = client.models.list()
    print("Available Models/Endpoints:")
    for model in models.data:
        print(f"- {model.id}")
except Exception as e:
    print(f"Error listing models: {e}")
