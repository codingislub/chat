# Invoice Chatbot

Ever wished you could just ask questions about your invoices in plain English? This chatbot does exactly that! Upload invoice images, ask questions like "How many invoices are due this week?" or "What's our total with Amazon?", and get instant answers.

## What it does

This chatbot takes invoice images and turns them into a searchable database. Instead of manually going through piles of invoices, you can just ask questions naturally and get quick, accurate answers.

**Key features:**
- 📸 **Parse invoices from images** - Just upload invoice photos and it extracts all the important details
- 💬 **Ask questions naturally** - "Show me overdue invoices" or "What's our total with Microsoft?"
- ⚡ **Lightning fast** - No waiting for AI responses, everything is calculated instantly
- 📊 **Handles lots of data** - Works great whether you have 10 invoices or 10,000

## Getting Started

### What you'll need
- Python 3.10 or newer
- An OpenAI API key (for parsing invoice images)

### Installation

First, install the required packages:

```bash
pip install -r requirements.txt
```

Then set up your OpenAI API key:

```bash
# On Windows (PowerShell)
$env:OPENAI_API_KEY="your_key_here"

# On Mac/Linux
export OPENAI_API_KEY="your_key_here"
```

## How to use it

### Step 1: Parse invoice images (optional)

If you have invoice images you want to process, run this command:

```bash
python -m src.parse_invoices --out data/invoices.json \
  --urls https://example.com/invoice1.png \
         https://example.com/invoice2.png
```

This will extract:
- Company name (vendor)
- Invoice number
- Invoice date
- Due date
- Total amount

### Step 2: Ask questions!

You can ask questions in two ways:

**Single question:**
```bash
python -m src.chatbot --data data/invoices.sample.json --q "How many invoices are due in 7 days?"
```

**Interactive chat:**
```bash
python -m src.chatbot --data data/invoices.sample.json
```

## What questions can you ask?

The chatbot understands lots of different ways to ask the same thing. Here are some examples:

### Due dates
- "How many invoices are due in 7 days?"
- "Invoices due in 2 days?"
- "Count invoices due next week"

### Totals by vendor
- "What's the total from Amazon?"
- "How much do we owe Microsoft?"
- "Sum all invoices from Google"

### Overdue invoices
- "Show me overdue invoices"
- "What invoices are past due?"
- "List overdue bills"

### Summary info
- "Summary of all invoices"
- "How many invoices do we have?"
- "Give me an overview"

### Specific invoices
- "Show invoices from Amazon"
- "List all Microsoft invoices"

### Date ranges
- "Total invoices from 2024-01-01 to 2024-01-31"

## Example conversation

Here's what a typical session looks like:

```
$ python -m src.chatbot --data data/invoices.sample.json

Type a question (Ctrl+C to exit). Examples:
- How many invoices are due in the next 7 days?
- What is the total value of invoices from Amazon?
- Show me overdue invoices
- Summary of all invoices

You: How many invoices are due in 2 days?
Bot: 0 invoices are due in the next 2 days.

You: What's the total from Amazon?
Bot: The total value of invoices from Amazon is $2450.00.

You: Show me overdue invoices
Bot: Found 2 overdue invoices:
- Amazon (INV-0012): $2450.00
- Microsoft (INV-0043): $3100.00

You: Summary
Bot: Invoice Summary:
- Total invoices: 3
- Total value: $6849.99
- Unique vendors: 3
- Overdue invoices: 2
```

## How it works under the hood

I built this because I was tired of manually searching through invoice data. The original approach of dumping everything into an AI prompt was slow and expensive, so I redesigned it to be much more efficient.

**The magic happens in three steps:**

1. **Parse your question** - Uses smart pattern matching to understand what you're asking
2. **Query the data** - Uses pandas (a fast data processing library) to find the answer
3. **Format the response** - Gives you a clean, readable answer

This approach is way faster than sending everything to an AI model every time you ask a question. Plus, it's more accurate since it's doing actual calculations instead of AI approximations.

## Project structure

```
src/
├── llm.py              # Handles OpenAI API calls
├── models.py           # Data structure definitions
├── query_engine.py     # The brain that processes your questions
├── query_parser.py     # Understands natural language
├── parse_invoices.py   # Converts images to data
└── chatbot.py          # Main interface

data/
└── invoices.sample.json # Sample data to try it out
```

## Why I built it this way

**Problem:** The first version was slow and expensive because it sent all invoice data to an AI model for every question.

**Solution:** I switched to using pandas (a data processing library) for calculations and only use AI for parsing invoice images. This makes it:
- Much faster (no API calls for data questions)
- More accurate (exact calculations vs AI guesses)
- Cheaper to run
- Able to handle thousands of invoices without breaking a sweat

## Dependencies

- `openai` - For parsing invoice images
- `pandas` - For fast data processing
- `pydantic` - For data validation
- `python-dotenv` - For environment variables
- `rich` - For pretty command line output
- `requests` - For downloading images

## Try it out!

The easiest way to get started is with the sample data:

```bash
python -m src.chatbot --data data/invoices.sample.json --q "Summary"
```

This will give you a quick overview of what the chatbot can do. From there, you can either use your own invoice data or try parsing some invoice images!
