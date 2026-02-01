import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "service_account.json"
PARENT_FOLDER_ID = "1s3wFZnf_HdtJezONnzUiEF8cYGB3p974"

def manage_google_file(filename: str, content: str):
    """
    Creates or updates a Google Sheet in the Freebot_Workspace folder.
    Call this when the user wants to log, record, or save info to a file.
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
        gc = gspread.authorize(creds)
        
        try:
            sheet = gc.open(filename)
            worksheet = sheet.sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            sheet = gc.create(filename)
            # Move to target folder
            drive_service = build('drive', 'v3', credentials=creds)
            file = drive_service.files().get(fileId=sheet.id, fields='parents').execute()
            prev_parents = ",".join(file.get('parents', []))
            drive_service.files().update(fileId=sheet.id, addParents=PARENT_FOLDER_ID, removeParents=prev_parents).execute()
            worksheet = sheet.sheet1
            worksheet.append_row(["Timestamp", "Entry"])

        worksheet.append_row([str(datetime.datetime.now()), content])
        return f"Successfully updated '{filename}' in Drive."
    except Exception as e:
        return f"Drive Error: {str(e)}"
