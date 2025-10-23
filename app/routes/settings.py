"""
Settings Routes for PostCrafterPro
プロンプト設定管理用のルート
"""
from flask import Blueprint, request, jsonify, render_template
from app.services.prompt_service import PromptService
import traceback

settings_bp = Blueprint('settings', __name__)

# Initialize prompt service
prompt_service = PromptService()


@settings_bp.route('/settings', methods=['GET'])
def settings_page():
    """設定画面を表示"""
    return render_template('settings.html')


@settings_bp.route('/api/prompts', methods=['GET'])
def get_prompts():
    """
    すべてのプロンプトを取得

    Response:
        {
            "system_prompt_initial": "...",
            "system_prompt_final": "...",
            "system_prompt_refinement": "...",
            "user_prompt_template": "...",
            "refinement_prompt_template": "..."
        }
    """
    try:
        prompts = prompt_service.get_all_prompts()
        return jsonify(prompts), 200

    except Exception as e:
        print(f"Error in /api/prompts GET: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/api/prompts', methods=['POST'])
def update_prompts():
    """
    プロンプトを更新

    Request:
        {
            "prompt_key": "system_prompt_initial",
            "prompt_value": "新しいシステムプロンプト"
        }

    Response:
        {
            "success": true,
            "message": "プロンプトを更新しました"
        }
    """
    try:
        data = request.get_json()

        prompt_key = data.get('prompt_key')
        prompt_value = data.get('prompt_value')

        if not prompt_key or not prompt_value:
            return jsonify({'error': 'prompt_keyとprompt_valueは必須です'}), 400

        # Update prompt
        success = prompt_service.update_prompt(prompt_key, prompt_value)

        if success:
            return jsonify({
                'success': True,
                'message': 'プロンプトを更新しました'
            }), 200
        else:
            return jsonify({
                'error': '無効なプロンプトキーです'
            }), 400

    except Exception as e:
        print(f"Error in /api/prompts POST: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/api/prompts/reset', methods=['POST'])
def reset_prompts():
    """
    プロンプトをデフォルトにリセット

    Response:
        {
            "success": true,
            "message": "プロンプトをデフォルトにリセットしました"
        }
    """
    try:
        success = prompt_service.reset_to_defaults()

        if success:
            return jsonify({
                'success': True,
                'message': 'プロンプトをデフォルトにリセットしました'
            }), 200
        else:
            return jsonify({
                'error': 'リセットに失敗しました'
            }), 500

    except Exception as e:
        print(f"Error in /api/prompts/reset: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/api/prompts/validate', methods=['POST'])
def validate_prompt():
    """
    プロンプトテンプレートの検証

    Request:
        {
            "template": "テンプレート文字列",
            "required_vars": ["date", "decided", ...]
        }

    Response:
        {
            "valid": true,
            "message": ""
        }
    """
    try:
        data = request.get_json()

        template = data.get('template', '')
        required_vars = data.get('required_vars', [])

        is_valid, error_message = prompt_service.validate_prompt_template(
            template, required_vars
        )

        return jsonify({
            'valid': is_valid,
            'message': error_message
        }), 200

    except Exception as e:
        print(f"Error in /api/prompts/validate: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
