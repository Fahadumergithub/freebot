import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials

def log_to_sheet(data_to_log: str):
    """
    Logs a piece of professional information or a record into the Google Sheet.
    Use this when the user mentions recording, logging, or saving data to a sheet.
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Freebot_Records").sheet1
        sheet.append_row([str(datetime.datetime.now()), data_to_log])
        return f"Successfully logged: {data_to_log}"
    except Exception as e:
        return f"Error logging to sheet: {e}"
