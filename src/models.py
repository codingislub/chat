from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from pydantic.types import Decimal


class Invoice(BaseModel):
    """Invoice model with validation and type safety."""
    
    vendor: Optional[str] = Field(None, description="Invoice vendor/company name")
    invoice_number: Optional[str] = Field(None, description="Unique invoice identifier")
    invoice_date: Optional[str] = Field(None, description="Invoice date in YYYY-MM-DD format")
    due_date: Optional[str] = Field(None, description="Payment due date in YYYY-MM-DD format")
    total: Optional[float] = Field(None, description="Total invoice amount", ge=0)
    
    @field_validator('invoice_date', 'due_date')
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate date format is YYYY-MM-DD."""
        if v is None:
            return v
        try:
            # Validate date format by parsing it
            from datetime import datetime
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError(f'Date must be in YYYY-MM-DD format, got: {v}')
    
    @field_validator('total')
    @classmethod
    def validate_total(cls, v: Optional[float]) -> Optional[float]:
        """Validate total is non-negative."""
        if v is not None and v < 0:
            raise ValueError('Total amount cannot be negative')
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            date: lambda dt: dt.isoformat(),
        }
        validate_assignment = True
