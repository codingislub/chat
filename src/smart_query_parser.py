"""
Smart query parser using LLM for understanding + local pandas for execution.
This addresses the limitations of regex-based parsing while maintaining performance.
"""

import json
import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.llm import get_openai_client
from src.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ParsedQuery:
    """Structured representation of a parsed query."""
    action: str  
    entities: Dict[str, Any] 
    filters: List[Dict[str, Any]] 
    confidence: float


class SmartQueryParser:
    """LLM-powered query parser that understands natural language without hardcoding."""
    
    def __init__(self):
        self.schema = {
            "actions": [
                "count_invoices",
                "sum_total", 
                "list_invoices",
                "get_summary",
                "find_overdue"
            ],
            "entity_types": [
                "vendor",
                "customer", 
                "amount",
                "date",
                "invoice_number"
            ],
            "filter_operators": [
                "equals",
                "greater_than",
                "less_than", 
                "between",
                "contains"
            ]
        }
    
    def parse(self, question: str, available_vendors: List[str] = None) -> ParsedQuery:
        """
        Parse natural language question into structured query.
        
        Args:
            question: User's question in natural language
            available_vendors: List of known vendors from the dataset (for disambiguation)
            
        Returns:
            ParsedQuery object with extracted intent and entities
        """
        try:
            config = get_config()
            
            if config.openai is None:
                logger.info("OpenAI not available, using fallback parsing")
                return self._enhanced_fallback_parse(question, available_vendors)
                
            openai_config = config.get_openai_config()
            client = get_openai_client()
            
            system_prompt = self._build_system_prompt(available_vendors or [])
            
            response = client.chat.completions.create(
                model=openai_config.text_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this query: '{question}'"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            if not content:
                return self._enhanced_fallback_parse(question, available_vendors)
                
            parsed_result = json.loads(content)
            
            return ParsedQuery(
                action=parsed_result.get('action', 'unknown'),
                entities=parsed_result.get('entities', {}),
                filters=parsed_result.get('filters', []),
                confidence=parsed_result.get('confidence', 0.5)
            )
            
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return self._enhanced_fallback_parse(question, available_vendors)
    
    def _build_system_prompt(self, known_vendors: List[str]) -> str:
        """Build context-aware system prompt."""
        vendor_context = ""
        if known_vendors:
            vendor_context = f"\nKnown vendors in the dataset: {', '.join(known_vendors[:10])}"
        
        return f"""You are an expert at parsing invoice-related queries. Parse the user's question and return structured JSON.

Available actions:
- count_invoices: Count invoices matching criteria
- sum_total: Calculate total amount 
- list_invoices: Show specific invoices
- get_summary: Get overview statistics
- find_overdue: Find past-due invoices

Entity types to extract:
- vendor: Company that sent the invoice
- customer: Company that received the invoice (usually "us")
- amount: Monetary values
- date: Date ranges or specific dates
- invoice_number: Specific invoice identifiers

{vendor_context}

For the query "How many invoices are due from Microsoft to Reliance?":
- This is ambiguous: does it mean invoices FROM Microsoft TO Reliance, or FROM Microsoft (with Reliance mentioned for some other reason)?
- Most likely interpretation: invoices from Microsoft (vendor=Microsoft)
- "due" suggests filtering by due date or overdue status

Return JSON with:
{{
  "action": "count_invoices",
  "entities": {{
    "vendor": "Microsoft",
    "customer": "Reliance" // if relevant
  }},
  "filters": [
    {{"field": "vendor", "operator": "equals", "value": "Microsoft"}},
    {{"field": "status", "operator": "equals", "value": "due"}}
  ],
  "confidence": 0.8,
  "interpretation": "Count invoices from Microsoft that are due",
  "ambiguities": ["unclear if Reliance is customer or another filter"]
}}

Be smart about disambiguation and always explain your interpretation."""

    def _enhanced_fallback_parse(self, question: str, available_vendors: List[str] = None) -> ParsedQuery:
        """Enhanced keyword-based fallback when LLM fails or is unavailable."""
        import re
        
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["summary", "overview", "stats", "statistics"]):
            return ParsedQuery("get_summary", {}, [], 0.8)
        
        elif any(word in question_lower for word in ["overdue", "past due", "late"]):
            return ParsedQuery("find_overdue", {}, [], 0.8)
        
        elif any(word in question_lower for word in ["how many", "count", "number of"]):
           
            value_patterns = [
                (r'(?:less than|under|below)\s*(?:\$)?(\d+(?:,\d{3})*(?:\.\d{2})?)', 'less_than'),
                (r'(?:more than|over|above|greater than)\s*(?:\$)?(\d+(?:,\d{3})*(?:\.\d{2})?)', 'greater_than'),
                (r'(?:equal to|equals?|exactly)\s*(?:\$)?(\d+(?:,\d{3})*(?:\.\d{2})?)', 'equal_to'),
            ]
            
            for pattern, operator in value_patterns:
                match = re.search(pattern, question_lower)
                if match:
                    value = float(match.group(1).replace(',', ''))
                    filters = [{"field": "total", "operator": operator, "value": value}]
                    return ParsedQuery("count_invoices", {"amount": value}, filters, 0.8)
            
           
            detected_vendors = []
            if available_vendors:
                for vendor in available_vendors:
                    if vendor.lower() in question_lower:
                        detected_vendors.append(vendor)
            
            if detected_vendors:
                filters = [{"field": "vendor", "operator": "equals", "value": detected_vendors[0]}]
                return ParsedQuery("count_invoices", {"vendor": detected_vendors[0]}, filters, 0.7)
            else:
                return ParsedQuery("count_invoices", {}, [], 0.6)
        
        elif any(word in question_lower for word in ["total", "sum", "amount"]):
            detected_vendors = []
            if available_vendors:
                for vendor in available_vendors:
                    if vendor.lower() in question_lower:
                        detected_vendors.append(vendor)
            
            if detected_vendors:
                filters = [{"field": "vendor", "operator": "equals", "value": detected_vendors[0]}]
                return ParsedQuery("sum_total", {"vendor": detected_vendors[0]}, filters, 0.7)
            else:
                return ParsedQuery("sum_total", {}, [], 0.6)
            detected_vendors = []
            if available_vendors:
                for vendor in available_vendors:
                    if vendor.lower() in question_lower:
                        detected_vendors.append(vendor)
            
            if detected_vendors:
                filters = [{"field": "vendor", "operator": "equals", "value": detected_vendors[0]}]
                return ParsedQuery("sum_total", {"vendor": detected_vendors[0]}, filters, 0.7)
            else:
                return ParsedQuery("sum_total", {}, [], 0.6)
        
        elif any(word in question_lower for word in ["show", "list", "display"]):
            detected_vendors = []
            if available_vendors:
                for vendor in available_vendors:
                    if vendor.lower() in question_lower:
                        detected_vendors.append(vendor)
            
            if detected_vendors:
                filters = [{"field": "vendor", "operator": "equals", "value": detected_vendors[0]}]
                return ParsedQuery("list_invoices", {"vendor": detected_vendors[0]}, filters, 0.7)
            else:
                return ParsedQuery("list_invoices", {}, [], 0.6)
        
        return ParsedQuery("unknown", {}, [], 0.0)

    def _fallback_parse(self, question: str) -> ParsedQuery:
        """Simple keyword-based fallback when LLM fails."""
        if "summary" in question.lower():
            return ParsedQuery("get_summary", {}, [], 0.6)
        elif "overdue" in question.lower():
            return ParsedQuery("find_overdue", {}, [], 0.6)
        else:
            return ParsedQuery("unknown", {}, [], 0.0)


