### Invoice Chatbot (Small Demo)

A tiny Python project that parses 2–3 invoice images into structured JSON and answers questions about them via an LLM.

#### 1) Setup

- Python 3.10+
- Create and activate a virtual environment (recommended)
- Install deps:

```bash
pip install -r requirements.txt
```

- Set your OpenAI API key:

```bash
$env:OPENAI_API_KEY="your_key_here"   # PowerShell
# or
export OPENAI_API_KEY="your_key_here"  # bash
```

Optional: copy `.env.example` to `.env` and set `OPENAI_API_KEY`.

#### 2) Parse invoices (optional)

By default the chatbot uses `data/invoices.sample.json`. To parse the example invoice images with a vision model and write `data/invoices.json`:

```bash
python -m src.parse_invoices --out data/invoices.json \
  --urls https://templates.invoicehome.com/invoice-template-us-classic-blue-750px.png \
         https://templates.invoicehome.com/invoice-template-us-classic-green-750px.png
```

This calls the LLM to extract:
- vendor
- invoice_number
- invoice_date (YYYY-MM-DD)
- due_date (YYYY-MM-DD)
- total (number)

#### 3) Run the chatbot

Using the sample data:

```bash
python -m src.chatbot --data data/invoices.sample.json --q "How many invoices are due in the next 7 days?"
```

Interactive mode:

```bash
python -m src.chatbot --data data/invoices.sample.json
```

If you generated `data/invoices.json`, you can point to it:

```bash
python -m src.chatbot --data data/invoices.json
```

Examples to try:
- "How many invoices are due in the next 7 days?"
- "What is the total value of the invoice from Amazon?"

#### Notes
- Uses lightweight rule-based answers for common queries; falls back to the LLM with the invoices JSON as context.
- Keep dataset tiny (2–3 invoices) as requested. For more accuracy, you could add a PDF-to-image step or use OCR before the LLM.
# small-chatbot
