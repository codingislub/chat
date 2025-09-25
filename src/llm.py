import os
from typing import Any, Dict
from openai import OpenAI


OPENAI_MODEL_VISION = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
OPENAI_MODEL_TEXT = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")


def get_openai_client() -> OpenAI:
	api_key = os.getenv("OPENAI_API_KEY")
	if not api_key:
		raise RuntimeError("OPENAI_API_KEY is not set. Set it in your environment.")
	return OpenAI(api_key=api_key)


def extract_invoice_fields_from_image(image_url: str) -> Dict[str, Any]:
	client = get_openai_client()
	system_prompt = (
		"You are a precise invoice extraction engine. "
		"Extract these fields if present: vendor, invoice_number, invoice_date (YYYY-MM-DD), "
		"due_date (YYYY-MM-DD), total (number). "
		"If a field is missing or unreadable, return null for that field. "
		"Only output strict JSON with keys: vendor, invoice_number, invoice_date, due_date, total."
	)

	resp = client.chat.completions.create(
		model=OPENAI_MODEL_VISION,
		messages=[
			{"role": "system", "content": system_prompt},
			{
				"role": "user",
				"content": [
					{"type": "text", "text": "Extract fields from this invoice image."},
					{"type": "image_url", "image_url": {"url": image_url}},
				],
			},
		],
		response_format={"type": "json_object"},
		temperature=0.0,
	)

	content = resp.choices[0].message.content
	import json
	try:
		data = json.loads(content)
		return {
			"vendor": data.get("vendor"),
			"invoice_number": data.get("invoice_number"),
			"invoice_date": data.get("invoice_date"),
			"due_date": data.get("due_date"),
			"total": data.get("total"),
		}
	except Exception:
		return {
			"vendor": None,
			"invoice_number": None,
			"invoice_date": None,
			"due_date": None,
			"total": None,
		}
