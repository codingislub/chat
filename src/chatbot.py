import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.query_engine import InvoiceQueryEngine, InvoiceQueryError
from src.query_parser import QueryParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rich console for better output
console = Console()

DEFAULT_DATA_PATH = os.getenv("INVOICES_JSON", "data/invoices.sample.json")


class InvoiceChatbotError(Exception):
    """Custom exception for chatbot errors."""
    pass


def load_invoices(path: str) -> List[Dict[str, Any]]:
    """
    Load invoice data from JSON file with error handling.
    
    Args:
        path: Path to the JSON file
        
    Returns:
        List of invoice dictionaries
        
    Raises:
        InvoiceChatbotError: If file cannot be loaded
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise InvoiceChatbotError(f"Invoice data file not found: {path}")
    
    if not file_path.suffix.lower() == '.json':
        raise InvoiceChatbotError(f"Expected JSON file, got: {file_path.suffix}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise InvoiceChatbotError("Invoice data must be a list of objects")
        
        logger.info(f"Loaded {len(data)} invoices from {path}")
        return data
        
    except json.JSONDecodeError as e:
        raise InvoiceChatbotError(f"Invalid JSON in file {path}: {e}")
    except Exception as e:
        raise InvoiceChatbotError(f"Failed to load invoice data from {path}: {e}")


def answer_question(question: str, query_engine: InvoiceQueryEngine) -> str:
    """
    Process a natural language question about invoices.
    
    Args:
        question: User's question in natural language
        query_engine: Initialized query engine
        
    Returns:
        Answer string
    """
    if not question or not question.strip():
        return "Please ask a question about your invoices."
    
    try:
        parser = QueryParser()
        intent = parser.parse(question.strip())
        
        if intent.confidence < 0.5:
            # Try to provide more helpful suggestions based on what we detected
            suggestions = [
                "• Invoices due in X days",
                "• Total amounts by vendor", 
                "• Overdue invoices",
                "• Invoice summary/overview",
                "• Count invoices by value (e.g., 'less than $2000')"
            ]
            
            # If we detected potential vendors, give specific examples
            if 'vendor' in intent.parameters:
                vendor = intent.parameters['vendor']
                suggestions.extend([
                    f"• 'What's the total from {vendor}?'",
                    f"• 'Show invoices from {vendor}'",
                    f"• 'How many invoices from {vendor}?'"
                ])
            
            suggestion_text = "\n".join(suggestions)
            return f"I'm not quite sure what you're asking. Here are some questions I can answer:\n{suggestion_text}"
        
        action = intent.action
        params = intent.parameters
        
        # Route to appropriate query method
        if action == 'count_due':
            days = params.get('days', 7)
            count = query_engine.count_due_in_days(days)
            return f"📅 {count} invoices are due in the next {days} days."
        
        elif action == 'count_by_value':
            value = params.get('value', 0)
            comparison = params.get('comparison', 'less_than')
            count = query_engine.count_by_value(value, comparison)
            
            if comparison == 'less_than':
                return f"💰 {count} invoices have values less than ${value:,.2f}"
            else:
                return f"💰 {count} invoices have values greater than ${value:,.2f}"
        
        elif action == 'total_by_vendor':
            vendor = params.get('vendor', '').strip()
            if not vendor:
                return "Please specify a vendor name."
            total = query_engine.total_by_vendor(vendor)
            return f"💰 Total value of invoices from {vendor.title()}: ${total:,.2f}"
        
        elif action == 'total_by_date':
            start_date = params.get('start_date', '').strip()
            end_date = params.get('end_date', '').strip()
            if not start_date or not end_date:
                return "Please specify both start and end dates (YYYY-MM-DD format)."
            total = query_engine.total_by_date_range(start_date, end_date)
            return f"💰 Total value from {start_date} to {end_date}: ${total:,.2f}"
        
        elif action == 'invoices_by_vendor':
            vendor = params.get('vendor', '').strip()
            if not vendor:
                return "Please specify a vendor name."
            invoices = query_engine.get_invoices_by_vendor(vendor)
            if not invoices:
                return f"❌ No invoices found from {vendor.title()}."
            
            result = f"📋 Found {len(invoices)} invoices from {vendor.title()}:\n"
            for inv in invoices:
                inv_num = inv.get('invoice_number', 'N/A')
                amount = inv.get('total', 0)
                due_date = inv.get('due_date', 'N/A')
                result += f"  • {inv_num}: ${amount:,.2f} (due {due_date})\n"
            return result.strip()
        
        elif action == 'overdue':
            invoices = query_engine.get_overdue_invoices()
            if not invoices:
                return "✅ No overdue invoices found!"
            
            result = f"⚠️  Found {len(invoices)} overdue invoices:\n"
            total_overdue = 0
            for inv in invoices:
                vendor = inv.get('vendor', 'N/A').title()
                inv_num = inv.get('invoice_number', 'N/A')
                amount = inv.get('total', 0)
                due_date = inv.get('due_date', 'N/A')
                total_overdue += amount
                result += f"  • {vendor} ({inv_num}): ${amount:,.2f} (due {due_date})\n"
            result += f"\n💰 Total overdue amount: ${total_overdue:,.2f}"
            return result.strip()
        
        elif action == 'summary':
            stats = query_engine.get_summary_stats()
            return f"""📊 Invoice Summary:
