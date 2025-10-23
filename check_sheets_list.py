"""
Check all sheets in analytics spreadsheet
"""
import sys
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# UTF-8 output for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Initialize Google Sheets connection
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'service_account.json', scope
    )
except FileNotFoundError:
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json', scope
    )

client = gspread.authorize(creds)

# Get analytics spreadsheet
analytics_id = os.getenv('GOOGLE_SHEETS_ANALYTICS_ID')
print(f"Analytics Spreadsheet ID: {analytics_id}\n")

spreadsheet = client.open_by_key(analytics_id)

print("=== スプレッドシート内の全シート ===\n")
worksheets = spreadsheet.worksheets()

for i, sheet in enumerate(worksheets, 1):
    print(f"{i}. シート名: {sheet.title}")
    print(f"   行数: {sheet.row_count}")
    print(f"   列数: {sheet.col_count}")

    # Get first row (headers)
    try:
        headers = sheet.row_values(1)
        print(f"   カラム数: {len(headers)}")
        print(f"   最初の5カラム: {headers[:5]}")
    except:
        print("   ヘッダー取得失敗")

    # Get row count with data
    try:
        all_values = sheet.get_all_values()
        data_rows = len([row for row in all_values if any(row)])
        print(f"   データ行数: {data_rows}")
    except:
        pass

    print()
