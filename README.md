# Invoice Chatbot

A scalable Python chatbot that parses invoice images and answers data questions using efficient query processing instead of LLM context dumping.

## Architecture

- **Invoice Parser**: OpenAI Vision API extracts structured data from images
- **Query Engine**: Pandas-based data operations for efficient querying  
- **Query Parser**: Regex-based natural language understanding
- **Chatbot**: CLI interface with structured responses

## Key Features

- ✅ **Scalable**: Handles hundreds/thousands of invoices efficiently
- ✅ **Precise**: Direct data calculations vs LLM approximation
- ✅ **Fast**: No API calls for data questions
- ✅ **Structured**: Clear separation of parsing, querying, and presentation

## Setup

### Prerequisites
- Python 3.10+
- OpenAI API key

### Installation
```bash
pip install -r requirements.txt
```

### Environment Setup
```bash
# PowerShell
$env:OPENAI_API_KEY="your_key_here"

# Bash
export OPENAI_API_KEY="your_key_here"
```

## Usage

### 1. Parse Invoice Images (Optional)

Parse invoice images into structured JSON:

```bash
python -m src.parse_invoices --out data/invoices.json \
  --urls https://templates.invoicehome.com/invoice-template-us-classic-blue-750px.png \
         https://templates.invoicehome.com/invoice-template-us-classic-green-750px.png
```

**Extracts:**
- `vendor` - Company name
- `invoice_number` - Invoice identifier  
- `invoice_date` - Date in YYYY-MM-DD format
- `due_date` - Due date in YYYY-MM-DD format
- `total` - Invoice amount

### 2. Query the Chatbot

#### Single Question
```bash
python -m src.chatbot --data data/invoices.sample.json --q "How many invoices are due in the next 7 days?"
```

#### Interactive Mode
```bash
python -m src.chatbot --data data/invoices.sample.json
```

### Supported Query Types

| Query Type | Example | Response |
|------------|---------|----------|
| **Count Due** | "How many invoices are due in the next 7 days?" | "1 invoices are due in the next 7 days." |
| **Total by Vendor** | "What is the total value from Amazon?" | "The total value of invoices from Amazon is $2450.00." |
| **Overdue** | "Show me overdue invoices" | "Found 2 overdue invoices: ..." |
| **Summary** | "Summary of all invoices" | "Invoice Summary: Total invoices: 3, Total value: $6849.99..." |
| **List by Vendor** | "Show invoices from Microsoft" | "Found 1 invoices from Microsoft: ..." |
| **Date Range** | "Total invoices from 2025-01-01 to 2025-01-31" | "The total value of invoices from 2025-01-01 to 2025-01-31 is $X.XX." |

## Technical Implementation

### Query Processing Pipeline
1. **Parse**: Regex patterns extract intent and parameters
2. **Query**: Pandas DataFrame operations for data filtering/aggregation  
3. **Format**: Structured response generation

### Data Operations (Pandas-based)
```python
class InvoiceQueryEngine:
    def count_due_in_days(self, days: int) -> int
    def total_by_vendor(self, vendor: str) -> float  
    def get_overdue_invoices(self) -> List[Dict]
    def get_summary_stats(self) -> Dict[str, Any]
```

### Performance Characteristics
- **Scalable**: O(n) operations with pandas, not O(tokens) with LLM
- **Memory Efficient**: DataFrame operations vs large context windows
- **Precise**: Exact calculations vs LLM approximation

## Project Structure

```
src/
├── llm.py              # OpenAI API helpers
├── models.py           # Pydantic data models  
├── query_engine.py     # Pandas data operations
├── query_parser.py     # Natural language parsing
├── parse_invoices.py   # Image parsing script
└── chatbot.py          # Main CLI interface

data/
└── invoices.sample.json # Sample dataset
```

## Key Technical Decisions

### 1. Scalable Data Querying
- **Problem**: Initial approach dumped all invoice JSON into LLM context (doesn't scale)
- **Solution**: Implemented pandas DataFrame with efficient data operations
- **Result**: Handles hundreds/thousands of invoices without performance issues

### 2. Structured Query Processing  
- **Query Parser**: Uses regex patterns to extract intent and parameters
- **Query Engine**: Pandas-based operations for filtering, aggregation, date calculations
- **Benefits**: Fast, precise answers without API calls for data questions

## Dependencies

- `openai>=1.40.0` - Vision and text models
- `pandas>=2.2.2` - Data operations
- `pydantic>=2.8.2` - Data validation
- `python-dotenv>=1.0.1` - Environment management
- `rich>=13.7.1` - CLI formatting
- `requests>=2.32.3` - HTTP requests
# chat
