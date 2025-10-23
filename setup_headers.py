"""
Setup headers for Google Sheets
"""
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_headers():
    """Setup headers for draft and published sheets"""

    # Initialize connection
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            'service_account.json', scope
        )
    except FileNotFoundError:
        print("❌ service_account.json not found!")
        return

    client = gspread.authorize(creds)

    # Get spreadsheet ID
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    if not spreadsheet_id:
        print("❌ GOOGLE_SHEETS_SPREADSHEET_ID not set in .env")
        return

    # Open spreadsheet
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"✅ Opened spreadsheet: {spreadsheet.title}")
    except Exception as e:
        print(f"❌ Error opening spreadsheet: {e}")
        return

    # Get sheet names
    draft_name = os.getenv('GOOGLE_SHEETS_DRAFT_SHEET_NAME', '下書き')
    published_name = os.getenv('GOOGLE_SHEETS_PUBLISHED_SHEET_NAME', '完成版')

    # Setup draft sheet headers
    print(f"\n📝 Setting up '{draft_name}' sheet...")
    try:
        draft_sheet = spreadsheet.worksheet(draft_name)

        # Draft headers
        draft_headers = [
            '作成日時', '投稿日', 'URL', '決定事項', '記念日', '補足',
            'R1_案A', 'R1_案B', 'R1_選択', 'R1_改善リクエスト',
            'R2_案A', 'R2_案B', 'R2_選択', 'R2_改善リクエスト',
            'R3_案A', 'R3_案B', 'R3_選択', 'R3_改善リクエスト',
            '最終投稿', '最終文字数', '文字数チェック', 'ラウンド数',
            'Pinecone結果数', '類似投稿数'
        ]

        # Set headers
        draft_sheet.update('A1:X1', [draft_headers])

        # Format headers
        draft_sheet.format('A1:X1', {
            'textFormat': {'bold': True, 'fontSize': 10},
            'backgroundColor': {'red': 0.85, 'green': 0.92, 'blue': 0.95},
            'horizontalAlignment': 'CENTER'
        })

        print(f"   ✅ Headers set for '{draft_name}' ({len(draft_headers)} columns)")

    except gspread.exceptions.WorksheetNotFound:
        print(f"   ⚠️ Sheet '{draft_name}' not found. Please create it first.")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Setup published sheet headers
    print(f"\n📝 Setting up '{published_name}' sheet...")
    try:
        published_sheet = spreadsheet.worksheet(published_name)

        # Published headers
        published_headers = [
            '作成日時', '投稿日', 'URL', '決定事項', '記念日', '補足',
            '最終投稿', '文字数', '文字数チェック', 'ラウンド数',
            'Pinecone結果数', '類似投稿数'
        ]

        # Set headers
        published_sheet.update('A1:L1', [published_headers])

        # Format headers
        published_sheet.format('A1:L1', {
            'textFormat': {'bold': True, 'fontSize': 10},
            'backgroundColor': {'red': 0.85, 'green': 0.92, 'blue': 0.95},
            'horizontalAlignment': 'CENTER'
        })

        print(f"   ✅ Headers set for '{published_name}' ({len(published_headers)} columns)")

    except gspread.exceptions.WorksheetNotFound:
        print(f"   ⚠️ Sheet '{published_name}' not found. Please create it first.")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n🎉 Setup complete!")
    print(f"\n📊 Spreadsheet URL:")
    print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")


if __name__ == '__main__':
    print("=" * 60)
    print("Google Sheets Header Setup")
    print("=" * 60)
    setup_headers()