• Total invoices: {stats['total_invoices']:,}
• Total value: ${stats['total_value']:,.2f}
• Average invoice: ${stats['average_invoice_value']:,.2f}
• Unique vendors: {stats['unique_vendors']:,}
• Overdue invoices: {stats['overdue_count']:,}"""
        
        return "I couldn't process that request. Please try rephrasing your question."
        
    except InvoiceQueryError as e:
        logger.error(f"Query error: {e}")
        return f"❌ Error processing your question: {e}"
    except Exception as e:
        logger.error(f"Unexpected error answering question: {e}")
        return "❌ An unexpected error occurred. Please try again or check your data."


def print_welcome_message() -> None:
    """Display welcome message with examples."""
    welcome_text = Text("Invoice Chatbot", style="bold blue")
    examples = """Ask questions about your invoices in natural language:

💡 Examples:
  • How many invoices are due in 7 days?
  • What's the total from Amazon?
  • Show me overdue invoices
  • Summary of all invoices
  • List invoices from Microsoft

⌨️  Type your questions below (Ctrl+C to exit)"""
    
    console.print(Panel(examples, title=welcome_text, border_style="blue"))


def main() -> None:
    """Main chatbot interface."""
    parser = argparse.ArgumentParser(
        description="AI-powered chatbot for invoice queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.chatbot --data data/invoices.json --q "How many invoices are due?"
  python -m src.chatbot --data data/invoices.json  # Interactive mode
        """
    )
    parser.add_argument(
        "--data", 
        default=DEFAULT_DATA_PATH, 
        help=f"Path to invoices JSON file (default: {DEFAULT_DATA_PATH})"
    )
    parser.add_argument(
        "--q", "--question",
        dest="question", 
        help="Single question to ask (for non-interactive mode)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load invoice data
        console.print(f"📂 Loading invoice data from: {args.data}")
        invoices = load_invoices(args.data)
        
        # Initialize query engine
        query_engine = InvoiceQueryEngine(invoices)
        console.print(f"✅ Ready! Loaded {len(invoices)} invoices")
        
    except InvoiceChatbotError as e:
        console.print(f"❌ {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        logger.exception("Unexpected error during initialization")
        sys.exit(1)
    
    # Handle single question mode
    if args.question:
        try:
            answer = answer_question(args.question, query_engine)
            console.print(f"\n🤖 {answer}")
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
            sys.exit(1)
        return
    
    # Interactive mode
    print_welcome_message()
    
    while True:
        try:
            question = console.input("\n[bold green]You:[/bold green] ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'bye']:
                console.print("👋 Goodbye!", style="blue")
                break
            
            answer = answer_question(question, query_engine)
            console.print(f"[bold blue]Bot:[/bold blue] {answer}")
            
        except KeyboardInterrupt:
            console.print("\n\n👋 Goodbye!", style="blue")
            break
        except EOFError:
            console.print("\n\n👋 Goodbye!", style="blue")
            break
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
            logger.exception("Error in interactive mode")


if __name__ == "__main__":
    main()
