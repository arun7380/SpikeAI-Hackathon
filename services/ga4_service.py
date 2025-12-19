import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from core.config import settings

class SheetsService:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        # Load credentials directly from the file we placed in root
        self.creds = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_APPLICATION_CREDENTIALS, scopes=self.scopes)
        self.service = build('sheets', 'v4', credentials=self.creds)

    def get_spreadsheet_data(self, spreadsheet_id: str = None):
        sid = spreadsheet_id if spreadsheet_id else settings.DEFAULT_SHEET_ID
        range_name = 'A1:Z1000' # Scans the first 1000 rows
        
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(spreadsheetId=sid, range=range_name).execute()
            values = result.get('values', [])
            
            if not values:
                return pd.DataFrame()
            
            return pd.DataFrame(values[1:], columns=values[0])
        except Exception as e:
            print(f"Sheets Error: {e}")
            return pd.DataFrame()