"""
Alternative approach: AI-powered query understanding for complex questions.
This shows how to add LLM-based query parsing as a fallback.
"""

import json
import logging
from typing import Dict, Any, Optional
from src.config import get_config
from src.llm import get_openai_client, OpenAIClientError

logger = logging.getLogger(__name__)


def parse_complex_query_with_ai(question: str, available_actions: list) -> Optional[Dict[str, Any]]:
    """
    Use AI to parse complex queries that don't match predefined patterns.
    
    This is a fallback for when pattern matching fails.
    Only use for truly ambiguous questions.
    """
    try:
        config = get_config()
        openai_config = config.get_openai_config()
        client = get_openai_client()
        
        system_prompt = f"""You are a query parser for an invoice management system.
        
Available actions: {', '.join(available_actions)}

Parse the user's question and return JSON with:
- "action": one of the available actions
- "parameters": extracted parameters as key-value pairs
- "confidence": 0.0 to 1.0

Available actions explain:
- "count_due": Count invoices due in X days (parameter: days)
- "count_by_value": Count invoices by value comparison (parameters: value, comparison)  
- "total_by_vendor": Get total amount from vendor (parameter: vendor)
- "invoices_by_vendor": List invoices from vendor (parameter: vendor)
- "overdue": Get overdue invoices (no parameters)
- "summary": Get summary statistics (no parameters)

If unclear, return confidence < 0.5 and best guess."""

        response = client.chat.completions.create(
            model=openai_config.text_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse this question: '{question}'"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=200
        )
        
        content = response.choices[0].message.content
        if not content:
            return None
            
        result = json.loads(content)
        logger.info(f"AI parsed query: {result}")
        return result
        
    except (OpenAIClientError, json.JSONDecodeError, Exception) as e:
        logger.warning(f"AI query parsing failed: {e}")
        return None


# Example usage in query_parser.py:
def enhanced_parse_with_ai_fallback(self, question: str):
    """Enhanced version that uses AI as fallback."""
    
    # First try pattern matching
    result = self.parse(question)
    
    # If confidence is low, try AI parsing
    if result.confidence < 0.5:
        available_actions = list(self.patterns.keys())
        ai_result = parse_complex_query_with_ai(question, available_actions)
        
        if ai_result and ai_result.get('confidence', 0) > result.confidence:
            return QueryIntent(
                action=ai_result['action'],
                parameters=ai_result.get('parameters', {}),
                confidence=ai_result.get('confidence', 0.5)
            )
    
    return result