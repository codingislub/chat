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
from src.smart_query_parser import SmartQueryParser, ParsedQuery

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
    Process a natural language question about invoices using smart LLM parsing.
    
    Args:
        question: User's question in natural language
        query_engine: Initialized query engine
        
    Returns:
        Answer string
    """
    if not question or not question.strip():
        return "Please ask a question about your invoices."
    
    try:
        # Get known vendors from the dataset for better context
        known_vendors = []
        if hasattr(query_engine, 'df') and not query_engine.df.empty:
            known_vendors = query_engine.df['vendor'].dropna().str.title().unique().tolist()
        
        # Use smart LLM-powered parsing
        parser = SmartQueryParser()
        parsed_query = parser.parse(question.strip(), known_vendors)
        
        if parsed_query.confidence < 0.5:
            return _handle_unclear_question(question, parsed_query, known_vendors)
        
        # Execute the parsed query using our existing query engine
        return _execute_smart_query(parsed_query, query_engine)
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return f"❌ Sorry, I encountered an error processing your question: {e}"


def _handle_unclear_question(question: str, parsed_query: ParsedQuery, known_vendors: List[str]) -> str:
    """Handle questions that couldn't be parsed with high confidence."""
    suggestions = [
        "💡 Here are some questions I can definitely answer:",
        "",
        "📊 **Summary & Statistics**",
        "• 'Summary of all invoices'",
        "• 'How many invoices do we have?'",
        "",
        "🏢 **Vendor Queries**",
        "• 'What's the total from [vendor]?'",
        "• 'Show me invoices from [vendor]'",
        "• 'How many invoices from [vendor]?'",
        "",
        "💰 **Amount-Based Queries**", 
        "• 'How many invoices less than $2000?'",
        "• 'Show invoices over $5000'",
        "",
        "📅 **Date-Based Queries**",
        "• 'How many invoices are due in 30 days?'",
        "• 'Show me overdue invoices'",
    ]
    
    # Add specific vendor examples if we have them
    if known_vendors:
        suggestions.extend([
            "",
            f"🎯 **Try with your vendors**: {', '.join(known_vendors[:5])}",
            f"• Example: 'What's our total with {known_vendors[0]}?'"
        ])
    
    # Add what we understood for debugging
    if parsed_query.action != 'unknown':
        suggestions.extend([
            "",
            f"🤔 **What I understood**: {parsed_query.action}",
            f"**Confidence**: {parsed_query.confidence:.1%}",
            f"**Entities found**: {parsed_query.entities}"
        ])
    
    return "\n".join(suggestions)


def _execute_smart_query(parsed_query: ParsedQuery, query_engine: InvoiceQueryEngine) -> str:
    """Execute a parsed query using the existing query engine methods."""
    
    action = parsed_query.action
    entities = parsed_query.entities
    filters = parsed_query.filters
    
    try:
        if action == "count_invoices":
            return _handle_count_invoices(entities, filters, query_engine)
        
        elif action == "sum_total":
            return _handle_sum_total(entities, filters, query_engine)
        
        elif action == "list_invoices":
            return _handle_list_invoices(entities, filters, query_engine)
        
        elif action == "get_summary":
            stats = query_engine.get_summary_stats()
            return f"""� **Invoice Summary**:
• Total invoices: {stats['total_invoices']:,}
• Total value: ${stats['total_value']:,.2f}
• Average invoice: ${stats['average_invoice_value']:,.2f}
• Unique vendors: {stats['unique_vendors']:,}
• Overdue invoices: {stats['overdue_count']:,}"""
        
        elif action == "find_overdue":
            invoices = query_engine.get_overdue_invoices()
            if not invoices:
                return "✅ No overdue invoices found!"
            
            total_overdue = sum(inv.get('total', 0) for inv in invoices)
            result = f"⚠️  Found {len(invoices)} overdue invoices:\n"
            for inv in invoices[:10]:  # Limit to first 10
                vendor = inv.get('vendor', 'N/A').title()
                inv_num = inv.get('invoice_number', 'N/A')
                amount = inv.get('total', 0)
                due_date = inv.get('due_date', 'N/A')
                result += f"  • {vendor} ({inv_num}): ${amount:,.2f} (due {due_date})\n"
            
            if len(invoices) > 10:
                result += f"  ... and {len(invoices) - 10} more\n"
            result += f"\n💰 Total overdue amount: ${total_overdue:,.2f}"
            return result.strip()
        
        else:
            return f"I understood you want to '{action}' but I'm not sure how to do that yet. Can you try rephrasing?"
            
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return f"❌ I understood your question but couldn't execute it: {e}"


def _handle_count_invoices(entities: Dict, filters: List, query_engine: InvoiceQueryEngine) -> str:
    """Handle counting invoices with various filters."""
    
    # Check for vendor filter
    vendor = entities.get('vendor')
    if vendor:
        invoices = query_engine.get_invoices_by_vendor(vendor)
        return f"📊 Found {len(invoices)} invoices from {vendor.title()}"
    
    # Check for amount filters
    for filter_item in filters:
        if filter_item.get('field') == 'total':
            operator = filter_item.get('operator')
            value = float(filter_item.get('value', 0))
            
            if operator == 'less_than':
                count = query_engine.count_by_value(value, 'less_than')
                return f"💰 {count} invoices have values less than ${value:,.2f}"
            elif operator == 'greater_than':
                count = query_engine.count_by_value(value, 'greater_than') 
                return f"💰 {count} invoices have values greater than ${value:,.2f}"
    
    # Default: count all invoices
    stats = query_engine.get_summary_stats()
    return f"📊 Total invoices: {stats['total_invoices']:,}"


def _handle_sum_total(entities: Dict, filters: List, query_engine: InvoiceQueryEngine) -> str:
    """Handle summing totals with various filters."""
    
    vendor = entities.get('vendor')
    if vendor:
        total = query_engine.total_by_vendor(vendor)
        return f"💰 Total value from {vendor.title()}: ${total:,.2f}"
    
    # Default: total all invoices
    stats = query_engine.get_summary_stats()
    return f"💰 Total value of all invoices: ${stats['total_value']:,.2f}"


def _handle_list_invoices(entities: Dict, filters: List, query_engine: InvoiceQueryEngine) -> str:
    """Handle listing specific invoices."""
    
    vendor = entities.get('vendor')
    if vendor:
        invoices = query_engine.get_invoices_by_vendor(vendor)
        if not invoices:
            return f"❌ No invoices found from {vendor.title()}"
        
        result = f"📋 Found {len(invoices)} invoices from {vendor.title()}:\n"
        for inv in invoices[:10]:  # Limit display
            inv_num = inv.get('invoice_number', 'N/A')
            amount = inv.get('total', 0)
            due_date = inv.get('due_date', 'N/A')
            result += f"  • {inv_num}: ${amount:,.2f} (due {due_date})\n"
        
        if len(invoices) > 10:
            result += f"  ... and {len(invoices) - 10} more invoices"
        
        return result.strip()
    
    return "Please specify which invoices you'd like to see (e.g., 'from Amazon')"


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
