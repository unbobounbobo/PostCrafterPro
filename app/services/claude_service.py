"""
Claude 4.5 API service for PostCrafterPro
Based on enhanced_sns_crafter.py with improvements for Tinder UI and Pinecone RAG
"""
import os
import anthropic
import requests
import json
import re
from datetime import datetime
from app.services.prompt_service import PromptService
from pydantic import BaseModel, Field


# Pydantic models for structured output
class PostOption(BaseModel):
    """Single post option"""
    text: str = Field(description="投稿テキスト（全角140字/半角280字以内）")
    character_count: int = Field(description="文字数")
    is_valid: bool = Field(description="文字数が280字以内かどうか")


class TwoPostsResponse(BaseModel):
    """Two post options response"""
    post_a: PostOption = Field(description="投稿案A")
    post_b: PostOption = Field(description="投稿案B")


class ClaudeService:
    """
    Claude 4.5 API integration for SNS post generation
    """

    def __init__(self):
        """Initialize Claude client"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')

        # Tweet length checker API
        self.tweet_checker_api = "https://mj7k0bs0qd.execute-api.ap-northeast-1.amazonaws.com/prod/check"

        # Prompt service for dynamic prompt management
        self.prompt_service = PromptService()

        print(f"[OK] Claude Service initialized with model: {self.model}")

    def create_sns_post_with_context(self, date, decided, url, remarks,
                                     anniversary=None, pinecone_context=None, similar_posts=None,
                                     analytics_insights=None):
        """
        Create initial SNS post with Pinecone context (2 options for Tinder UI)

        Args:
            date: Post date
            decided: Decided content
            url: Product URL
            remarks: Additional remarks
            anniversary: Anniversary information (optional)
            pinecone_context: Product information from Pinecone
            similar_posts: Similar past posts
            analytics_insights: X Analytics performance insights

        Returns:
            dict: {
                'post_a': {'text': str, 'character_count': int, 'is_valid': bool},
                'post_b': {'text': str, 'character_count': int, 'is_valid': bool},
                'metadata': {...}
            }
        """
        # Build message content
        message_content = self._construct_message(
            date, decided, url, remarks, anniversary,
            pinecone_context, similar_posts, analytics_insights,
            request_type='initial'
        )

        # Define tools
        tools = [
            {
                "name": "tweet_length_checker",
                "description": "API to check if a given text meets Twitter's length requirements",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to be checked for Twitter length requirements"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "web_search",
                "type": "web_search_20250305"
            }
        ]

        conversation = [{"role": "user", "content": message_content}]

        # Result container
        result = {
            "post_a": None,
            "post_b": None,
            "metadata": {
                "model": self.model,
                "tokens": {"input": 0, "output": 0}
            }
        }

        try:
            print(f"\n{'🔵'*30}")
            print(f"[INFO] Claude API 投稿生成開始")
            print(f"   モデル: {self.model}")
            print(f"   日付: {date}")
            print(f"   決定事項: {decided}")
            print(f"{'🔵'*30}\n")

            # Conversation loop (max 10 turns)
            max_turns = 10
            current_turn = 0

            while current_turn < max_turns:
                current_turn += 1
                print(f"\n{'='*60}")
                print(f"会話ターン {current_turn}/{max_turns}")
                print(f"{'='*60}")

                # Force final output after turn 6
                if current_turn >= 6:
                    print(f"\n⚠️  [警告] ターン数が6に到達 - 強制的に最終出力を要求します")
                    conversation.append({
                        "role": "user",
                        "content": "これまでの検討に基づいて、2つの最終投稿案を出力してください。"
                    })

                    print(f"[INFO] 構造化出力リクエスト送信中...")
                    # Request JSON output via system prompt (Anthropic API doesn't support response_format)
                    final_response = self.client.messages.create(
                        model=self.model,
                        max_tokens=10000,
                        temperature=1,
                        system=self.prompt_service.get_system_prompt('final'),
                        messages=conversation
                    )

                    print(f"[INFO] 構造化出力レスポンス受信完了")
                    # Parse structured output
                    self._parse_structured_output(final_response, result)

                    break

                # Regular API request
                response = self.client.beta.messages.create(
                    model=self.model,
                    max_tokens=16000,
                    temperature=1,
                    system=self.prompt_service.get_system_prompt('initial'),
                    messages=conversation,
                    tools=tools,
                    thinking={"type": "enabled", "budget_tokens": 6554},
                    betas=["web-search-2025-03-05", "output-128k-2025-02-19"]
                )

                # Log web search results if any
                self._log_web_search_results(response)

                # Add response to conversation
                conversation.append({"role": "assistant", "content": response.content})

                # Check if conversation is complete
                if response.stop_reason != "tool_use":
                    print(f"\n✅ [完了] Claude応答完了 (stop_reason: {response.stop_reason})")
                    print(f"[INFO] 最終投稿案の構造化出力を要求します")

                    # Request structured output for final posts
                    conversation.append({
                        "role": "user",
                        "content": "2つの投稿案を出力してください。"
                    })

                    print(f"[INFO] 構造化出力リクエスト送信中...")
                    final_response = self.client.messages.create(
                        model=self.model,
                        max_tokens=10000,
                        temperature=1,
                        system=self.prompt_service.get_system_prompt('final'),
                        messages=conversation
                    )

                    print(f"[INFO] 構造化出力レスポンス受信完了")
                    print(f"[DEBUG] レスポンス詳細:")
                    print(f"   - stop_reason: {final_response.stop_reason}")
                    print(f"   - content blocks: {len(final_response.content)}")
                    for i, block in enumerate(final_response.content):
                        print(f"   - block[{i}]: type={getattr(block, 'type', 'unknown')}, length={len(getattr(block, 'text', '')) if hasattr(block, 'text') else 0}")
                        if hasattr(block, 'text'):
                            print(f"      preview: {block.text[:200]}...")

                    self._parse_structured_output(final_response, result)
                    break

                # Process tool use
                tool_outputs = self._process_tool_use(response)
                if tool_outputs:
                    conversation.append({"role": "user", "content": tool_outputs})

            print(f"\n{'🔵'*30}")
            print(f"[SUCCESS] 投稿生成完了")
            print(f"   post_a: {'✅ あり' if result.get('post_a') else '❌ なし'}")
            print(f"   post_b: {'✅ あり' if result.get('post_b') else '❌ なし'}")
            print(f"{'🔵'*30}\n")

            return result

        except Exception as e:
            print(f"\n{'❌'*30}")
            print(f"[CRITICAL ERROR] Claude API実行中にエラー発生")
            print(f"エラー内容: {e}")
            print(f"{'❌'*30}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def refine_post(self, selected_post, refinement_request=None, round_num=2):
        """
        Refine selected post and generate 2 improved options

        Args:
            selected_post: The post text selected by user
            refinement_request: Optional refinement request
            round_num: Round number

        Returns:
            dict: {
                'post_a': {...},
                'post_b': {...},
                'metadata': {...}
            }
        """
        print(f"\n{'🟠'*30}")
        print(f"[INFO] 投稿改善（refine_post）開始")
        print(f"   モデル: {self.model}")
        print(f"   ラウンド: {round_num}")
        print(f"   改善リクエスト: {refinement_request or '（なし）'}")
        print(f"   元の投稿: {selected_post[:100]}...")
        print(f"{'🟠'*30}\n")

        # Build refinement message from template
        template = self.prompt_service.get_refinement_prompt_template()

        refinement_instruction = f"「{refinement_request}」という要望を反映した" if refinement_request else ""

        message = template.format(
            refinement_instruction=refinement_instruction,
            selected_post=selected_post
        )

        print(f"[INFO] プロンプト構築完了")
        conversation = [{"role": "user", "content": message}]

        # Define tools (same as initial generation)
        tools = [
            {
                "name": "tweet_length_checker",
                "description": "API to check if a given text meets Twitter's length requirements",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to be checked for Twitter length requirements"
                        }
                    },
                    "required": ["text"]
                }
            }
        ]

        # Result container
        result = {
            "post_a": None,
            "post_b": None,
            "metadata": {"model": self.model, "round": round_num}
        }

        try:
            print(f"[INFO] Claude API リクエスト送信中（ツール使用可能）...")

            # Conversation loop (max 5 turns for refinement)
            max_turns = 5
            current_turn = 0

            while current_turn < max_turns:
                current_turn += 1
                print(f"\n{'='*60}")
                print(f"改善ターン {current_turn}/{max_turns}")
                print(f"{'='*60}")

                # Force final output after turn 3
                if current_turn >= 3:
                    print(f"\n⚠️  [警告] ターン数が3に到達 - 強制的に最終出力を要求します")
                    conversation.append({
                        "role": "user",
                        "content": "これまでの検討に基づいて、2つの改善案を出力してください。"
                    })

                    print(f"[INFO] 構造化出力リクエスト送信中...")
                    final_response = self.client.messages.create(
                        model=self.model,
                        max_tokens=8000,
                        temperature=1,
                        system=self.prompt_service.get_system_prompt('refinement'),
                        messages=conversation
                    )

                    print(f"[INFO] 構造化出力レスポンス受信完了")
                    self._parse_structured_output(final_response, result)
                    break

                # Regular API request with tools
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=8000,
                    temperature=1,
                    system=self.prompt_service.get_system_prompt('refinement'),
                    messages=conversation,
                    tools=tools
                )

                # Add response to conversation
                conversation.append({"role": "assistant", "content": response.content})

                # Check if conversation is complete
                if response.stop_reason != "tool_use":
                    print(f"\n✅ [完了] Claude応答完了 (stop_reason: {response.stop_reason})")
                    print(f"[INFO] 最終改善案の構造化出力を要求します")

                    # Request structured output for final posts
                    conversation.append({
                        "role": "user",
                        "content": "2つの改善案を出力してください。"
                    })

                    print(f"[INFO] 構造化出力リクエスト送信中...")
                    final_response = self.client.messages.create(
                        model=self.model,
                        max_tokens=8000,
                        temperature=1,
                        system=self.prompt_service.get_system_prompt('refinement'),
                        messages=conversation
                    )

                    print(f"[INFO] 構造化出力レスポンス受信完了")
                    self._parse_structured_output(final_response, result)
                    break

                # Process tool use
                tool_outputs = self._process_tool_use(response)
                if tool_outputs:
                    conversation.append({"role": "user", "content": tool_outputs})

            print(f"\n{'🟠'*30}")
            print(f"[SUCCESS] 投稿改善完了")
            print(f"   post_a: {'✅ あり' if result.get('post_a') else '❌ なし'}")
            print(f"   post_b: {'✅ あり' if result.get('post_b') else '❌ なし'}")
            print(f"{'🟠'*30}\n")

            return result

        except Exception as e:
            print(f"\n{'❌'*30}")
            print(f"[CRITICAL ERROR] 投稿改善中にエラー発生")
            print(f"エラー内容: {e}")
            print(f"{'❌'*30}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def _construct_message(self, date, decided, url, remarks, anniversary,
                          pinecone_context, similar_posts, analytics_insights=None,
                          request_type='initial'):
        """
        Construct message content with Pinecone, past posts, and analytics context

        Args:
            date, decided, url, remarks, anniversary: Post information
            pinecone_context: Product info from Pinecone
            similar_posts: Similar past posts
            analytics_insights: X Analytics performance insights
            request_type: 'initial' or 'refinement'

        Returns:
            str: Formatted message content
        """
        # Pinecone context section
        pinecone_section = ""
        if pinecone_context and pinecone_context.get('combined_summary'):
            pinecone_section = f"""【Pinecone検索結果（商品情報）】
{pinecone_context['combined_summary']}
"""

        # Similar posts section
        similar_section = ""
        if similar_posts:
            # Check if similar_posts is already a formatted string
            if isinstance(similar_posts, str):
                # Already formatted by format_similar_posts_context()
                similar_section = similar_posts
            else:
                # Process raw list of posts
                similar_texts = []
                for i, post in enumerate(similar_posts[:3], 1):
                    if isinstance(post, dict):
                        post_text = post.get('text', post.get('最終投稿', ''))
                        if post_text:
                            similar_texts.append(f"{i}. {post_text}")

                if similar_texts:
                    similar_section = f"""【過去の類似投稿】
{chr(10).join(similar_texts)}
"""

        # X Analytics insights section (NEW)
        analytics_section = ""
        if analytics_insights:
            analytics_section = f"""{analytics_insights}

