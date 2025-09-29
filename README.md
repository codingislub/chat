# Invoice Chatbot 

Ask questions about your invoices in plain English and get instant answers. No complex commands, no waiting.

## ✨ What Makes It Special

### 🧠 **Understands Natural Language**
- "How many invoices are less than $2000?"
- "Show me overdue invoices from Microsoft"
- "What's our total spend with tech vendors?"

Uses AI to understand your questions, then processes everything locally for speed. Works great even without an API key.

### 🚀 **Lightning Fast**
Sub-10ms responses on thousands of invoices. Local pandas processing means no waiting for external APIs.

### 💬 **Beautiful Interface**
Colored output, emojis, and clear formatting that's actually pleasant to use.

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/codingislub/chat.git
cd chat
python -m venv .venv

# Activate environment
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

### Usage

```bash
# Interactive mode
python -m src.chatbot --data data/invoices.json

# Single question
python -m src.chatbot --data data/invoices.json --q "How many invoices are overdue?"

# Debug mode
python -m src.chatbot --data data/invoices.json --verbose
```

## 📖 Example Questions

**Get Overview:**
```bash
python -m src.chatbot --data data/invoices.json --q "summary of all invoices"
```

**Filter & Count:**
```bash
# Small invoices
--q "how many invoices less than 2000"

# Vendor activity
--q "count invoices from Microsoft"

# Large tickets
--q "invoices over 5000"
```

**Analyze Spending:**
```bash
# Vendor totals
--q "total from Amazon"

# Overdue payments
--q "show me overdue invoices"
```

## 🗂️ Data Format

Simple JSON with your invoice data:

```json
[
  {
    "invoice_number": "INV-001",
    "vendor": "Microsoft Corporation",
    "amount": 2500.00,
    "due_date": "2025-10-15",
    "status": "pending"
  }
]
```

**Required:** `amount`, `vendor`  
**Optional:** `invoice_number`, `customer`, `due_date`, `issue_date`, `status`

## ⚙️ Configuration (Optional)

Create `.env` for enhanced AI understanding:

```env
OPENAI_API_KEY=your_key_here
OPENAI_TEXT_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

**No API key?** No problem – smart fallback patterns work perfectly.

## 📈 Performance

- **Speed:** < 10ms per query
- **Scale:** Tested with 10,000+ invoices
- **Efficiency:** Minimal memory usage
- **Smart:** AI only for understanding, not data processing

## 🆘 Troubleshooting

**"No OpenAI API key found"**  
Just a warning – everything works fine with the fallback system.

**"Invalid JSON format"**  
Validate with: `python -m json.tool your_file.json`

**Slow performance?**  
Use `--verbose` to diagnose. System is optimized – slowness usually means memory issues.

## 🤝 Contributing

Fork → Make changes → Pull request. We'd love your help!
