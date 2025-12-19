"""
tools/seo_tools.py - Logic for processing Screaming Frog audit data.
"""

# Common Screaming Frog columns identified from standard exports
SEO_COLUMNS_MAP = {
    "address": ["address", "url", "u_r_l"],
    "status_code": ["status_code", "status", "code"],
    "indexability": ["indexability", "indexable"],
    "title_length": ["title_1_length", "title_length", "page_title_length"],
    "meta_desc_length": ["meta_description_1_length", "description_length"],
    "h1": ["h1_1", "h1", "heading_1"]
}

SEO_AUDIT_TOOL_SCHEMA = {
    "name": "analyze_seo_audit",
    "description": "Analyze technical SEO data from a Screaming Frog export.",
    "parameters": {
        "type": "object",
        "properties": {
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
                "description": "Conditional logic to apply to the audit data (e.g., title_length > 60)."
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
    Standardizes column names to ensure the AI logic works across different exports.
    Handles the 'schema changes safely' requirement.
    """
    new_columns = {}
    for col in df.columns:
        normalized_name = col.lower().replace(" ", "_")
        
        # Check if this column matches one of our known SEO patterns
        for standard_key, aliases in SEO_COLUMNS_MAP.items():
            if normalized_name in aliases:
                new_columns[col] = standard_key
                break
        else:
            new_columns[col] = normalized_name
            
    return df.rename(columns=new_columns)