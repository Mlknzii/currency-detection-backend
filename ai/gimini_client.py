import base64
import json
from io import BytesIO

from PIL import Image
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"  # or whatever model you ended up using
genai.configure(api_key=API_KEY)


def analyze_currency(image_bytes: bytes):
    """
    Sends image bytes to Gemini and returns structured JSON with:
    currency_code, confidence, name_en, name_ar, denomination_value, is_counterfeit
    """

    # 1) Re-encode image as JPEG base64
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # 2) Prompt with strong JSON-only instruction
    prompt = """
You are a currency authentication expert.

Analyze the provided banknote image and return a JSON ONLY with these fields:

{
  "currency_code": "string",
  "confidence": float (0-1),
  "name_en": "string",
  "name_ar": "string",
  "denomination_value": int,
  "is_counterfeit": boolean
}

Rules:
- Reply with JSON ONLY. Do not include any extra text, markdown, or explanation.
- Do NOT wrap the JSON in ``` or ```json.
- If unsure, confidence must be lower.
- denomination_value must be an integer (100, 200, 500, 1000 for SDG).
- If fake or suspicious => is_counterfeit = true.
- name_ar MUST be Arabic translation.
"""

    model = genai.GenerativeModel(MODEL_NAME)

    response = model.generate_content(
        [
            prompt,
            {
                "mime_type": "image/jpeg",
                "data": encoded_image,
            },
        ]
    )

    # 3) Extract text safely
    raw_text = (response.text or "").strip()

    # In case Gemini still sends markdown fences, strip them
    if raw_text.startswith("```"):
        # Remove first ```... line
        lines = raw_text.splitlines()
        # Drop first line if it starts with ```
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # Drop last line if it is just ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()

    # 4) Parse JSON safely
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        # Raise clear error for FastAPI to catch
        raise ValueError(
            f"Gemini returned invalid JSON. Raw output: {raw_text}"
        ) from e

    # 5) Basic validation / normalization
    # Ensure required keys exist
    required_keys = [
        "currency_code",
        "confidence",
        "name_en",
        "name_ar",
        "denomination_value",
        "is_counterfeit",
    ]
    for k in required_keys:
        if k not in data:
            raise ValueError(
                f"Gemini response missing key '{k}'. Raw output: {raw_text}"
            )

    # Normalize types
    try:
        data["currency_code"] = str(data["currency_code"]).upper()
        data["name_en"] = str(data["name_en"])
        data["name_ar"] = str(data["name_ar"])
        data["confidence"] = float(data["confidence"])
        data["denomination_value"] = int(data["denomination_value"])
        data["is_counterfeit"] = bool(data["is_counterfeit"])
    except Exception as e:
        raise ValueError(
            f"Gemini response has wrong field types. Parsed: {data}"
        ) from e

    return data
