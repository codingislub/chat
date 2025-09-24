from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class Invoice(BaseModel):
	vendor: Optional[str]
	invoice_number: Optional[str]
	invoice_date: Optional[str]
	due_date: Optional[str]
	total: Optional[float]
