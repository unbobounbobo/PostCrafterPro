"""
Helper script to create Google Sheets for PostCrafterPro

This script will:
1. Create a new "SNS投稿_下書き" (Draft) sheet
2. Create a new "SNS投稿_完成版" (Published) sheet
3. Display the sheet IDs to add to .env file
"""
import os
from dotenv import load_dotenv
from app.services.sheets_service import SheetsService

# Load environment variables
load_dotenv()


def main():
    print("=" * 60)
    print("PostCrafterPro - Google Sheets Setup")
    print("=" * 60)
    print()

    # Check if Google credentials exist
    if not os.path.exists('service_account.json') and not os.path.exists('credentials.json'):
        print("❌ Error: Google credentials not found!")
        print()
        print("Please add one of the following files to the project root:")
        print("  - service_account.json (for service account)")
        print("  - credentials.json (for OAuth)")
        print()
        return

    try:
        # Initialize sheets service
        print("Connecting to Google Sheets...")
        service = SheetsService()
        print("✅ Connected successfully!")
        print()

        # Check existing sheets
        print("Checking existing sheets...")
        print(f"  Draft Sheet ID: {os.getenv('GOOGLE_SHEETS_DRAFT_ID') or 'Not set'}")
        print(f"  Published Sheet ID: {os.getenv('GOOGLE_SHEETS_PUBLISHED_ID') or 'Not set'}")
        print(f"  Analytics Sheet ID: {os.getenv('GOOGLE_SHEETS_ANALYTICS_ID') or 'Not set'}")
        print()

        # Ask user what to create
        print("What would you like to do?")
        print("1. Create Draft Sheet only")
        print("2. Create Published Sheet only")
        print("3. Create both Draft and Published Sheets")
        print("4. Exit")
        print()

        choice = input("Enter your choice (1-4): ").strip()

        if choice == '1' or choice == '3':
            print()
            print("Creating Draft Sheet...")
            draft_id = service.create_draft_sheet()
            print(f"✅ Draft Sheet created successfully!")
            print(f"   Sheet ID: {draft_id}")
            print()

        if choice == '2' or choice == '3':
            print()
            print("Creating Published Sheet...")
            published_id = service.create_published_sheet()
            print(f"✅ Published Sheet created successfully!")
            print(f"   Sheet ID: {published_id}")
            print()

        if choice in ['1', '2', '3']:
            print("=" * 60)
            print("✅ Setup Complete!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("1. Open your .env file")
            print("2. Add the following sheet IDs:")
            print()

            if choice == '1' or choice == '3':
                print(f"   GOOGLE_SHEETS_DRAFT_ID={draft_id if choice in ['1', '3'] else 'your-draft-sheet-id'}")

            if choice == '2' or choice == '3':
                print(f"   GOOGLE_SHEETS_PUBLISHED_ID={published_id if choice in ['2', '3'] else 'your-published-sheet-id'}")

            print()
            print("3. Restart the application")
            print()

        elif choice == '4':
            print("Exiting...")
        else:
            print("Invalid choice. Exiting...")

    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
