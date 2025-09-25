import datetime as dt
import pandas as pd
from typing import Any, Dict, List, Optional, Union


class InvoiceQueryEngine:
    def __init__(self, invoices: List[Dict[str, Any]]):
        self.df = pd.DataFrame(invoices)
        self._normalize_data()
    
    def _normalize_data(self):
        if self.df.empty:
            return
        
        self.df['vendor'] = self.df['vendor'].fillna('').astype(str).str.lower()
        self.df['invoice_date'] = pd.to_datetime(self.df['invoice_date'], errors='coerce')
        self.df['due_date'] = pd.to_datetime(self.df['due_date'], errors='coerce')
        self.df['total'] = pd.to_numeric(self.df['total'], errors='coerce').fillna(0)
    
    def count_due_in_days(self, days: int) -> int:
        if self.df.empty:
            return 0
        
        today = dt.date.today()
        target_date = today + dt.timedelta(days=days)
        
        mask = (
            self.df['due_date'].notna() &
            (self.df['due_date'].dt.date >= today) &
            (self.df['due_date'].dt.date <= target_date)
        )
        return int(mask.sum())
    
    def total_by_vendor(self, vendor: str) -> float:
        if self.df.empty:
            return 0.0
        
        vendor_lower = vendor.lower()
        mask = self.df['vendor'].str.contains(vendor_lower, case=False, na=False)
        return float(self.df.loc[mask, 'total'].sum())
    
    def total_by_date_range(self, start_date: str, end_date: str) -> float:
        if self.df.empty:
            return 0.0
        
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            mask = (
                self.df['invoice_date'].notna() &
                (self.df['invoice_date'] >= start) &
                (self.df['invoice_date'] <= end)
            )
            return float(self.df.loc[mask, 'total'].sum())
        except:
            return 0.0
    
    def get_invoices_by_vendor(self, vendor: str) -> List[Dict[str, Any]]:
        if self.df.empty:
            return []
        
        vendor_lower = vendor.lower()
        mask = self.df['vendor'].str.contains(vendor_lower, case=False, na=False)
        result_df = self.df.loc[mask].copy()
        
        result_df['invoice_date'] = result_df['invoice_date'].dt.strftime('%Y-%m-%d')
        result_df['due_date'] = result_df['due_date'].dt.strftime('%Y-%m-%d')
        
        return result_df.to_dict('records')
    
    def get_overdue_invoices(self) -> List[Dict[str, Any]]:
        if self.df.empty:
            return []
        
        today = dt.date.today()
        mask = (
            self.df['due_date'].notna() &
            (self.df['due_date'].dt.date < today)
        )
        result_df = self.df.loc[mask].copy()
        
        result_df['invoice_date'] = result_df['invoice_date'].dt.strftime('%Y-%m-%d')
        result_df['due_date'] = result_df['due_date'].dt.strftime('%Y-%m-%d')
        
        return result_df.to_dict('records')
    
    def get_summary_stats(self) -> Dict[str, Any]:
        if self.df.empty:
            return {
                'total_invoices': 0,
                'total_value': 0.0,
                'unique_vendors': 0,
                'overdue_count': 0
            }
        
        today = dt.date.today()
        overdue_count = int((
            self.df['due_date'].notna() &
            (self.df['due_date'].dt.date < today)
        ).sum())
        
        return {
            'total_invoices': len(self.df),
            'total_value': float(self.df['total'].sum()),
            'unique_vendors': int(self.df['vendor'].nunique()),
            'overdue_count': overdue_count
        }
