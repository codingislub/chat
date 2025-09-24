import argparse
import datetime as dt
import json
import os
from typing import Any, Dict, List

from openai import OpenAI

DEFAULT_DATA_PATH = os.getenv("INVOICES_JSON", "data/invoices.sample.json")
MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")


def load_invoices(path: str) -> List[Dict[str, Any]]:
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def answer_with_rules(question: str, invoices: List[Dict[str, Any]]) -> str:
	q = question.lower()
	# Simple rule: due in next 7 days
	if "due" in q and ("next 7 days" in q or "next seven days" in q):
		today = dt.date.today()
		in_7 = today + dt.timedelta(days=7)
		count = 0
		for inv in invoices:
			due = inv.get("due_date")
			if not due:
				continue
			try:
				d = dt.date.fromisoformat(due)
			except Exception:
				continue
			if today <= d <= in_7:
				count += 1
		return f"{count} invoices are due in the next 7 days."
	# Simple rule: total value for a vendor
	if "total" in q and ("from" in q or "for" in q):
		# naive vendor extract after "from" or "for"
		vendor = None
		for token in ["from", "for"]:
			if token in q:
				vendor = q.split(token, 1)[1].strip().strip("? .!")
				break
		if vendor:
			total = 0.0
			for inv in invoices:
				v = (inv.get("vendor") or "").lower()
				if vendor in v:
					t = inv.get("total") or 0
					try:
						total += float(t)
					except Exception:
						pass
			return f"The total value of invoices from {vendor.title()} is {total:.2f}."
	return "RULES_NO_ANSWER"


def answer_with_llm(question: str, invoices: List[Dict[str, Any]]) -> str:
	client = OpenAI()
	context_json = json.dumps(invoices)
	system = (
		"You answer questions about invoices based only on the provided JSON. "
		"If the answer is unknown from the JSON, say you cannot find it."
	)
	user = (
		"Here is JSON of invoices: " + context_json + "\n" +
		"Question: " + question + "\n" +
		"Return a short, direct answer."
	)
	resp = client.chat.completions.create(
		model=MODEL,
		messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
		temperature=0.0,
	)
	return resp.choices[0].message.content.strip()


def main() -> None:
	parser = argparse.ArgumentParser(description="Chatbot for answering invoice questions")
	parser.add_argument("--data", default=DEFAULT_DATA_PATH, help="Path to invoices JSON")
	parser.add_argument("--q", dest="question", default=None, help="Single question to ask")
	args = parser.parse_args()

	invoices = load_invoices(args.data)
	if args.question:
		question = args.question
		ans = answer_with_rules(question, invoices)
		if ans == "RULES_NO_ANSWER":
			ans = answer_with_llm(question, invoices)
		print(ans)
		return

	print("Type a question (Ctrl+C to exit). Examples:")
	print("- How many invoices are due in the next 7 days?")
	print("- What is the total value of the invoice from Amazon?")
	while True:
		try:
			q = input("You: ").strip()
			if not q:
				continue
			ans = answer_with_rules(q, invoices)
			if ans == "RULES_NO_ANSWER":
				ans = answer_with_llm(q, invoices)
			print(f"Bot: {ans}")
		except KeyboardInterrupt:
			print("\nBye!")
			break


if __name__ == "__main__":
	main()
