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
            'total_by_vendor': [
                r'what is the total (?:value|amount) (?:of invoices? )?from (.+?)(?:\?|$)',
                r'total (?:value|amount) (?:of invoices? )?from (.+?)(?:\?|$)',
                r'sum invoices? from (.+?)(?:\?|$)',
                r'how much (?:do we owe|is owed) to (.+?)(?:\?|$)'
            ],
            'total_by_date': [
                r'total (?:value|amount) (?:of invoices? )?(?:from|between) (.+?) to (.+?)(?:\?|$)',
                r'sum invoices? (?:from|between) (.+?) to (.+?)(?:\?|$)'
            ],
            'invoices_by_vendor': [
                r'show invoices? from (.+?)(?:\?|$)',
                r'list invoices? from (.+?)(?:\?|$)',
                r'invoices? from (.+?)(?:\?|$)'
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
    
    def parse(self, question: str) -> QueryIntent:
        question = question.lower().strip()
        
        for action, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, question, re.IGNORECASE)
                if match:
                    parameters = self._extract_parameters(action, match)
                    return QueryIntent(action=action, parameters=parameters, confidence=0.9)
        
        return QueryIntent(action='unknown', parameters={}, confidence=0.0)
    
    def _extract_parameters(self, action: str, match) -> Dict[str, Union[str, int]]:
        groups = match.groups()
        
        if action == 'count_due':
            return {'days': int(groups[0])}
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
