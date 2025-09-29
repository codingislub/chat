import logging
import os
from typing import Any, Dict, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion


# Configure logging
logger = logging.getLogger(__name__)

# Configuration with fallbacks
OPENAI_MODEL_VISION = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
OPENAI_MODEL_TEXT = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")
DEFAULT_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))


class OpenAIClientError(Exception):
    """Custom exception for OpenAI client errors."""
    pass


class InvoiceExtractionError(Exception):
    """Custom exception for invoice extraction errors."""
    pass


def get_openai_client() -> OpenAI:
    """Get configured OpenAI client with error handling."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise OpenAIClientError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it to your OpenAI API key."
        )
    
    try:
        return OpenAI(
            api_key=api_key,
            timeout=DEFAULT_TIMEOUT,
            max_retries=MAX_RETRIES
        )
    except Exception as e:
        raise OpenAIClientError(f"Failed to initialize OpenAI client: {e}")


def extract_invoice_fields_from_image(image_url: str) -> Dict[str, Any]:
    """
    Extract invoice fields from image URL using OpenAI Vision API.
    
    Args:
        image_url: URL of the invoice image to process
        
    Returns:
        Dictionary containing extracted invoice fields
        
    Raises:
        InvoiceExtractionError: If extraction fails
    """
    if not image_url or not isinstance(image_url, str):
        raise InvoiceExtractionError("Invalid image URL provided")
    
    logger.info(f"Extracting invoice fields from image: {image_url}")
    
    try:
        client = get_openai_client()
    except OpenAIClientError as e:
        raise InvoiceExtractionError(f"OpenAI client error: {e}")
    
    system_prompt = (
        "You are a precise invoice extraction engine. "
        "Extract these fields if present: vendor, invoice_number, invoice_date (YYYY-MM-DD), "
        "due_date (YYYY-MM-DD), total (number). "
        "If a field is missing or unreadable, return null for that field. "
        "Only output strict JSON with keys: vendor, invoice_number, invoice_date, due_date, total."
    )

    try:
        response: ChatCompletion = client.chat.completions.create(
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
        
        content = response.choices[0].message.content
        if not content:
            raise InvoiceExtractionError("Empty response from OpenAI API")
            
        logger.debug(f"Raw OpenAI response: {content}")
        
    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        raise InvoiceExtractionError(f"Failed to call OpenAI API: {e}")

    # Parse JSON response with error handling
    try:
        import json
        data = json.loads(content)
        
        # Validate expected structure
        extracted_fields = {
            "vendor": data.get("vendor"),
            "invoice_number": data.get("invoice_number"),
            "invoice_date": data.get("invoice_date"),
            "due_date": data.get("due_date"),
            "total": data.get("total"),
        }
        
        logger.info(f"Successfully extracted invoice fields: {extracted_fields}")
        return extracted_fields
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.debug(f"Invalid JSON content: {content}")
        # Return empty fields instead of crashing
        return {
            "vendor": None,
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "total": None,
        }
    except Exception as e:
        logger.error(f"Unexpected error during field extraction: {e}")
        raise InvoiceExtractionError(f"Failed to extract fields: {e}")
