import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv(".env.local")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("🔍 Pinging Google to find available models...")

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ AVAILABLE: {m.name}")
except Exception as e:
    print(f"❌ Error: {e}")