"""
Google Sheets integration service for PostCrafterPro
"""
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json


class SheetsService:
    """
    Manage Google Sheets operations for draft, published, and analytics sheets
    """

    def __init__(self):
        """Initialize Google Sheets connection"""
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]

        # Try service account first, fall back to OAuth
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                'service_account.json', self.scope
            )
        except FileNotFoundError:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                'credentials.json', self.scope
            )

        self.client = gspread.authorize(creds)

        # Get spreadsheet configuration
        # Support both single spreadsheet (new) and multiple spreadsheets (legacy)
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        self.draft_sheet_name = os.getenv('GOOGLE_SHEETS_DRAFT_SHEET_NAME', '下書き')
        self.published_sheet_name = os.getenv('GOOGLE_SHEETS_PUBLISHED_SHEET_NAME', '完成版')

        # Legacy support: separate spreadsheet IDs
        self.legacy_draft_id = os.getenv('GOOGLE_SHEETS_DRAFT_ID')
        self.legacy_published_id = os.getenv('GOOGLE_SHEETS_PUBLISHED_ID')

        # Analytics sheet (always separate file)
        self.analytics_sheet_id = os.getenv('GOOGLE_SHEETS_ANALYTICS_ID')

        # Initialize sheet connections
        self._init_sheets()

    def _init_sheets(self):
        """Initialize sheet connections and create if needed"""
        # Try new single spreadsheet approach first
        if self.spreadsheet_id:
            try:
                spreadsheet = self.client.open_by_key(self.spreadsheet_id)

                # Get draft sheet by name
                try:
                    self.draft_sheet = spreadsheet.worksheet(self.draft_sheet_name)
                    print(f"[OK] Connected to draft sheet: '{self.draft_sheet_name}'")
                except gspread.exceptions.WorksheetNotFound:
                    print(f"[WARN] Sheet '{self.draft_sheet_name}' not found in spreadsheet")
                    self.draft_sheet = None

                # Get published sheet by name
                try:
                    self.published_sheet = spreadsheet.worksheet(self.published_sheet_name)
                    print(f"[OK] Connected to published sheet: '{self.published_sheet_name}'")
                except gspread.exceptions.WorksheetNotFound:
                    print(f"[WARN] Sheet '{self.published_sheet_name}' not found in spreadsheet")
                    self.published_sheet = None

            except gspread.exceptions.SpreadsheetNotFound:
                print(f"[ERROR] Spreadsheet not found: {self.spreadsheet_id}")
                self.draft_sheet = None
                self.published_sheet = None

        # Fallback to legacy approach (separate spreadsheet files)
        else:
            # Draft sheet
            if self.legacy_draft_id:
                try:
                    self.draft_sheet = self.client.open_by_key(self.legacy_draft_id).sheet1
                    print(f"[OK] Connected to draft sheet (legacy mode)")
                except gspread.exceptions.SpreadsheetNotFound:
                    print(f"[ERROR] Draft sheet not found: {self.legacy_draft_id}")
                    self.draft_sheet = None
            else:
                self.draft_sheet = None

            # Published sheet
            if self.legacy_published_id:
                try:
                    self.published_sheet = self.client.open_by_key(self.legacy_published_id).sheet1
                    print(f"[OK] Connected to published sheet (legacy mode)")
                except gspread.exceptions.SpreadsheetNotFound:
                    print(f"[ERROR] Published sheet not found: {self.legacy_published_id}")
                    self.published_sheet = None
            else:
                self.published_sheet = None

        # Analytics sheets (always separate file with multiple worksheets)
        if self.analytics_sheet_id:
            try:
                analytics_spreadsheet = self.client.open_by_key(self.analytics_sheet_id)

                # Tweet sheet (投稿別データ)
                try:
                    self.analytics_sheet = analytics_spreadsheet.worksheet('tweet')
                    print(f"[OK] Connected to analytics sheet (tweet)")
                except gspread.exceptions.WorksheetNotFound:
                    self.analytics_sheet = analytics_spreadsheet.sheet1
                    print(f"[OK] Connected to analytics sheet (default)")

                # Day sheet (日次データ)
                try:
                    self.analytics_day_sheet = analytics_spreadsheet.worksheet('day')
                    print(f"[OK] Connected to analytics day sheet")
                except gspread.exceptions.WorksheetNotFound:
                    self.analytics_day_sheet = None
                    print(f"[WARN]  Analytics day sheet not found")

                # Social Dog sheet (フォロワー推移)
                try:
                    self.analytics_followers_sheet = analytics_spreadsheet.worksheet('social_dog1')
                    print(f"[OK] Connected to analytics followers sheet")
                except gspread.exceptions.WorksheetNotFound:
                    self.analytics_followers_sheet = None
                    print(f"[WARN]  Analytics followers sheet not found")

            except gspread.exceptions.SpreadsheetNotFound:
                print(f"[ERROR] Analytics spreadsheet not found: {self.analytics_sheet_id}")
                self.analytics_sheet = None
                self.analytics_day_sheet = None
                self.analytics_followers_sheet = None
        else:
            self.analytics_sheet = None
            self.analytics_day_sheet = None
            self.analytics_followers_sheet = None

    def create_draft_sheet(self, sheet_name="SNS投稿_下書き"):
        """
        Create a new draft sheet with headers

        Args:
            sheet_name: Name of the sheet to create

        Returns:
            str: Sheet ID of the created sheet
        """
        # Create new spreadsheet
        spreadsheet = self.client.create(sheet_name)

        # Get the first worksheet
        worksheet = spreadsheet.sheet1

        # Set headers
        headers = [
            '作成日時', 'URL', '決定事項', '記念日', '補足',
            'R1_案A', 'R1_案B', 'R1_選択',
            'R2_案A', 'R2_案B', 'R2_選択',
            'R3_案A', 'R3_案B', 'R3_選択',
            '改善履歴', 'ステータス'
        ]
        worksheet.append_row(headers)

        # Format headers (bold)
        worksheet.format('A1:P1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })

        print(f"Created draft sheet: {sheet_name}")
        print(f"Sheet ID: {spreadsheet.id}")
        print(f"Please add this ID to .env as GOOGLE_SHEETS_DRAFT_ID")

        return spreadsheet.id

    def create_published_sheet(self, sheet_name="SNS投稿_完成版"):
        """
        Create a new published sheet with headers

        Args:
            sheet_name: Name of the sheet to create

        Returns:
            str: Sheet ID of the created sheet
        """
        # Create new spreadsheet
        spreadsheet = self.client.create(sheet_name)

        # Get the first worksheet
        worksheet = spreadsheet.sheet1

        # Set headers (publish_post()の順序と一致させる)
        # ※重要: この順序は publish_post() の row リストと完全に一致する必要があります
        headers = [
            '作成日時', '投稿日', 'URL', '決定事項', '記念日', '補足',
            '最終投稿', '文字数', '文字数チェック', 'ラウンド数',
            'Pinecone結果数', '類似投稿数'
        ]
        worksheet.append_row(headers)

        # Format headers (bold)
        worksheet.format('A1:L1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })

        print(f"Created published sheet: {sheet_name}")
        print(f"Sheet ID: {spreadsheet.id}")
        print(f"Please add this ID to .env as GOOGLE_SHEETS_PUBLISHED_ID")

        return spreadsheet.id

    def save_draft(self, data):
        """
        Save draft to draft sheet

        Args:
            data: Dictionary containing draft data (prepare_sheet_data()の出力)
                {
                    '作成日時': str,
                    'URL': str,
                    '決定事項': str,
                    '記念日': str,
                    '補足': str,
                    'R1_案A': str,
                    'R1_案B': str,
                    'R1_選択': str,
                    'R1_改善リクエスト': str,
                    ... (R2, R3も同様)
                    '最終投稿': str,
                    '最終文字数': int,
                    '文字数チェック': str,
                    'ラウンド数': int,
                    'Pinecone結果数': int,
                    '類似投稿数': int
                }

        Returns:
            int: Row number of the saved draft
        """
        if not self.draft_sheet:
            raise ValueError("Draft sheet not configured")

        print(f"\n[DEBUG] save_draft() 開始")
        print(f"   受信データキー: {list(data.keys())}")
        print(f"   URL: {data.get('URL', 'なし')}")
        print(f"   決定事項: {data.get('決定事項', 'なし')}")

        # ヘッダー順に従ってデータを配置
        # Headers: '作成日時', 'URL', '決定事項', '記念日', '補足',
        #          'R1_案A', 'R1_案B', 'R1_選択',
        #          'R2_案A', 'R2_案B', 'R2_選択',
        #          'R3_案A', 'R3_案B', 'R3_選択',
        #          '改善履歴', 'ステータス'

        row = [
            data.get('作成日時', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            data.get('URL', ''),
            data.get('決定事項', ''),
            data.get('記念日', ''),
            data.get('補足', ''),
            # R1
            data.get('R1_案A', ''),
            data.get('R1_案B', ''),
            data.get('R1_選択', ''),
            # R2
            data.get('R2_案A', ''),
            data.get('R2_案B', ''),
            data.get('R2_選択', ''),
            # R3
            data.get('R3_案A', ''),
            data.get('R3_案B', ''),
            data.get('R3_選択', ''),
            # 改善履歴（複数ラウンドの改善リクエストを結合）
            self._combine_refinement_requests(data),
            # ステータス
            data.get('ステータス', '完了' if data.get('最終投稿') else '進行中')
        ]

        print(f"   書き込む行データ（最初の5項目）: {row[:5]}")
        print(f"   R1データ: 案A={bool(data.get('R1_案A'))}, 案B={bool(data.get('R1_案B'))}, 選択={data.get('R1_選択', 'なし')}")

        # Append row
        self.draft_sheet.append_row(row)
        print(f"✅ [完了] Draft sheetに保存完了")

        # Return row number
        return len(self.draft_sheet.get_all_values())

    def _combine_refinement_requests(self, data):
        """ラウンド別の改善リクエストを結合"""
        requests = []
        for r in range(1, 4):
            req = data.get(f'R{r}_改善リクエスト', '')
            if req:
                requests.append(f"R{r}: {req}")
        return '\n'.join(requests) if requests else ''

    def update_draft(self, row_num, data):
        """
        Update existing draft row

        Args:
            row_num: Row number to update (1-indexed)
            data: Dictionary containing updated data

        Returns:
            bool: Success status
        """
        if not self.draft_sheet:
            raise ValueError("Draft sheet not configured")

        # Get existing row
        existing = self.draft_sheet.row_values(row_num)

        # Update specific cells based on round
        round_num = data.get('round', 1)

        # Round columns: R1(F,G,H), R2(I,J,K), R3(L,M,N)
        col_offset = 5 + (round_num - 1) * 3  # F=6, I=9, L=12

        if 'post_a' in data:
            self.draft_sheet.update_cell(row_num, col_offset + 1, data['post_a']['text'])
        if 'post_b' in data:
            self.draft_sheet.update_cell(row_num, col_offset + 2, data['post_b']['text'])
        if 'selected' in data:
            self.draft_sheet.update_cell(row_num, col_offset + 3, data['selected'])

        # Update refinement history
        if 'refinement_request' in data and data['refinement_request']:
            self.draft_sheet.update_cell(row_num, 15, data['refinement_request'])

        return True

    def save_draft_post(self, data, row_number=None):
        """
        Save or update draft post in draft sheet

        Args:
            data: Dictionary containing draft data (日本語キー)
            row_number: Row number to update (if None, append new row)

        Returns:
            int: Row number
        """
        if not self.draft_sheet:
            raise ValueError("Draft sheet not configured")

        print(f"\n[DEBUG] save_draft_post() 開始")
        print(f"   行番号: {row_number if row_number else '新規追加'}")

        # Get headers
        headers = self.draft_sheet.row_values(1)

        # Prepare row data matching headers
        row_data = []
        for header in headers:
            value = data.get(header, '')
            row_data.append(str(value) if value else '')

        print(f"   データ長: {len(row_data)}")

        if row_number:
            # Update existing row
            cell_range = f"A{row_number}:{chr(65 + len(row_data) - 1)}{row_number}"
            self.draft_sheet.update(cell_range, [row_data])
            print(f"✅ 行{row_number}を更新しました")
            return row_number
        else:
            # Append new row
            self.draft_sheet.append_row(row_data)
            row_num = len(self.draft_sheet.get_all_values())
            print(f"✅ 新規行{row_num}を追加しました")
            return row_num

    def publish_post(self, data):
        """
        Publish final post to published sheet

        Args:
            data: Dictionary containing final post data (日本語キー)
                {
                    '投稿日': str,
                    'URL': str,
                    '決定事項': str,
                    '記念日': str,
                    '補足': str,
                    '最終投稿': str,
                    '文字数': int,
                    'ラウンド数': int,
                    'Pinecone結果数': int,
                    '類似投稿数': int,
                    '文字数チェック': str
                }

        Returns:
            int: Row number of the published post
        """
        if not self.published_sheet:
            raise ValueError("Published sheet not configured")

        print(f"\n[DEBUG] publish_post() 開始")
        print(f"   受信データキー: {list(data.keys())}")

        # 受信したデータをデバッグ出力
        print(f"   投稿日: {data.get('投稿日', 'なし')}")
        print(f"   URL: {data.get('URL', 'なし')}")
        print(f"   決定事項: {data.get('決定事項', 'なし')}")
        print(f"   最終投稿: {data.get('最終投稿', 'なし')[:50] if data.get('最終投稿') else 'なし'}...")
        print(f"   文字数: {data.get('文字数', 'なし')}")
        print(f"   ラウンド数: {data.get('ラウンド数', 'なし')}")

        # ヘッダー順に従ってデータを配置
        # Headers: '作成日時', '投稿日', 'URL', '決定事項', '記念日', '補足', '最終投稿', '文字数', '文字数チェック', 'ラウンド数', 'Pinecone結果数', '類似投稿数'
        # ※注意: ヘッダーの最初は「作成日時」です！
        row = [
            data.get('作成日時', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            data.get('投稿日', ''),
            data.get('URL', ''),
            data.get('決定事項', ''),
            data.get('記念日', ''),
            data.get('補足', ''),
            data.get('最終投稿', ''),
            data.get('文字数', 0),
            data.get('文字数チェック', ''),
            data.get('ラウンド数', 0),
            data.get('Pinecone結果数', 0),
            data.get('類似投稿数', 0)
        ]

        print(f"   書き込む行データ（最初の6項目）: {row[:6]}")

        # Append row
        self.published_sheet.append_row(row)
        print(f"✅ [完了] Published sheetに保存完了")

        # Return row number
        return len(self.published_sheet.get_all_values())

    def get_past_posts(self, limit=100):
        """
        Get past posts from published sheet (SNS投稿_完成版)
        Falls back to analytics sheet if published sheet is not available

        Args:
            limit: Maximum number of posts to retrieve

        Returns:
            list: List of past posts
        """
        print(f"\n[DEBUG] get_past_posts() 開始")
        print(f"   published_sheet: {'あり' if self.published_sheet else 'なし'}")
        print(f"   analytics_sheet: {'あり' if self.analytics_sheet else 'なし'}")

        # Priority 1: Use published sheet (作成した投稿の履歴)
        if self.published_sheet:
            try:
                print(f"[INFO] Published sheet（完成版）から過去投稿を取得中...")

                # Check if sheet has data (more than just header row)
                all_values = self.published_sheet.get_all_values()
                if len(all_values) <= 1:
                    print(f"⚠️  [警告] Published sheetにデータがありません（ヘッダーのみ）")
                    # Fall through to analytics sheet
                else:
                    all_records = self.published_sheet.get_all_records()
                    print(f"[INFO] Published sheetから {len(all_records)}件取得")

                    # Limit results
                    result = all_records[:limit] if limit else all_records
                    print(f"✅ [完了] {len(result)}件を返却（published sheet）")
                    return result

            except Exception as e:
                print(f"❌ [エラー] Published sheet読み取りエラー: {e}")
                import traceback
                traceback.print_exc()

        # Priority 2: Fallback to analytics sheet
        if self.analytics_sheet:
            try:
                print(f"[INFO] Analytics sheet（tweet）から過去投稿を取得中...")
                all_records = self.analytics_sheet.get_all_records()
                print(f"[INFO] Analytics sheetから {len(all_records)}件取得")

                # Limit results
                result = all_records[:limit] if limit else all_records
                print(f"✅ [完了] {len(result)}件を返却（analytics sheet）")
                return result

            except Exception as e:
                print(f"❌ [エラー] Analytics sheet読み取りエラー: {e}")
                import traceback
                traceback.print_exc()

        print(f"⚠️  [警告] 利用可能なシートがありません")
        return []

    def search_similar_posts(self, keyword, limit=10):
        """
        Search for similar posts in analytics and published sheets

        Args:
            keyword: Keyword to search for
            limit: Maximum number of results

        Returns:
            list: List of similar posts
        """
        results = []

        # Search in analytics sheet
        if self.analytics_sheet:
            try:
                all_records = self.analytics_sheet.get_all_records()
                for record in all_records:
                    # Simple keyword matching (can be enhanced with embedding)
                    if keyword.lower() in str(record).lower():
                        results.append(record)
                        if len(results) >= limit:
                            break
            except Exception as e:
                print(f"Error searching analytics sheet: {e}")

        # Search in published sheet
        if self.published_sheet and len(results) < limit:
            try:
                all_records = self.published_sheet.get_all_records()
                for record in all_records:
                    if keyword.lower() in str(record).lower():
                        results.append(record)
                        if len(results) >= limit:
                            break
            except Exception as e:
                print(f"Error searching published sheet: {e}")

        return results[:limit]

    def get_daily_stats(self, limit=30):
        """
        Get daily statistics from analytics day sheet

        Args:
            limit: Number of days to retrieve (default: 30, None for all)

        Returns:
            list: Daily statistics
        """
        if not self.analytics_day_sheet:
            return []

        try:
            all_records = self.analytics_day_sheet.get_all_records()
            # Return most recent records
            if limit is None:
                return all_records
            elif len(all_records) > limit:
                return all_records[-limit:]
            else:
                return all_records
        except Exception as e:
            print(f"Error reading daily stats: {e}")
            return []

    def get_follower_growth(self, limit=30):
        """
        Get follower growth data

        Args:
            limit: Number of days to retrieve (default: 30)

        Returns:
            list: Follower growth data
        """
        if not self.analytics_followers_sheet:
            return []

        try:
            all_records = self.analytics_followers_sheet.get_all_records()
            # Return most recent records
            return all_records[-limit:] if len(all_records) > limit else all_records
        except Exception as e:
            print(f"Error reading follower growth: {e}")
            return []