"""

        # Anniversary line
        anniversary_line = f"記念日: {anniversary}\n" if anniversary else ""

        # Get prompt template from prompt service
        template = self.prompt_service.get_user_prompt_template()

        # Format template with variables
        prompt = template.format(
            date=date,
            decided=decided,
            url=url,
            anniversary_line=anniversary_line,
            remarks=remarks,
            pinecone_section=pinecone_section,
            similar_section=similar_section,
            analytics_section=analytics_section
        )

        return prompt

    def _parse_structured_output(self, response, result):
        """
        Parse structured JSON output from Claude's response

        Args:
            response: Claude API response with structured output
            result: Result dictionary to populate
        """
        print(f"\n{'='*60}")
        print(f"[DEBUG] _parse_structured_output() 開始")
        print(f"[DEBUG] レスポンスブロック数: {len(response.content)}")
        print(f"{'='*60}")

        try:
            # Get the JSON content from response
            for i, block in enumerate(response.content):
                block_type = getattr(block, 'type', 'unknown')
                print(f"\n[DEBUG] ブロック{i}: type={block_type}")

                if hasattr(block, 'type') and block.type == 'text':
                    block_text = block.text
                    print(f"[DEBUG] テキストブロック発見 (長さ: {len(block_text)}文字)")
                    print(f"[DEBUG] テキスト内容（最初の500文字）:")
                    print(f"{block_text[:500]}")
                    print(f"[DEBUG] ---")

                    # Extract JSON from code blocks if present
                    print(f"[DEBUG] JSON抽出処理開始...")
                    json_text = self._extract_json_from_text(block_text)
                    print(f"[DEBUG] 抽出されたJSON (長さ: {len(json_text)}文字):")
                    print(f"{json_text[:500]}")
                    print(f"[DEBUG] ---")

                    try:
                        json_data = json.loads(json_text)
                        print(f"[DEBUG] JSON パース成功！")
                        print(f"[DEBUG] JSONキー: {list(json_data.keys())}")

                        # Parse post_a
                        if 'post_a' in json_data:
                            post_a = json_data['post_a']
                            print(f"[DEBUG] post_a データ: {post_a}")

                            # Remove markdown formatting
                            text_a = self._clean_text(post_a['text'])
                            result['post_a'] = {
                                'text': text_a,
                                'character_count': len(text_a),
                                'is_valid': len(text_a) <= 280
                            }
                            print(f"✅ [案A取得成功] {len(text_a)}文字")
                            print(f"   内容: {text_a[:100]}...")
                        else:
                            print(f"⚠️  [警告] post_a キーが見つかりません")

                        # Parse post_b
                        if 'post_b' in json_data:
                            post_b = json_data['post_b']
                            print(f"[DEBUG] post_b データ: {post_b}")

                            # Remove markdown formatting
                            text_b = self._clean_text(post_b['text'])
                            result['post_b'] = {
                                'text': text_b,
                                'character_count': len(text_b),
                                'is_valid': len(text_b) <= 280
                            }
                            print(f"✅ [案B取得成功] {len(text_b)}文字")
                            print(f"   内容: {text_b[:100]}...")
                        else:
                            print(f"⚠️  [警告] post_b キーが見つかりません")

                        break

                    except json.JSONDecodeError as json_err:
                        print(f"❌ [エラー] JSON パース失敗: {json_err}")
                        print(f"[DEBUG] パース失敗したテキスト: {block_text[:500]}...")
                        print(f"[INFO] レガシー抽出メソッドにフォールバック中...")
                        self._extract_two_posts_legacy(block_text, result)
                        break

                elif hasattr(block, 'type'):
                    print(f"[DEBUG] ブロックタイプ '{block_type}' はテキストではありません")

        except json.JSONDecodeError as e:
            print(f"\n❌ [JSON DECODE ERROR] {e}")
            print(f"[INFO] レガシー抽出メソッドにフォールバック")
            # Fallback to text extraction if JSON fails
            for block in response.content:
                if hasattr(block, 'type') and block.type == 'text':
                    print(f"[DEBUG] レガシー抽出を実行: {block.text[:200]}...")
                    self._extract_two_posts_legacy(block.text, result)
                    break
        except Exception as e:
            print(f"\n❌ [CRITICAL ERROR] 予期しないエラー: {e}")
            import traceback
            traceback.print_exc()

        finally:
            print(f"\n{'='*60}")
            print(f"[DEBUG] _parse_structured_output() 終了")
            print(f"[DEBUG] 最終結果:")
            print(f"   post_a: {'あり' if result.get('post_a') else 'なし'}")
            print(f"   post_b: {'あり' if result.get('post_b') else 'なし'}")
            if result.get('post_a'):
                print(f"   post_a 文字数: {result['post_a'].get('character_count', 0)}")
            if result.get('post_b'):
                print(f"   post_b 文字数: {result['post_b'].get('character_count', 0)}")
            print(f"{'='*60}\n")

    def _clean_text(self, text):
        """
        Remove markdown formatting from text

        Args:
            text: Text with potential markdown

        Returns:
            str: Cleaned text
        """
        # Remove **bold**
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        # Remove *italic*
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        return text.strip()

    def _extract_json_from_text(self, text):
        """
        Extract JSON from text, handling code blocks like ```json ... ```

        Args:
            text: Text that may contain JSON or JSON in code blocks

        Returns:
            str: Extracted JSON text with fixed control characters
        """
        extracted_json = None

        # Try to extract from ```json ... ``` code block (more flexible regex)
        # Matches: ```json\n{...}\n``` or ```json\n{...}``` or ```json{...}```
        json_match = re.search(r'```json\s*(.*?)```', text, re.DOTALL)
        if json_match:
            print(f"[DEBUG] JSONコードブロックから抽出")
            extracted_json = json_match.group(1).strip()

        # Try to extract from ``` ... ``` code block without json keyword
        if not extracted_json:
            code_match = re.search(r'```\s*(.*?)```', text, re.DOTALL)
            if code_match:
                potential_json = code_match.group(1).strip()
                # Check if it starts with { or [
                if potential_json.startswith('{') or potential_json.startswith('['):
                    print(f"[DEBUG] 汎用コードブロックからJSON抽出")
                    extracted_json = potential_json

        # Try to find JSON object directly (as fallback)
        if not extracted_json:
            json_direct = re.search(r'\{.*\}', text, re.DOTALL)
            if json_direct:
                print(f"[DEBUG] テキスト内から直接JSON抽出")
                extracted_json = json_direct.group(0)

        # No JSON found, return as is (will likely fail JSON parsing)
        if not extracted_json:
            print(f"[WARNING] JSONが見つからない、元のテキストを返す")
            return text.strip()

        # Fix control characters in JSON (newlines, tabs, etc.)
        print(f"[DEBUG] JSON制御文字のエスケープ処理開始...")
        fixed_json = self._fix_json_control_chars(extracted_json)
        print(f"[DEBUG] エスケープ処理完了")

        return fixed_json

    def _fix_json_control_chars(self, json_text):
        """
        Fix unescaped control characters in JSON string values

        Claude sometimes returns JSON with raw newlines in text values,
        which causes JSON parsing to fail. This method escapes those.

        Args:
            json_text: JSON text with potential unescaped control chars

        Returns:
            str: Fixed JSON text with properly escaped control characters
        """
        def escape_text_value(match):
            """Escape control characters in "text": "..." values"""
            prefix = match.group(1)   # "text": "
            content = match.group(2)  # The actual text content (may have newlines)
            suffix = match.group(3)   # "

            # Escape control characters in the correct order
            # (backslash first to avoid double-escaping)
            if '\\' not in content or '\n' in content or '\r' in content:
                # Only escape if there are actual control chars to escape
                content = content.replace('\\', '\\\\')  # Escape existing backslashes
                content = content.replace('\n', '\\n')   # Escape newlines
                content = content.replace('\r', '\\r')   # Escape carriage returns
                content = content.replace('\t', '\\t')   # Escape tabs
                print(f"[DEBUG] 制御文字をエスケープしました ({len(content)}文字)")

            return prefix + content + suffix

        # Pattern to match: "text" : " ... " (with any whitespace, capturing content)
        # Group 1: "text": "
        # Group 2: content (can include newlines with re.DOTALL)
        # Group 3: " (followed by comma or closing brace)
        pattern = r'("text"\s*:\s*")(.*?)("\s*[,}])'

        fixed = re.sub(pattern, escape_text_value, json_text, flags=re.DOTALL)

        return fixed

    def _extract_two_posts_legacy(self, text, result):
        """
        Legacy method: Extract two post options from Claude's response using regex
        Used as fallback if structured output fails

        Args:
            text: Response text
            result: Result dictionary to populate
        """
        # Extract 案A
        match_a = re.search(r'\[案A\](.*?)(?=\[案B\]|\[|$)', text, re.DOTALL)
        if match_a:
            post_a_text = self._clean_text(match_a.group(1))
            result['post_a'] = {
                'text': post_a_text,
                'character_count': len(post_a_text),
                'is_valid': len(post_a_text) <= 280
            }
            print(f"\n[案A抽出(レガシー)] {len(post_a_text)}文字")

        # Extract 案B
        match_b = re.search(r'\[案B\](.*?)(?=\[|$)', text, re.DOTALL)
        if match_b:
            post_b_text = self._clean_text(match_b.group(1))
            result['post_b'] = {
                'text': post_b_text,
                'character_count': len(post_b_text),
                'is_valid': len(post_b_text) <= 280
            }
            print(f"[案B抽出(レガシー)] {len(post_b_text)}文字")

    def _log_web_search_results(self, response):
        """
        Log web search results from Claude's response

        Args:
            response: Claude API response
        """
        try:
            for block in response.content:
                # Check for web search tool use
                if hasattr(block, 'type') and block.type == 'tool_use':
                    if hasattr(block, 'name') and block.name == 'web_search':
                        print(f"\n[WEB] Web Search実行:")
                        if hasattr(block, 'input') and 'query' in block.input:
                            print(f"   検索クエリ: {block.input['query']}")

                # Check for search results in content
                if hasattr(block, 'type') and block.type == 'tool_result':
                    if hasattr(block, 'content'):
                        try:
                            # Try to parse tool result
                            content_str = str(block.content)
                            if 'url' in content_str.lower() or 'http' in content_str:
                                print(f"   取得元: {content_str[:200]}...")
                        except:
                            pass

        except Exception as e:
            # Silent fail - logging is optional
            pass

    def _process_tool_use(self, response):
        """
        Process tool use in Claude's response

        Args:
            response: Claude API response

        Returns:
            list: Tool results to send back to Claude
        """
        tool_outputs = []

        for block in response.content:
            if hasattr(block, 'type') and block.type == 'tool_use':
                print(f"ツール使用検出: {block.name}")

                if block.name == 'tweet_length_checker':
                    text = block.input.get('text', '')

                    try:
                        api_response = requests.post(
                            self.tweet_checker_api,
                            json={"text": text},
                            timeout=10
                        )

                        if api_response.status_code == 200:
                            api_result = api_response.json()
                            print(f"文字数チェック結果: {api_result}")

                            tool_outputs.append({
                                'type': 'tool_result',
                                'tool_use_id': block.id,
                                'content': json.dumps(api_result)
                            })
                        else:
                            # Fallback
                            char_count = len(text)
                            is_valid = char_count <= 280

                            tool_outputs.append({
                                'type': 'tool_result',
                                'tool_use_id': block.id,
                                'content': json.dumps({
                                    "character_count": char_count,
                                    "is_valid": is_valid
                                })
                            })

                    except Exception as e:
                        print(f"文字数チェックエラー: {e}")
                        # Fallback
                        char_count = len(text)
                        tool_outputs.append({
                            'type': 'tool_result',
                            'tool_use_id': block.id,
                            'content': json.dumps({
                                "character_count": char_count,
                                "is_valid": char_count <= 280,
                                "error": str(e)
                            })
                        })

        return tool_outputs

    def refine_emojis(self, original_text, emoji_guidelines):
        """
        Refine emoji usage in post based on X Analytics performance data

        Args:
            original_text: Original post text
            emoji_guidelines: Emoji guidelines from AnalyticsService.get_emoji_guidelines()

        Returns:
            dict: {
                'original': str,
                'improved': str,
                'changes': [{'from': '💙', 'to': '🚨', 'reason': '...'}],
                'character_count': int,
                'is_valid': bool
            }
        """
        print(f"\n[INFO] 絵文字改善プロセス開始...")
        print(f"   元テキスト長: {len(original_text)}文字")

        # Build prompt with guidelines
        guidelines_text = emoji_guidelines.get('guidelines_text', '')

        system_prompt = f"""あなたはX（旧Twitter）の絵文字最適化エキスパートです。

