import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build

# === CONFIGURATION ===
SERVICE_ACCOUNT_FILE = "service_account.json"
PARENT_FOLDER_ID = "1s3wFZnf_HdtJezONnzUiEF8cYGB3p974"

def get_drive_service():
    """Internal helper to connect to Google Drive API."""
    scope = ["https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    return build('drive', 'v3', credentials=creds)

def manage_google_file(filename: str, content: str):
    """
    Creates a new Google Sheet or updates an existing one in the Freebot_Workspace folder.
    Gemini will call this when the user wants to log, record, or save data to a specific file.
    """
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
        gc = gspread.authorize(creds)
        drive_service = get_drive_service()

        try:
            # 1. Try to open the file if it already exists
            sheet = gc.open(filename)
            worksheet = sheet.sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            # 2. Create the file if it doesn't exist
            sheet = gc.create(filename)
            
            # 3. Move the new file into your Freebot_Workspace folder
            file = drive_service.files().get(fileId=sheet.id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents', []))
            drive_service.files().update(
                fileId=sheet.id, 
                addParents=PARENT_FOLDER_ID, 
                removeParents=previous_parents, 
                fields='id, parents'
            ).execute()
            
            worksheet = sheet.sheet1
            # Add a header row for new files
            worksheet.append_row(["Timestamp", "Entry Content"])

        # 4. Append the new data
        worksheet.append_row([str(datetime.datetime.now()), content])
        return f"✅ Successfully updated '{filename}' in your Freebot_Workspace folder with: {content}"

    except Exception as e:
        return f"❌ Google Drive Error: {str(e)}"
