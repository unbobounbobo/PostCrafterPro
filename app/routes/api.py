"""
API Routes for PostCrafterPro
Tinder形式のSNS投稿作成アプリケーション
"""

from flask import Blueprint, request, jsonify
from app.services.rag_service import RAGService
from app.services.claude_service import ClaudeService
from app.services.sheets_service import SheetsService
from datetime import datetime
import traceback

api_bp = Blueprint('api', __name__)

# Initialize services
rag_service = RAGService()
claude_service = ClaudeService()
sheets_service = SheetsService()


@api_bp.route('/init', methods=['POST'])
def initialize_context():
    """
    Step 1: コンテキストの初期化
    - Pinecone検索（商品情報）
    - 過去投稿の類似検索

    Request:
        {
            "date": "2025-01-15",
            "url": "https://ec.midori-anzen.com/shop/...",
            "decided": "防災の日にヘルメットをPRする",
            "anniversary": "防災の日",
            "remarks": "補足事項"
        }

    Response:
        {
            "pinecone_results": [...],
            "similar_posts": [...]
        }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('decided'):
            return jsonify({'error': '決定事項は必須です'}), 400

        # Get comprehensive context (including X Analytics insights)
        # URL is optional - if not provided, only similar posts will be searched
        context = rag_service.get_comprehensive_context(
            url=data.get('url') or None,
            decided=data.get('decided'),
            anniversary=data.get('anniversary')
        )

        return jsonify({
            'pinecone_results': context.get('pinecone_results', []),
            'similar_posts': context.get('similar_posts', []),
            'analytics_insights': context.get('analytics_insights', '')
        }), 200

    except Exception as e:
        print(f"Error in /api/init: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/generate', methods=['POST'])
def generate_posts():
    """
    Step 2: 初回投稿生成（2つの案）

    Request:
        {
            "date": "2025-01-15",
            "url": "https://ec.midori-anzen.com/shop/...",
            "decided": "防災の日にヘルメットをPRする",
            "anniversary": "防災の日",
            "remarks": "補足事項",
            "pinecone_results": [...],
            "similar_posts": [...]
        }

    Response:
        {
            "post_a": {
                "text": "...",
                "character_count": 123,
                "is_valid": true,
                "thinking": "..."
            },
            "post_b": {
                "text": "...",
                "character_count": 123,
                "is_valid": true,
                "thinking": "..."
            },
            "metadata": {...}
        }
    """
    try:
        print(f"\n{'🟢'*30}")
        print(f"[API] /api/generate リクエスト受信")
        print(f"{'🟢'*30}")

        data = request.get_json()

        print(f"\n[DEBUG] リクエストデータ:")
        print(f"   日付: {data.get('date')}")
        print(f"   URL: {data.get('url')}")
        print(f"   決定事項: {data.get('decided')}")
        print(f"   記念日: {data.get('anniversary')}")
        print(f"   備考: {data.get('remarks')}")
        print(f"   Pinecone結果数: {len(data.get('pinecone_results', []))}")
        print(f"   類似投稿数: {len(data.get('similar_posts', []))}")
        print(f"   Analytics有無: {'あり' if data.get('analytics_insights') else 'なし'}")

        # Validate required fields
        if not data.get('decided'):
            print(f"❌ [エラー] 決定事項が入力されていません")
            return jsonify({'error': '決定事項は必須です'}), 400

        # Format context for Claude
        pinecone_context = None
        if data.get('pinecone_results'):
            print(f"\n[INFO] Pineconeコンテキストをフォーマット中...")
            pinecone_context = format_pinecone_context(data['pinecone_results'])
            print(f"   フォーマット完了 (長さ: {len(pinecone_context) if pinecone_context else 0}文字)")

        similar_posts_context = None
        if data.get('similar_posts'):
            print(f"\n[INFO] 類似投稿コンテキストをフォーマット中...")
            similar_posts_context = format_similar_posts_context(data['similar_posts'])
            print(f"   フォーマット完了 (長さ: {len(similar_posts_context) if similar_posts_context else 0}文字)")
            print(f"   内容プレビュー: {similar_posts_context[:200] if similar_posts_context else 'なし'}...")
        else:
            print(f"\n⚠️  [警告] 類似投稿が見つかりませんでした")

        # Get analytics insights from request
        analytics_insights = data.get('analytics_insights', '')
        if analytics_insights:
            print(f"\n[INFO] Analytics insights取得完了 (長さ: {len(analytics_insights)}文字)")

        # Generate posts with Claude (including X Analytics insights)
        print(f"\n[INFO] Claude API呼び出し開始...")
        result = claude_service.create_sns_post_with_context(
            date=data.get('date'),
            decided=data.get('decided'),
            url=data.get('url'),
            remarks=data.get('remarks', ''),
            anniversary=data.get('anniversary', ''),
            pinecone_context=pinecone_context,
            similar_posts=similar_posts_context,
            analytics_insights=analytics_insights
        )

        print(f"\n{'🟢'*30}")
        print(f"[API] Claude API呼び出し完了")
        print(f"[DEBUG] 戻り値の確認:")
        print(f"   result type: {type(result)}")
        print(f"   result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        print(f"   post_a: {result.get('post_a') if isinstance(result, dict) else 'N/A'}")
        print(f"   post_b: {result.get('post_b') if isinstance(result, dict) else 'N/A'}")

        if isinstance(result, dict):
            if result.get('post_a'):
                print(f"\n✅ [案A] 取得成功")
                print(f"   テキスト長: {len(result['post_a'].get('text', ''))}文字")
                print(f"   内容: {result['post_a'].get('text', '')[:100]}...")
                print(f"   文字数: {result['post_a'].get('character_count', 0)}")
                print(f"   有効: {result['post_a'].get('is_valid', False)}")
            else:
                print(f"\n❌ [案A] データなし")

            if result.get('post_b'):
                print(f"\n✅ [案B] 取得成功")
                print(f"   テキスト長: {len(result['post_b'].get('text', ''))}文字")
                print(f"   内容: {result['post_b'].get('text', '')[:100]}...")
                print(f"   文字数: {result['post_b'].get('character_count', 0)}")
                print(f"   有効: {result['post_b'].get('is_valid', False)}")
            else:
                print(f"\n❌ [案B] データなし")

            if result.get('error'):
                print(f"\n❌ [エラー] Claude APIエラー: {result['error']}")

        print(f"{'🟢'*30}\n")

        return jsonify(result), 200

    except Exception as e:
        print(f"\n{'❌'*30}")
        print(f"[CRITICAL ERROR] /api/generate でエラー発生")
        print(f"エラー内容: {str(e)}")
        print(f"{'❌'*30}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/refine', methods=['POST'])
def refine_post():
    """
    Step 3: 投稿の改善（選択した投稿をベースに2つの改善案）

    Request:
        {
            "selected_post": "選択された投稿テキスト",
            "refinement_request": "もっとカジュアルに（オプション）",
            "round": 2
        }

    Response:
        {
            "post_a": {...},
            "post_b": {...},
            "metadata": {...}
        }
    """
    try:
        print(f"\n{'🟡'*30}")
        print(f"[API] /api/refine リクエスト受信")
        print(f"{'🟡'*30}")

        data = request.get_json()

        print(f"\n[DEBUG] リクエストデータ:")
        print(f"   selected_post: {data.get('selected_post', '')[:100]}...")
        print(f"   refinement_request: {data.get('refinement_request', '')}")
        print(f"   round: {data.get('round', 2)}")

        # Validate required fields
        if not data.get('selected_post'):
            print(f"❌ [エラー] 選択された投稿がありません")
            return jsonify({'error': '選択された投稿は必須です'}), 400

        # Refine post with Claude
        print(f"\n[INFO] Claude API（改善）呼び出し開始...")
        result = claude_service.refine_post(
            selected_post=data.get('selected_post'),
            refinement_request=data.get('refinement_request', ''),
            round_num=data.get('round', 2)
        )

        print(f"\n{'🟡'*30}")
        print(f"[API] Claude API（改善）呼び出し完了")
        print(f"[DEBUG] 戻り値の確認:")
        print(f"   result type: {type(result)}")
        print(f"   result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

        if isinstance(result, dict):
            if result.get('post_a'):
                print(f"\n✅ [改善案A] 取得成功")
                print(f"   テキスト長: {len(result['post_a'].get('text', ''))}文字")
                print(f"   内容: {result['post_a'].get('text', '')[:100]}...")
            else:
                print(f"\n❌ [改善案A] データなし")

            if result.get('post_b'):
                print(f"\n✅ [改善案B] 取得成功")
                print(f"   テキスト長: {len(result['post_b'].get('text', ''))}文字")
                print(f"   内容: {result['post_b'].get('text', '')[:100]}...")
            else:
                print(f"\n❌ [改善案B] データなし")

            if result.get('error'):
                print(f"\n❌ [エラー] Claude APIエラー: {result['error']}")

        print(f"{'🟡'*30}\n")

        return jsonify(result), 200

    except Exception as e:
        print(f"\n{'❌'*30}")
        print(f"[CRITICAL ERROR] /api/refine でエラー発生")
        print(f"エラー内容: {str(e)}")
        print(f"{'❌'*30}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/publish', methods=['POST'])
def publish_post():
    """
    Step 4: 最終投稿の保存（Google Sheetsに保存）

    Request:
        {
            "date": "2025-01-15",
            "url": "https://ec.midori-anzen.com/shop/...",
            "decided": "防災の日にヘルメットをPRする",
            "anniversary": "防災の日",
            "remarks": "補足事項",
            "final_post": {
                "text": "最終投稿テキスト",
                "character_count": 123,
                "is_valid": true
            },
            "history": [
                {
                    "round": 1,
                    "postA": {...},
                    "postB": {...},
                    "selected": "A",
                    "refinementRequest": ""
                },
                ...
            ],
            "pinecone_results": [...],
            "similar_posts": [...]
        }

    Response:
        {
            "success": true,
            "draft_row": 2,
            "published_row": 5
        }
    """
    try:
        print(f"\n{'🟣'*30}")
        print(f"[API] /api/publish リクエスト受信")

        data = request.get_json()

        print(f"\n[DEBUG] 受信データ:")
        print(f"   date: {data.get('date', 'なし')}")
        print(f"   url: {data.get('url', 'なし')[:50] if data.get('url') else 'なし'}...")
        print(f"   decided: {data.get('decided', 'なし')}")
        print(f"   final_post: {bool(data.get('final_post'))}")
        if data.get('final_post'):
            print(f"      text: {data['final_post'].get('text', '')[:50]}...")
            print(f"      character_count: {data['final_post'].get('character_count', 0)}")
        print(f"   history: {len(data.get('history', []))}件")

        # Validate required fields
        if not data.get('final_post'):
            return jsonify({'error': '最終投稿は必須です'}), 400

        # Prepare data for sheets
        print(f"\n[INFO] prepare_sheet_data() 実行中...")
        sheet_data = prepare_sheet_data(data)
        print(f"   準備されたデータキー: {list(sheet_data.keys())[:10]}...")

        # Save to Draft sheet
        print(f"\n[INFO] Draft sheetに保存中...")
        draft_row = sheets_service.save_draft(sheet_data)
        print(f"   Draft sheet 行番号: {draft_row}")

        # Save to Published sheet
        print(f"\n[INFO] Published sheetに保存中...")
        published_data = {
            '作成日時': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '投稿日': data.get('date', ''),
            'URL': data.get('url', ''),
            '決定事項': data.get('decided', ''),
            '記念日': data.get('anniversary', ''),
            '補足': data.get('remarks', ''),
            '最終投稿': data['final_post']['text'],
            '文字数': data['final_post']['character_count'],
            '文字数チェック': '✓' if data['final_post']['is_valid'] else '✗',
            'ラウンド数': len(data.get('history', [])),
            'Pinecone結果数': len(data.get('pinecone_results', [])),
            '類似投稿数': len(data.get('similar_posts', []))
        }
        print(f"   Published data keys: {list(published_data.keys())}")

        published_row = sheets_service.publish_post(published_data)
        print(f"   Published sheet 行番号: {published_row}")

        print(f"\n✅ [完了] /api/publish 処理完了")
        print(f"{'🟣'*30}\n")

        return jsonify({
            'success': True,
            'draft_row': draft_row,
            'published_row': published_row
        }), 200

    except Exception as e:
        print(f"\n❌ [エラー] /api/publish でエラー: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ========================================
# Helper Functions
# ========================================

def format_pinecone_context(results):
    """Pinecone検索結果をClaude用のコンテキストにフォーマット"""
    if not results:
        return None

    context = "【商品情報（Pinecone）】\n"
    for i, result in enumerate(results[:5], 1):
        context += f"\n{i}. "
        if result.get('title'):
            context += f"タイトル: {result['title']}\n"
        if result.get('description'):
            context += f"説明: {result['description']}\n"
        if result.get('content'):
            context += f"内容: {result['content'][:200]}...\n"
        if result.get('score'):
            context += f"類似度: {result['score']:.2%}\n"

    return context


def format_similar_posts_context(posts):
    """過去の類似投稿をClaude用のコンテキストにフォーマット"""
    if not posts:
        return None

    context = "【過去の類似投稿】\n"
    for i, post in enumerate(posts[:5], 1):
        context += f"\n{i}. "
        # Try multiple field names (PostCrafterPro, X Analytics, etc.)
        post_text = (
            post.get('text') or
            post.get('最終投稿', '') or
            post.get('ツイート本文', '')
        )
        context += f"{post_text}\n"
        if post.get('similarity_score'):
            context += f"類似度: {post['similarity_score']:.2%}\n"
        # Try multiple date field names
        post_date = post.get('投稿日') or post.get('date') or post.get('時間（日本1）', '')
        if post_date:
            context += f"投稿日: {post_date}\n"

    return context


def prepare_sheet_data(data):
    """Google Sheets保存用のデータを準備"""
    sheet_data = {
        '作成日時': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '投稿日': data.get('date', ''),
        'URL': data.get('url', ''),
        '決定事項': data.get('decided', ''),
        '記念日': data.get('anniversary', ''),
        '補足': data.get('remarks', ''),
    }

    # Add round history
    history = data.get('history', [])
    for round_data in history:
        round_num = round_data['round']
        prefix = f'R{round_num}'

        # Post A
        if round_data.get('postA'):
            sheet_data[f'{prefix}_案A'] = round_data['postA']['text']
            sheet_data[f'{prefix}_案A_文字数'] = round_data['postA']['character_count']

        # Post B
        if round_data.get('postB'):
            sheet_data[f'{prefix}_案B'] = round_data['postB']['text']
            sheet_data[f'{prefix}_案B_文字数'] = round_data['postB']['character_count']

        # Selection
        sheet_data[f'{prefix}_選択'] = round_data.get('selected', '')

        # Refinement request
        if round_data.get('refinementRequest'):
            sheet_data[f'{prefix}_改善リクエスト'] = round_data['refinementRequest']

    # Final post
    if data.get('final_post'):
        sheet_data['最終投稿'] = data['final_post']['text']
        sheet_data['最終文字数'] = data['final_post']['character_count']
        sheet_data['文字数チェック'] = '✓' if data['final_post']['is_valid'] else '✗'

    # Metadata
    sheet_data['ラウンド数'] = len(history)
    sheet_data['Pinecone結果数'] = len(data.get('pinecone_results', []))
    sheet_data['類似投稿数'] = len(data.get('similar_posts', []))

    return sheet_data
