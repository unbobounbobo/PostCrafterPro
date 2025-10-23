"""
Batch Processing API Routes

複数の投稿を一括で生成・処理するためのAPI
"""

from flask import Blueprint, request, jsonify
from app.services.sheets_service import SheetsService
from app.services.claude_service import ClaudeService
from app.services.pinecone_service import PineconeService
import traceback
import csv
import io
from datetime import datetime

batch_api_bp = Blueprint('batch_api', __name__, url_prefix='/api/batch')


@batch_api_bp.route('/load', methods=['POST'])
def load_batch_data():
    """
    Step 1: Load batch data from Google Sheets

    Request:
        {
            "source": "sheet",  # "sheet", "csv", or "manual"
            "sheet_name": "SNS投稿_下書き",
            "start_row": 2,
            "end_row": 0  # 0 = all rows
        }

    Response:
        {
            "success": true,
            "posts": [
                {
                    "row": 2,
                    "date": "2025-01-15",
                    "url": "...",
                    "decided": "...",
                    "anniversary": "...",
                    "remarks": "..."
                },
                ...
            ],
            "count": 10
        }
    """
    try:
        data = request.get_json()
        source = data.get('source', 'sheet')

        print(f"\n{'📦'*30}")
        print(f"[BATCH] データ読み込み開始")
        print(f"   ソース: {source}")
        print(f"{'📦'*30}\n")

        if source == 'sheet':
            sheet_name = data.get('sheet_name', 'SNS投稿_下書き')
            start_row = data.get('start_row', 2)
            end_row = data.get('end_row', 0)

            print(f"[INFO] Google Sheetsから読み込み")
            print(f"   シート名: {sheet_name}")
            print(f"   開始行: {start_row}")
            print(f"   終了行: {end_row if end_row > 0 else '全件'}")

            sheets_service = SheetsService()

            # Get all data from the sheet
            all_values = sheets_service.draft_sheet.get_all_values()

            if not all_values or len(all_values) < 2:
                return jsonify({
                    'success': False,
                    'error': 'シートにデータがありません'
                }), 400

            # Headers are in row 1 (index 0)
            headers = all_values[0]

            # Find column indices
            try:
                date_idx = headers.index('投稿日')
                url_idx = headers.index('URL')
                decided_idx = headers.index('決定事項')
                anniversary_idx = headers.index('記念日') if '記念日' in headers else None
                remarks_idx = headers.index('補足') if '補足' in headers else None
                final_post_idx = headers.index('最終投稿') if '最終投稿' in headers else None
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'error': f'必須カラムが見つかりません: {e}'
                }), 400

            # Extract data rows
            posts = []
            data_rows = all_values[start_row - 1:]  # start_row is 1-indexed

            if end_row > 0:
                data_rows = data_rows[:end_row - start_row + 1]

            for i, row in enumerate(data_rows):
                row_number = start_row + i

                # Skip if already has final post
                if final_post_idx and len(row) > final_post_idx and row[final_post_idx].strip():
                    print(f"[SKIP] 行{row_number}: すでに最終投稿が存在")
                    continue

                # Skip if missing required fields
                if len(row) <= decided_idx or not row[decided_idx].strip():
                    print(f"[SKIP] 行{row_number}: 決定事項が空")
                    continue

                post = {
                    'row': row_number,
                    'date': row[date_idx] if len(row) > date_idx else '',
                    'url': row[url_idx] if len(row) > url_idx else '',
                    'decided': row[decided_idx] if len(row) > decided_idx else '',
                    'anniversary': row[anniversary_idx] if anniversary_idx and len(row) > anniversary_idx else '',
                    'remarks': row[remarks_idx] if remarks_idx and len(row) > remarks_idx else ''
                }

                posts.append(post)

            print(f"\n✅ [成功] {len(posts)}件のデータを読み込みました")

            return jsonify({
                'success': True,
                'posts': posts,
                'count': len(posts)
            }), 200

        elif source == 'csv':
            # CSV parsing (to be implemented)
            return jsonify({
                'success': False,
                'error': 'CSV読み込みは未実装です'
            }), 501

        else:
            return jsonify({
                'success': False,
                'error': f'不明なソース: {source}'
            }), 400

    except Exception as e:
        print(f"\n{'❌'*30}")
        print(f"[ERROR] データ読み込みエラー")
        print(f"   エラー: {str(e)}")
        print(f"{'❌'*30}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@batch_api_bp.route('/process', methods=['POST'])
def process_batch():
    """
    Step 2: Process batch posts (generate posts one by one)

    Request:
        {
            "post": {
                "row": 2,
                "date": "2025-01-15",
                "url": "...",
                "decided": "...",
                "anniversary": "...",
                "remarks": "..."
            },
            "auto_save": false,
            "select_first": true  # Automatically select first post (post_a)
        }

    Response:
        {
            "success": true,
            "post_a": {...},
            "post_b": {...},
            "selected": "..."  # If select_first=true
        }
    """
    try:
        data = request.get_json()
        post_data = data.get('post')
        auto_save = data.get('auto_save', False)
        select_first = data.get('select_first', True)

        print(f"\n{'🔄'*30}")
        print(f"[BATCH] 投稿生成開始")
        print(f"   行: {post_data.get('row')}")
        print(f"   投稿日: {post_data.get('date')}")
        print(f"   決定事項: {post_data.get('decided')}")
        print(f"{'🔄'*30}\n")

        # Initialize services
        claude_service = ClaudeService()
        pinecone_service = PineconeService()
        sheets_service = SheetsService()

        # Step 1: Get context (Pinecone + Similar posts)
        print(f"[INFO] コンテキスト取得中...")

        # Pinecone search
        pinecone_results = []
        if post_data.get('url'):
            try:
                pinecone_results = pinecone_service.search_products(
                    query=post_data.get('decided', ''),
                    top_k=5
                )
                print(f"✅ Pinecone: {len(pinecone_results)}件取得")
            except Exception as e:
                print(f"⚠️  Pinecone検索エラー: {e}")

        # Similar posts search
        similar_posts = []
        try:
            similar_posts = sheets_service.get_similar_posts(
                query=post_data.get('decided', ''),
                top_k=3
            )
            print(f"✅ 類似投稿: {len(similar_posts)}件取得")
        except Exception as e:
            print(f"⚠️  類似投稿検索エラー: {e}")

        # Step 2: Generate posts
        print(f"[INFO] 投稿生成中...")

        result = claude_service.generate_posts(
            date=post_data.get('date', ''),
            decided=post_data.get('decided', ''),
            url=post_data.get('url', ''),
            remarks=post_data.get('remarks', ''),
            anniversary=post_data.get('anniversary', ''),
            pinecone_context=pinecone_results,
            similar_posts=similar_posts
        )

        if 'error' in result:
            print(f"❌ [エラー] 投稿生成失敗: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

        print(f"✅ [成功] 投稿生成完了")

        # Step 3: Auto-select first post if requested
        selected_post = None
        if select_first and result.get('post_a'):
            selected_post = result['post_a']['text']
            print(f"[INFO] 自動選択: 案A")

        # Step 4: Auto-save if requested
        if auto_save and selected_post:
            print(f"[INFO] 自動保存中...")

            save_data = {
                '作成日時': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '投稿日': post_data.get('date', ''),
                'URL': post_data.get('url', ''),
                '決定事項': post_data.get('decided', ''),
                '記念日': post_data.get('anniversary', ''),
                '補足': post_data.get('remarks', ''),
                '最終投稿': selected_post,
                '文字数': len(selected_post),
                '文字数チェック': '✅' if len(selected_post) <= 140 else '❌',
                'ラウンド数': 1,
                'Pinecone結果数': len(pinecone_results),
                '類似投稿数': len(similar_posts)
            }

            try:
                # Save to draft sheet (update existing row)
                sheets_service.save_draft_post(save_data, post_data.get('row'))

                # Save to published sheet (add new row)
                sheets_service.publish_post(save_data)

                print(f"✅ [成功] 自動保存完了")
            except Exception as e:
                print(f"⚠️  自動保存エラー: {e}")

        return jsonify({
            'success': True,
            'post_a': result.get('post_a'),
            'post_b': result.get('post_b'),
            'selected': selected_post,
            'pinecone_count': len(pinecone_results),
            'similar_count': len(similar_posts)
        }), 200

    except Exception as e:
        print(f"\n{'❌'*30}")
        print(f"[ERROR] バッチ処理エラー")
        print(f"   エラー: {str(e)}")
        print(f"{'❌'*30}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@batch_api_bp.route('/export', methods=['POST'])
def export_results():
    """
    Step 3: Export batch results as CSV

    Request:
        {
            "results": [
                {
                    "row": 2,
                    "date": "2025-01-15",
                    "status": "success",
                    "post": "..."
                },
                ...
            ]
        }

    Response:
        CSV file download
    """
    try:
        data = request.get_json()
        results = data.get('results', [])

        print(f"\n{'💾'*30}")
        print(f"[BATCH] 結果エクスポート開始")
        print(f"   件数: {len(results)}")
        print(f"{'💾'*30}\n")

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(['行番号', '投稿日', 'ステータス', '生成された投稿', 'エラー'])

        # Write data
        for result in results:
            writer.writerow([
                result.get('row', ''),
                result.get('date', ''),
                result.get('status', ''),
                result.get('post', ''),
                result.get('error', '')
            ])

        csv_data = output.getvalue()
        output.close()

        print(f"✅ [成功] CSV生成完了")

        return jsonify({
            'success': True,
            'csv': csv_data,
            'filename': f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }), 200

    except Exception as e:
        print(f"\n{'❌'*30}")
        print(f"[ERROR] エクスポートエラー")
        print(f"   エラー: {str(e)}")
        print(f"{'❌'*30}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
