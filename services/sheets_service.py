import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from core.config import settings

class SheetsService:
    def __init__(self):
        """
        Initializes the Google Sheets API client.
        Requirement: Use credentials.json from the project root.
        """
        # Define the scope for reading spreadsheets
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        
        # Load credentials from the root-level JSON file
        self.creds = Credentials.from_service_account_file(
            settings.GA4_CREDENTIALS_PATH, 
            scopes=self.scopes
        )
        self.service = build('sheets', 'v4', credentials=self.creds)

    def get_spreadsheet_data(self, spreadsheet_id: str, range_name: str = "A:Z"):
        """
        Fetches data from a Google Sheet and returns a Pandas DataFrame.
        """
        try:
            # Call the Sheets API
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id, 
                range=range_name
            ).execute()
            
            values = result.get('values', [])

            if not values:
                return pd.DataFrame()

            # The first row is typically the header (Address, Title, Indexability, etc.)
            df = pd.DataFrame(values[1:], columns=values[0])
            
            # Sanitization: Ensure column names are lowercase and underscores for easier AI logic
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            return df

        except Exception as e:
            # Handle edge cases like invalid spreadsheet IDs or permission errors
            return {"error": str(e), "status": "failed"}

    def get_seo_metrics(self, df):
        """
        Example helper to perform basic Tier 2 logic like grouping or filtering.
        """
        if df.empty:
            return "No data available."
            
        # Example: Group by indexability status as required by Tier 2
        if 'indexability' in df.columns:
            return df['indexability'].value_counts().to_dict()
        
        return "Indexability column not found."