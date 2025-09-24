import argparse
import json
from typing import List

from src.llm import extract_invoice_fields_from_image
from src.models import Invoice


def parse_invoices(image_urls: List[str]) -> List[Invoice]:
	invoices: List[Invoice] = []
	for url in image_urls:
		fields = extract_invoice_fields_from_image(url)
		invoices.append(Invoice(**fields))
	return invoices


def main() -> None:
	parser = argparse.ArgumentParser(description="Parse invoice images into structured JSON")
	parser.add_argument("--urls", nargs="*", help="Image URLs to parse", required=False)
	parser.add_argument(
		"--out",
		dest="out",
		type=str,
		default="data/invoices.json",
		help="Path to write JSON",
	)
	args = parser.parse_args()

	urls = args.urls or [
		"https://templates.invoicehome.com/invoice-template-us-classic-blue-750px.png",
		"https://templates.invoicehome.com/invoice-template-us-classic-green-750px.png",
	]

	invoices = parse_invoices(urls)
	data = [inv.model_dump() for inv in invoices]

	with open(args.out, "w", encoding="utf-8") as f:
		json.dump(data, f, indent=2)
	print(f"Wrote {len(data)} invoices to {args.out}")


if __name__ == "__main__":
	main()
