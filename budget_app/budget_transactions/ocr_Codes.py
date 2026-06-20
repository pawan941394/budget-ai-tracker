
import os
import json
import sys
from pathlib import Path
from pydantic import BaseModel, Field
from rapidocr import RapidOCR
from pydantic_ai import Agent


class TransactionData(BaseModel):
    status: str | None = None
    amount: float | None = None
    sender_name: str | None = None
    sender_upi: str | None = None
    receiver_name: str | None = None
    receiver_upi: str | None = None
    bank: str | None = None
    timestamp: str | None = None
    reference_id: str | None = None
    payment_type: str | None = None
    utr_id: str | None = None


def image_ocr(image_path):
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found.", file=sys.stderr)
        sys.exit(1)
    
    engine = RapidOCR()
    result = engine(image_path)
    if hasattr(result, "txts"):
        return list(result.txts)

    if isinstance(result, tuple) and result and result[0]:
        first_item = result[0]
        if isinstance(first_item, list) and first_item and isinstance(first_item[0], list):
            return [item[1] for item in first_item]

    return []


def build_raw_text(txts):
    if not txts:
        return ""
    return " ".join(str(token) for token in txts)


def extract_with_gemini(raw_text,api_key):
    if not api_key:
        print("Error: an API key is required for transaction extraction.", file=sys.stderr)
        sys.exit(1)

    os.environ["GOOGLE_API_KEY"] = api_key
    agent = Agent('google:gemini-flash-lite-latest', output_type=TransactionData)
    prompt = (
        "Extract transaction details from the raw OCR text below. "
        "Return ONLY valid JSON matching this schema exactly: "
        "{status, amount, sender_name, sender_upi, receiver_name, receiver_upi, bank, timestamp, reference_id, payment_type, raw_text}. "
        "For `payment_type` return a single value: either 'received', 'sent', or null. "
        "If a field is missing, use null. Do not add extra keys.\n\n"
        f"RAW TEXT:\n{raw_text}"
    )
    result = agent.run_sync(prompt)
    return result.output

def get_transaction_data(image_path, api_key=None):
    txts = image_ocr(image_path)
    raw_text = build_raw_text(txts)
    parsed = extract_with_gemini(raw_text, api_key)
    return parsed
