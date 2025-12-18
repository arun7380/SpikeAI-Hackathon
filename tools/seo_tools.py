import pandas as pd
import logging

logger = logging.getLogger(__name__)

class SEOTools:
    """
    Collection of data processing functions for the SEO Agent.
    Operates on the raw data (list of dicts) fetched from Google Sheets.
    """

    @staticmethod
    def filter_pages(data: list, filters: list):
        """
        Applies multiple conditional filters to the SEO data.
        Example filter: {"column": "Title 1", "operator": "length_gt", "value": 60}
        """
        if not data:
            return []
            
        df = pd.DataFrame(data)
        
        for f in filters:
            col = f['column']
            op = f['operator']
            val = f['value']
            
            if op == "not_contains":
                df = df[~df[col].astype(str).str.contains(val, na=False)]
            elif op == "length_gt":
                df = df[df[col].astype(str).str.len() > val]
            elif op == "equals":
                df = df[df[col] == val]
            elif op == "is_missing":
                df = df[df[col].isna() | (df[col] == "")]
                
        return df.to_dict(orient='records')

    @staticmethod
    def get_audit_summary(data: list):
        """
        Aggregates data to provide high-level SEO health metrics.
        Fulfills Tier 2 'Grouping' and 'Aggregations' requirement.
        """
        if not data:
            return {}

        df = pd.DataFrame(data)
        
        summary = {
            "total_urls": len(df),
            "non_https": len(df[~df['Address'].str.startswith('https', na=False)]),
            "missing_titles": len(df[df['Title 1'].isna()]),
            "overly_long_titles": len(df[df['Title 1'].str.len() > 60]),
            "indexable_count": len(df[df['Indexability'] == 'Indexable'])
        }
        
        return summary

    @staticmethod
    def group_by_status(data: list):
        """
        Groups URLs by their HTTP status code.
        """
        if not data:
            return {}

        df = pd.DataFrame(data)
        # Groups and counts occurrences for each status code
        return df.groupby('Status Code').size().to_dict()