{guidelines_text}

【タスク】
与えられた投稿の絵文字を、X Analyticsの実績データに基づいて最適化してください。

【ルール】
1. 投稿の**意味や文脈は変えない**（絵文字のみ変更）
2. 1投稿あたり絵文字は2-4個まで
3. 高エンゲージメント絵文字に置き換える
4. 低エンゲージメント絵文字は削除または置き換え
5. 絵文字は文脈に自然に溶け込むように配置
6. 文字数制限（280文字）を超えないようにする

【出力形式】
JSONで以下の形式で出力:
{{
  "improved_text": "改善後の投稿テキスト",
  "changes": [
    {{"from": "元の絵文字", "to": "新しい絵文字", "reason": "変更理由"}}
  ],
  "reasoning": "改善の意図と期待される効果"
}}"""

        user_message = f"""以下の投稿の絵文字を最適化してください：

【元の投稿】
{original_text}

X Analyticsデータに基づいて、エンゲージメント率が高まるように絵文字を改善してください。"""

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            # Parse response
            result_text = ""
            for block in response.content:
                if block.type == "text":
                    result_text += block.text

            print(f"[DEBUG] Claude応答: {result_text[:200]}...")

            # Extract JSON
            json_match = re.search(r'\{[\s\S]*"improved_text"[\s\S]*\}', result_text)
            if json_match:
                result_json = json.loads(json_match.group())

                improved_text = result_json.get('improved_text', original_text)
                changes = result_json.get('changes', [])
                reasoning = result_json.get('reasoning', '')

                # Check character count with tweet_length_checker
                char_count, is_valid = self._check_tweet_length(improved_text)

                print(f"[OK] 絵文字改善完了")
                print(f"   改善後文字数: {char_count}文字")
                print(f"   変更箇所: {len(changes)}件")

                return {
                    'original': original_text,
                    'improved': improved_text,
                    'changes': changes,
                    'reasoning': reasoning,
                    'character_count': char_count,
                    'is_valid': is_valid
                }

            else:
                print(f"[WARN]  JSON抽出失敗、元テキストを返却")
                char_count, is_valid = self._check_tweet_length(original_text)
                return {
                    'original': original_text,
                    'improved': original_text,
                    'changes': [],
                    'reasoning': 'JSON解析に失敗しました',
                    'character_count': char_count,
                    'is_valid': is_valid
                }

        except Exception as e:
            print(f"[ERROR] 絵文字改善エラー: {e}")
            import traceback
            traceback.print_exc()

            char_count, is_valid = self._check_tweet_length(original_text)
            return {
                'original': original_text,
                'improved': original_text,
                'changes': [],
                'reasoning': f'エラー: {str(e)}',
                'character_count': char_count,
                'is_valid': is_valid,
                'error': str(e)
            }

    def _check_tweet_length(self, text):
        """
        Check tweet length using tweet_length_checker API

        Args:
            text: Text to check

        Returns:
            tuple: (character_count, is_valid)
        """
        try:
            response = requests.post(
                self.tweet_checker_url,
                json={"text": text},
                timeout=10
            )
            data = response.json()
            return data.get('weightedLength', len(text)), data.get('isValid', len(text) <= 280)
        except Exception as e:
            print(f"[WARN] Tweet length check failed: {e}")
            return len(text), len(text) <= 280
