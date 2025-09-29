import datetime as dt
import logging
import pandas as pd
from typing import Any, Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


class InvoiceQueryError(Exception):
    """Custom exception for invoice query errors."""
    pass


class InvoiceQueryEngine:
    """High-performance invoice query engine using pandas for local data processing."""
    
    def __init__(self, invoices: List[Dict[str, Any]]) -> None:
        """
        Initialize the query engine with invoice data.
        
        Args:
            invoices: List of invoice dictionaries
        """
        if not isinstance(invoices, list):
            raise InvoiceQueryError("Invoices must be a list")
        
        try:
            self.df = pd.DataFrame(invoices)
            self._normalize_data()
            logger.info(f"Initialized query engine with {len(self.df)} invoices")
        except Exception as e:
            logger.error(f"Failed to initialize query engine: {e}")
            raise InvoiceQueryError(f"Failed to initialize with invoice data: {e}")
    
    def _normalize_data(self) -> None:
        """Normalize and validate invoice data for efficient querying."""
        if self.df.empty:
            logger.warning("No invoice data to normalize")
            return
        
        try:
            # Normalize vendor names
            self.df['vendor'] = self.df['vendor'].fillna('').astype(str).str.lower().str.strip()
            
            # Parse and validate dates
            self.df['invoice_date'] = pd.to_datetime(self.df['invoice_date'], errors='coerce')
            self.df['due_date'] = pd.to_datetime(self.df['due_date'], errors='coerce')
            
            # Normalize totals
            self.df['total'] = pd.to_numeric(self.df['total'], errors='coerce').fillna(0)
            
            # Log data quality issues
            invalid_invoice_dates = self.df['invoice_date'].isna().sum()
            invalid_due_dates = self.df['due_date'].isna().sum()
            invalid_totals = (self.df['total'] == 0).sum()
            
            if invalid_invoice_dates > 0:
                logger.warning(f"{invalid_invoice_dates} invoices have invalid invoice dates")
            if invalid_due_dates > 0:
                logger.warning(f"{invalid_due_dates} invoices have invalid due dates")
            if invalid_totals > 0:
                logger.warning(f"{invalid_totals} invoices have invalid or zero totals")
                
        except Exception as e:
            logger.error(f"Data normalization failed: {e}")
            raise InvoiceQueryError(f"Failed to normalize invoice data: {e}")
    
    def count_by_value(self, value: float, comparison: str = 'less_than') -> int:
        """
        Count invoices by value comparison.
        
        Args:
            value: Value threshold to compare against
            comparison: 'less_than' or 'greater_than'
            
        Returns:
            Count of invoices matching the criteria
        """
        if not isinstance(value, (int, float)) or value < 0:
            raise InvoiceQueryError("Value must be a non-negative number")
        
        if comparison not in ['less_than', 'greater_than']:
            raise InvoiceQueryError("Comparison must be 'less_than' or 'greater_than'")
        
        if self.df.empty:
            return 0
        
        try:
            if comparison == 'less_than':
                mask = self.df['total'] < value
            else:  # greater_than
                mask = self.df['total'] > value
            
            result = int(mask.sum())
            logger.debug(f"Found {result} invoices with total {comparison.replace('_', ' ')} ${value:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to count by value: {e}")
            raise InvoiceQueryError(f"Failed to count invoices by value: {e}")
    
    def count_due_in_days(self, days: int) -> int:
        """
        Count invoices due within the specified number of days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            Count of invoices due within the specified timeframe
        """
        if not isinstance(days, int) or days < 0:
            raise InvoiceQueryError("Days must be a non-negative integer")
        
        if self.df.empty:
            return 0
        
        try:
            today = dt.date.today()
            target_date = today + dt.timedelta(days=days)
            
            mask = (
                self.df['due_date'].notna() &
                (self.df['due_date'].dt.date >= today) &
                (self.df['due_date'].dt.date <= target_date)
            )
            result = int(mask.sum())
            logger.debug(f"Found {result} invoices due in next {days} days")
            return result
            
        except Exception as e:
            logger.error(f"Failed to count due invoices: {e}")
            raise InvoiceQueryError(f"Failed to count invoices due in {days} days: {e}")
    
    def total_by_vendor(self, vendor: str) -> float:
        """
        Calculate total invoice amount for a specific vendor.
        
        Args:
            vendor: Vendor name (case-insensitive partial matching)
            
        Returns:
            Total amount for the vendor
        """
        if not isinstance(vendor, str):
            raise InvoiceQueryError("Vendor must be a string")
        
        if self.df.empty:
            return 0.0
        
        try:
            vendor_lower = vendor.lower().strip()
            if not vendor_lower:
                raise InvoiceQueryError("Vendor name cannot be empty")
                
            mask = self.df['vendor'].str.contains(vendor_lower, case=False, na=False, regex=False)
            result = float(self.df.loc[mask, 'total'].sum())
            logger.debug(f"Total for vendor '{vendor}': ${result:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to calculate vendor total: {e}")
            raise InvoiceQueryError(f"Failed to calculate total for vendor '{vendor}': {e}")
    
    def total_by_date_range(self, start_date: str, end_date: str) -> float:
        """
        Calculate total invoice amount for a date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Total amount for the date range
        """
        if self.df.empty:
            return 0.0
        
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            
            if start > end:
                raise InvoiceQueryError("Start date cannot be after end date")
            
            mask = (
                self.df['invoice_date'].notna() &
                (self.df['invoice_date'] >= start) &
                (self.df['invoice_date'] <= end)
            )
            result = float(self.df.loc[mask, 'total'].sum())
            logger.debug(f"Total for date range {start_date} to {end_date}: ${result:.2f}")
            return result
            
        except pd.errors.ParserError as e:
            raise InvoiceQueryError(f"Invalid date format. Use YYYY-MM-DD: {e}")
        except Exception as e:
            logger.error(f"Failed to calculate date range total: {e}")
            raise InvoiceQueryError(f"Failed to calculate total for date range: {e}")
    
    def get_invoices_by_vendor(self, vendor: str) -> List[Dict[str, Any]]:
        """
        Get all invoices for a specific vendor.
        
        Args:
            vendor: Vendor name (case-insensitive partial matching)
            
        Returns:
            List of invoice dictionaries
        """
        if not isinstance(vendor, str):
            raise InvoiceQueryError("Vendor must be a string")
            
        if self.df.empty:
            return []
        
        try:
            vendor_lower = vendor.lower().strip()
            if not vendor_lower:
                raise InvoiceQueryError("Vendor name cannot be empty")
                
            mask = self.df['vendor'].str.contains(vendor_lower, case=False, na=False, regex=False)
            result_df = self.df.loc[mask].copy()
            
            if result_df.empty:
                return []
            
            # Format dates for output
            result_df['invoice_date'] = result_df['invoice_date'].dt.strftime('%Y-%m-%d')
            result_df['due_date'] = result_df['due_date'].dt.strftime('%Y-%m-%d')
            
            result = result_df.to_dict('records')
            logger.debug(f"Found {len(result)} invoices for vendor '{vendor}'")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get vendor invoices: {e}")
            raise InvoiceQueryError(f"Failed to get invoices for vendor '{vendor}': {e}")
    
    def get_overdue_invoices(self) -> List[Dict[str, Any]]:
        """
        Get all overdue invoices.
        
        Returns:
            List of overdue invoice dictionaries
        """
        if self.df.empty:
            return []
        
        try:
            today = dt.date.today()
            mask = (
                self.df['due_date'].notna() &
                (self.df['due_date'].dt.date < today)
            )
            result_df = self.df.loc[mask].copy()
            
            if result_df.empty:
                return []
            
            # Format dates for output
            result_df['invoice_date'] = result_df['invoice_date'].dt.strftime('%Y-%m-%d')
            result_df['due_date'] = result_df['due_date'].dt.strftime('%Y-%m-%d')
            
            result = result_df.to_dict('records')
            logger.debug(f"Found {len(result)} overdue invoices")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get overdue invoices: {e}")
            raise InvoiceQueryError(f"Failed to get overdue invoices: {e}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for all invoices.
        
        Returns:
            Dictionary with summary statistics
        """
        if self.df.empty:
            return {
                'total_invoices': 0,
                'total_value': 0.0,
                'unique_vendors': 0,
                'overdue_count': 0,
                'average_invoice_value': 0.0
            }
        
        try:
            today = dt.date.today()
            overdue_count = int((
                self.df['due_date'].notna() &
                (self.df['due_date'].dt.date < today)
            ).sum())
            
            total_value = float(self.df['total'].sum())
            total_invoices = len(self.df)
            unique_vendors = int(self.df['vendor'].nunique())
            average_value = total_value / total_invoices if total_invoices > 0 else 0.0
            
            result = {
                'total_invoices': total_invoices,
                'total_value': total_value,
                'unique_vendors': unique_vendors,
                'overdue_count': overdue_count,
                'average_invoice_value': average_value
            }
            
            logger.debug(f"Generated summary stats: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate summary stats: {e}")
            raise InvoiceQueryError(f"Failed to generate summary statistics: {e}")