class IntelligentQueryEngine:
    """Query engine that uses smart parsing + pandas execution."""
    
    def __init__(self, invoices_df):
        self.df = invoices_df
        self.parser = SmartQueryParser()
        
        self.known_vendors = list(self.df['vendor'].dropna().str.title().unique())
    
    def answer_question(self, question: str) -> str:
        """
        Answer natural language question about invoices.
        
        This is the main interface - LLM understands the question,
        pandas executes the query locally.
        """
        # Parse question using LLM
        parsed = self.parser.parse(question, self.known_vendors)
        
        if parsed.confidence < 0.5:
            return self._handle_unclear_question(question, parsed)
        
        try:
            return self._execute_parsed_query(parsed)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return f"I understood your question but couldn't execute it: {e}"
    
    def _execute_parsed_query(self, parsed: ParsedQuery) -> str:
        """Execute the parsed query using pandas operations."""
        
        if parsed.action == "count_invoices":
            return self._count_invoices(parsed.entities, parsed.filters)
        elif parsed.action == "sum_total":
            return self._sum_total(parsed.entities, parsed.filters)
        elif parsed.action == "list_invoices":
            return self._list_invoices(parsed.entities, parsed.filters)
        elif parsed.action == "get_summary":
            return self._get_summary()
        elif parsed.action == "find_overdue":
            return self._find_overdue()
        else:
            return f"I understood you want to '{parsed.action}' but I don't know how to do that yet."
    
    def _count_invoices(self, entities: Dict, filters: List) -> str:
        """Count invoices based on extracted entities and filters."""
        filtered_df = self._apply_filters(self.df, filters)
        count = len(filtered_df)
        
        description = self._build_filter_description(filters)
        return f"Found {count} invoices{description}"
    
    def _apply_filters(self, df, filters: List) -> 'pd.DataFrame':
        """Apply filters to dataframe based on parsed conditions."""
        filtered_df = df.copy()
        
        for filter_condition in filters:
            field = filter_condition.get('field')
            operator = filter_condition.get('operator') 
            value = filter_condition.get('value')
            
            if field == 'vendor' and operator == 'equals':
                filtered_df = filtered_df[
                    filtered_df['vendor'].str.lower().str.contains(
                        str(value).lower(), na=False
                    )
                ]
            elif field == 'total' and operator == 'less_than':
                filtered_df = filtered_df[filtered_df['total'] < float(value)]
            elif field == 'total' and operator == 'greater_than':
                filtered_df = filtered_df[filtered_df['total'] > float(value)]
            
        return filtered_df
    
    def _build_filter_description(self, filters: List) -> str:
        """Build human-readable description of applied filters."""
        if not filters:
            return ""
        
        descriptions = []
        for f in filters:
            if f.get('field') == 'vendor':
                descriptions.append(f" from {f.get('value')}")
            elif f.get('field') == 'total':
                op = f.get('operator', '')
                val = f.get('value', '')
                if op == 'less_than':
                    descriptions.append(f" with amount less than ${val}")
                elif op == 'greater_than':
                    descriptions.append(f" with amount greater than ${val}")
        
        return "".join(descriptions)
    
    def _handle_unclear_question(self, question: str, parsed: ParsedQuery) -> str:
        """Handle questions that couldn't be parsed with high confidence."""
        return f"""I'm not quite sure what you're asking. Here's what I understood:
        
Your question: "{question}"
My interpretation: {parsed.action}
Confidence: {parsed.confidence:.1%}

Could you rephrase your question? For example:
• "How many invoices from Microsoft?"
• "What's the total amount from Amazon?"
• "Show me overdue invoices"
• "Summary of all invoices"
"""


# Usage example:
def create_intelligent_chatbot(invoices_data):
    """Create an intelligent chatbot that can handle any invoice question."""
    import pandas as pd
    
    df = pd.DataFrame(invoices_data)
    # Normalize data
    df['vendor'] = df['vendor'].fillna('').astype(str)
    df['total'] = pd.to_numeric(df['total'], errors='coerce')
    
    return IntelligentQueryEngine(df)


# Example usage:
if __name__ == "__main__":
    # Test with sample data
    sample_invoices = [
        {"vendor": "Microsoft", "total": 3100, "due_date": "2025-09-10"},
        {"vendor": "Amazon", "total": 2450, "due_date": "2025-09-05"},
        {"vendor": "Apple", "total": 1300, "due_date": "2025-10-01"}
    ]
    
    chatbot = create_intelligent_chatbot(sample_invoices)
    
    # This should now work without hardcoded patterns:
    print(chatbot.answer_question("How many invoices are due from Microsoft to Reliance?"))
    print(chatbot.answer_question("What's our spend with tech companies this quarter?"))
    print(chatbot.answer_question("Any invoices over 2000 bucks?"))
