import pandas as pd
import io
import requests
from core.config import settings

class SheetsService:
    def __init__(self):
        # Use the public spreadsheet URL from settings
        # The hackathon sheet must be set to 'Anyone with the link can view'
        self.raw_url = settings.SEO_SHEET_URL

    def get_spreadsheet_data(self):
        """
        Ingests the live Screaming Frog export data from Google Sheets.
        Returns a list of dictionaries (one per row).
        """
        # 1. Transform the standard Edit URL into a CSV Export URL
        # e.g., .../edit#gid=1438203274 -> .../export?format=csv&gid=1438203274
        csv_url = self.raw_url.replace('/edit', '/export?format=csv')
        
        try:
            # 2. Fetch the live data
            response = requests.get(csv_url)
            response.raise_for_status()

            # 3. Parse with Pandas for robust schema handling
            df = pd.read_csv(io.StringIO(response.text))
            
            # Clean column names (remove leading/trailing spaces)
            df.columns = df.columns.str.strip()

            # 4. Convert to list of dicts for the AI agent to process
            return df.to_dict(orient='records')

        except Exception as e:
            # Handle empty/sparse datasets gracefully as per requirements
            print(f"Error fetching SEO data: {str(e)}")
            return []

    def get_headers(self):
        """
        Helper to get column names for schema-safe agent planning.
        """
        data = self.get_spreadsheet_data()
        if data:
            return list(data[0].keys())
        return []