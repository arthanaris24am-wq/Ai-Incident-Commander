import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from backend/.env if needed
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

class GeminiService:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = None
        if self.api_key and self.api_key.strip() != "" and self.api_key != "YOUR_KEY":
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Failed to initialize Gemini Client: {e}")
                self.client = None

    def health_check(self) -> Dict[str, Any]:
        """
        Check if the Gemini API is available.
        """
        if not self.client:
            return {
                "available": False,
                "provider": "Gemini",
                "status": "fallback",
                "reason": "API key not configured or client failed to initialize"
            }
        
        # We can attempt a lightweight generation or just assume it's connected if we have a client.
        # But for speed, if the client initialized, we assume connected. We will handle quota errors at runtime.
        return {
            "available": True,
            "provider": "Gemini",
            "status": "connected"
        }

    def generate_json(self, prompt: str, schema: Any, system_instruction: str = "") -> Dict[str, Any]:
        """
        Reusable method to generate structured JSON from Gemini.
        Returns the parsed JSON dictionary, or a safe fallback on error.
        """
        if not self.client:
            raise Exception("Gemini API is unavailable (fallback mode).")

        model_name = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=schema,
                        temperature=0.2
                    )
                )
                return json.loads(response.text)
            except Exception as e:
                err_msg = str(e).lower()
                if ("503" in err_msg or "high demand" in err_msg or "unavailable" in err_msg or "429" in err_msg) and attempt < 2:
                    import time
                    time.sleep(2 * (attempt + 1))
                    continue
                print(f"Gemini API Error: {e}")
                raise

gemini_service = GeminiService()
