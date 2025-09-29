import re
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass


@dataclass
class QueryIntent:
    action: str
    parameters: Dict[str, Union[str, int, float]]
    confidence: float


class QueryParser:
    def __init__(self):
        self.patterns = {
            'count_due': [
                r'how many invoices? are due (?:in the )?next (\d+) days?',
                r'count invoices? due (?:in the )?next (\d+) days?',
                r'invoices? due (?:in the )?next (\d+) days?',
                r'how many invoices? are due in (\d+) days?',
                r'count invoices? due in (\d+) days?',
                r'invoices? due in (\d+) days?'
            ],
            'count_by_value': [
                r'how many invoices? (?:have (?:value|total|amount) )?(?:are )?(?:less than|under|below) \$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'count invoices? (?:with (?:value|total|amount) )?(?:less than|under|below) \$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'invoices? (?:with (?:value|total|amount) )?(?:less than|under|below) \$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'how many invoices? (?:have (?:value|total|amount) )?(?:are )?(?:greater than|over|above) \$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'count invoices? (?:with (?:value|total|amount) )?(?:greater than|over|above) \$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'invoices? (?:with (?:value|total|amount) )?(?:greater than|over|above) \$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
            ],
            'total_by_vendor': [
                r'what.s the total (?:value|amount)?\s*(?:of invoices?)?\s*from (.+?)(?:\?|$)',
                r'what is the total (?:value|amount)?\s*(?:of invoices?)?\s*from (.+?)(?:\?|$)',
                r'total (?:value|amount)?\s*(?:of invoices?)?\s*from (.+?)(?:\?|$)',
                r'sum (?:invoices?)?\s*from (.+?)(?:\?|$)',
                r'how much (?:do we owe|is owed) to (.+?)(?:\?|$)',
                r'(?:what.s|whats) the total from (.+?)(?:\?|$)'
            ],
            'total_by_date': [
                r'total (?:value|amount) (?:of invoices? )?(?:from|between) (.+?) to (.+?)(?:\?|$)',
                r'sum invoices? (?:from|between) (.+?) to (.+?)(?:\?|$)'
            ],
            'invoices_by_vendor': [
                r'show invoices? from (.+?)(?:\?|$)',
                r'list invoices? from (.+?)(?:\?|$)',
                r'invoices? from (.+?)(?:\?|$)',
                r'how many invoices? (?:are )?(?:due )?from (.+?)(?:\?|$)',
                r'count invoices? from (.+?)(?:\?|$)'
            ],
            'overdue': [
                r'overdue invoices?',
                r'invoices? that are overdue',
                r'past due invoices?'
            ],
            'summary': [
                r'summary',
                r'overview',
                r'total invoices?',
                r'how many invoices? (?:do we have|are there)'
            ]
        }
        
        # Keywords for fuzzy matching
        self.vendor_keywords = ['from', 'by', 'vendor', 'company']
        self.count_keywords = ['how many', 'count', 'number of']
        self.total_keywords = ['total', 'sum', 'amount', 'value']
        self.due_keywords = ['due', 'overdue', 'past due']
    
    def parse(self, question: str) -> QueryIntent:
        question = question.lower().strip()
        
        # First try exact pattern matching
        for action, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, question, re.IGNORECASE)
                if match:
                    parameters = self._extract_parameters(action, match)
                    return QueryIntent(action=action, parameters=parameters, confidence=0.9)
        
        # If no exact match, try fuzzy logic
        return self._fuzzy_parse(question)
    
    def _fuzzy_parse(self, question: str) -> QueryIntent:
        """Attempt to understand the question using fuzzy logic and keyword detection."""
        words = question.split()
        
        # Check for count + vendor patterns
        if any(keyword in question for keyword in self.count_keywords):
            # Look for vendor names (common company names)
            potential_vendors = self._extract_potential_vendors(question)
            if potential_vendors:
                # If it mentions "due" it's probably asking for count of vendor invoices
                if any(keyword in question for keyword in self.due_keywords + ['invoices']):
                    return QueryIntent(
                        action='invoices_by_vendor', 
                        parameters={'vendor': potential_vendors[0]}, 
                        confidence=0.7
                    )
        
        # Check for total + vendor patterns  
        if any(keyword in question for keyword in self.total_keywords):
            potential_vendors = self._extract_potential_vendors(question)
            if potential_vendors:
                return QueryIntent(
                    action='total_by_vendor',
                    parameters={'vendor': potential_vendors[0]},
                    confidence=0.7
                )
        
        # Fallback: suggest clarification
        return QueryIntent(action='unknown', parameters={}, confidence=0.0)
    
    def _extract_potential_vendors(self, question: str) -> List[str]:
        """Extract potential vendor names from the question."""
        # Common company names and indicators
        common_companies = [
            'microsoft', 'amazon', 'google', 'apple', 'ibm', 'oracle', 
            'adobe', 'salesforce', 'netflix', 'spotify', 'uber', 'airbnb',
            'tesla', 'meta', 'twitter', 'linkedin', 'slack', 'zoom', 
            'dropbox', 'github', 'reliance'
        ]
        
        found_vendors = []
        for company in common_companies:
            if company in question.lower():
                found_vendors.append(company.title())
        
        # Also look for capitalized words that might be company names
        words = question.split()
        for word in words:
            if word[0].isupper() and len(word) > 2:
                # Skip common words
                if word.lower() not in ['how', 'many', 'what', 'from', 'to', 'are', 'the']:
                    found_vendors.append(word)
        
        return found_vendors
    
    def parse(self, question: str) -> QueryIntent:
        question = question.lower().strip()
        
        for action, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, question, re.IGNORECASE)
                if match:
                    parameters = self._extract_parameters(action, match)
                    return QueryIntent(action=action, parameters=parameters, confidence=0.9)
        
        return QueryIntent(action='unknown', parameters={}, confidence=0.0)
    
    def _extract_parameters(self, action: str, match) -> Dict[str, Union[str, int, float]]:
        groups = match.groups()
        
        if action == 'count_due':
            return {'days': int(groups[0])}
        elif action == 'count_by_value':
            # Parse value and determine comparison type from original query
            value_str = groups[0].replace(',', '')  # Remove commas
            value = float(value_str)
            
            # Determine if it's less than or greater than based on the matched pattern
            query_lower = match.string.lower()
            if any(word in query_lower for word in ['less than', 'under', 'below']):
                return {'value': value, 'comparison': 'less_than'}
            elif any(word in query_lower for word in ['greater than', 'over', 'above']):
                return {'value': value, 'comparison': 'greater_than'}
            else:
                return {'value': value, 'comparison': 'less_than'}  # Default
        elif action == 'total_by_vendor':
            vendor = groups[0].strip().rstrip('?')
            return {'vendor': vendor}
        elif action == 'total_by_date':
            return {'start_date': groups[0].strip(), 'end_date': groups[1].strip()}
        elif action == 'invoices_by_vendor':
            vendor = groups[0].strip().rstrip('?')
            return {'vendor': vendor}
        elif action in ['overdue', 'summary']:
            return {}
        
        return {}
