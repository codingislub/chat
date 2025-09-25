import argparse
import json
import os
from typing import Any, Dict, List

from src.query_engine import InvoiceQueryEngine
from src.query_parser import QueryParser

DEFAULT_DATA_PATH = os.getenv("INVOICES_JSON", "data/invoices.sample.json")


def load_invoices(path: str) -> List[Dict[str, Any]]:
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def answer_question(question: str, query_engine: InvoiceQueryEngine) -> str:
	parser = QueryParser()
	intent = parser.parse(question)
	
	if intent.confidence < 0.5:
		return "I don't understand that question. Try asking about invoices due in X days, total amounts by vendor, or overdue invoices."
	
	action = intent.action
	params = intent.parameters
	
	if action == 'count_due':
		days = params.get('days', 7)
		count = query_engine.count_due_in_days(days)
		return f"{count} invoices are due in the next {days} days."
	
	elif action == 'total_by_vendor':
		vendor = params.get('vendor', '')
		total = query_engine.total_by_vendor(vendor)
		return f"The total value of invoices from {vendor.title()} is ${total:.2f}."
	
	elif action == 'total_by_date':
		start_date = params.get('start_date', '')
		end_date = params.get('end_date', '')
		total = query_engine.total_by_date_range(start_date, end_date)
		return f"The total value of invoices from {start_date} to {end_date} is ${total:.2f}."
	
	elif action == 'invoices_by_vendor':
		vendor = params.get('vendor', '')
		invoices = query_engine.get_invoices_by_vendor(vendor)
		if not invoices:
			return f"No invoices found from {vendor.title()}."
		result = f"Found {len(invoices)} invoices from {vendor.title()}:\n"
		for inv in invoices:
			result += f"- {inv.get('invoice_number', 'N/A')}: ${inv.get('total', 0):.2f} (due {inv.get('due_date', 'N/A')})\n"
		return result.strip()
	
	elif action == 'overdue':
		invoices = query_engine.get_overdue_invoices()
		if not invoices:
			return "No overdue invoices found."
		result = f"Found {len(invoices)} overdue invoices:\n"
		for inv in invoices:
			result += f"- {inv.get('vendor', 'N/A')} ({inv.get('invoice_number', 'N/A')}): ${inv.get('total', 0):.2f}\n"
		return result.strip()
	
	elif action == 'summary':
		stats = query_engine.get_summary_stats()
		return f"""Invoice Summary:
- Total invoices: {stats['total_invoices']}
- Total value: ${stats['total_value']:.2f}
- Unique vendors: {stats['unique_vendors']}
- Overdue invoices: {stats['overdue_count']}"""
	
	return "I couldn't process that request."


def main() -> None:
	parser = argparse.ArgumentParser(description="Chatbot for answering invoice questions")
	parser.add_argument("--data", default=DEFAULT_DATA_PATH, help="Path to invoices JSON")
	parser.add_argument("--q", dest="question", default=None, help="Single question to ask")
	args = parser.parse_args()

	invoices = load_invoices(args.data)
	query_engine = InvoiceQueryEngine(invoices)
	
	if args.question:
		question = args.question
		ans = answer_question(question, query_engine)
		print(ans)
		return

	print("Type a question (Ctrl+C to exit). Examples:")
	print("- How many invoices are due in the next 7 days?")
	print("- What is the total value of invoices from Amazon?")
	print("- Show me overdue invoices")
	print("- Summary of all invoices")
	while True:
		try:
			q = input("You: ").strip()
			if not q:
				continue
			ans = answer_question(q, query_engine)
			print(f"Bot: {ans}")
		except KeyboardInterrupt:
			print("\nBye!")
			break


if __name__ == "__main__":
	main()
