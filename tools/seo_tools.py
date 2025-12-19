"""
tools/seo_tools.py - Logic for processing Screaming Frog audit data for Sheet 1zzf4ax...
"""
import pandas as pd

# Hardcoded Sheet ID for your SEO Audit
DEFAULT_SHEET_ID = "1zzf4ax_H2WiTBVrJigGjF2Q3Yz-qy2qMCbAMKvl6VEE"

# Common Screaming Frog columns identified from standard exports
SEO_COLUMNS_MAP = {
    "address": ["address", "url", "u_r_l"],
    "status_code": ["status_code", "status", "code"],
    "indexability": ["indexability", "indexable"],
    "indexability_status": ["indexability_status", "indexability_reason"],
    "title_length": ["title_1_length", "title_length", "page_title_length"],
    "meta_desc_length": ["meta_description_1_length", "description_length"],
    "h1": ["h1_1", "h1", "heading_1"]
}

SEO_AUDIT_TOOL_SCHEMA = {
    "name": "analyze_seo_audit",
    "description": f"Analyze technical SEO data from Sheet ID: {DEFAULT_SHEET_ID}.",
    "parameters": {
        "type": "object",
        "properties": {
            "sheet_id": {
                "type": "string", 
                "default": DEFAULT_SHEET_ID,
                "description": "The Google Sheet ID containing the Screaming Frog export."
            },
            "filters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "column": {"type": "string", "description": "The normalized column name (e.g., status_code)"},
                        "operator": {"type": "string", "enum": ["==", "!=", ">", "<", "contains"]},
                        "value": {"type": "string"}
                    }
                },
                "description": "Conditional logic to apply (e.g., title_length > 60)."
            },
            "group_by": {
                "type": "string",
                "description": "Column to group results by (e.g., indexability)."
            },
            "metrics": {
                "type": "array",
                "items": {"type": "string", "enum": ["count", "percentage", "average"]},
                "description": "Aggregations to calculate."
            }
        }
    }
}

def normalize_seo_dataframe(df):
    """
    Standardizes column names to handle schema changes safely.
    Ensures 'Title 1 Length' maps correctly to 'title_length'.
    """
    new_columns = {}
    for col in df.columns:
        # Standardize strings for matching (lowercase, no spaces)
        normalized_name = col.lower().replace(" ", "_")
        
        # Match against known SEO spider column patterns
        for standard_key, aliases in SEO_COLUMNS_MAP.items():
            if normalized_name in aliases:
                new_columns[col] = standard_key
                break
        else:
            new_columns[col] = normalized_name
            
    return df.rename(columns=new_columns)