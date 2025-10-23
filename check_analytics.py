"""
Check X analytics sheet structure
"""
import sys
import io
from app.services.sheets_service import SheetsService

# UTF-8 output for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sheets = SheetsService()

# アナリティクスシートの構造確認
if sheets.analytics_sheet:
    print('=== アナリティクスシートのカラム名 ===')
    headers = sheets.analytics_sheet.row_values(1)
    for i, h in enumerate(headers, 1):
        print(f'{i}. {h}')

    print('\n=== サンプルデータ（最初の3行） ===')
    all_records = sheets.analytics_sheet.get_all_records()
    for i, record in enumerate(all_records[:3], 1):
        print(f'\n--- 行{i} ---')
        for key, value in record.items():
            if value:  # 空でないフィールドのみ表示
                print(f'{key}: {str(value)[:100]}')  # 最初の100文字のみ

    print(f'\n=== 合計レコード数: {len(all_records)} ===')
else:
    print('アナリティクスシートに接続できませんでした')
