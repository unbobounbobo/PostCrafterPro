"""
Integrated RAG service combining Pinecone, past posts, and X analytics
"""
from app.services.pinecone_service import PineconeService
from app.services.sheets_service import SheetsService
from app.services.embedding_service import EmbeddingService
from app.services.analytics_service import AnalyticsService


class RAGService:
    """
    Unified RAG service that combines:
    1. Pinecone (Midori Anzen website data)
    2. Google Sheets (past posts)
    3. X Analytics (performance insights)
    """

    def __init__(self):
        """Initialize all RAG components"""
        # Pinecone temporarily disabled
        print("[INFO] Pinecone service disabled (temporary)")
        self.pinecone = None

        # Uncomment below to re-enable Pinecone
        # try:
        #     self.pinecone = PineconeService()
        #     print("[OK] Pinecone service connected")
        # except Exception as e:
        #     print(f"[WARN] Pinecone service unavailable: {e}")
        #     self.pinecone = None

        try:
            self.sheets = SheetsService()
            print("[OK] Sheets service connected")
        except Exception as e:
            print(f"[WARN] Sheets service unavailable: {e}")
            self.sheets = None

        try:
            self.embedding = EmbeddingService()
            print("[OK] Embedding service connected")
        except Exception as e:
            print(f"[WARN] Embedding service unavailable: {e}")
            self.embedding = None

        try:
            self.analytics = AnalyticsService()
            print("[OK] Analytics service connected")
        except Exception as e:
            print(f"[WARN] Analytics service unavailable: {e}")
            self.analytics = None

    def get_comprehensive_context(self, url=None, decided=None, anniversary=None):
        """
        Get comprehensive context from all sources

        Args:
            url: Product URL
            decided: Decided content
            anniversary: Anniversary information

        Returns:
            dict: {
                'pinecone_results': [...],
                'similar_posts': [...],
                'analytics_insights': str,
                'context_summary': str
            }
        """
        context = {
            'pinecone_results': [],
            'similar_posts': [],
            'analytics_insights': '',
            'context_summary': ''
        }

        # 1. Search Pinecone (product info)
        if self.pinecone and url:
            try:
                # Check if multiple URLs (comma-separated)
                if ',' in url:
                    # Use multiple URL search
                    pinecone_results = self.pinecone.search_by_multiple_urls(
                        urls=url,
                        top_k_per_url=3,
                        total_top_k=5
                    )
                    context['pinecone_results'] = pinecone_results
                else:
                    # Single URL search
                    pinecone_results = self.pinecone.search_by_url(url, top_k=5)
                    context['pinecone_results'] = pinecone_results

                # Also search by keywords if decided is provided
                if decided:
                    keyword_results = self.pinecone.search_by_keywords(decided, top_k=3)
                    # Merge unique results
                    existing_ids = {r['id'] for r in context['pinecone_results']}
                    for result in keyword_results:
                        if result['id'] not in existing_ids:
                            context['pinecone_results'].append(result)
                            existing_ids.add(result['id'])

            except Exception as e:
                print(f"Error in Pinecone search: {e}")

        # 2. Search past posts (semantic search)
        if self.sheets and self.embedding and decided:
            try:
                print(f"\n[INFO] 過去投稿の検索を開始...")
                print(f"   クエリ: {decided}")
                similar_posts = self.find_similar_posts(decided, top_k=5)
                context['similar_posts'] = similar_posts
                print(f"✅ [完了] 類似投稿 {len(similar_posts)}件 取得")

            except Exception as e:
                print(f"❌ [エラー] 過去投稿検索でエラー: {e}")
                import traceback
                traceback.print_exc()

        # 3. Anniversary-based search
        if self.sheets and self.embedding and anniversary:
            try:
                anniversary_posts = self.find_similar_posts(anniversary, top_k=3)
                # Merge with existing similar posts
                existing_texts = {p.get('text', '') for p in context['similar_posts']}
                for post in anniversary_posts:
                    post_text = post.get('text', post.get('最終投稿', ''))
                    if post_text and post_text not in existing_texts:
                        context['similar_posts'].append(post)

            except Exception as e:
                print(f"Error in anniversary search: {e}")

        # 4. Get X Analytics insights (NEW)
        if self.analytics and decided:
            try:
                # Extract keywords from decided content
                analytics_context = self.analytics.create_prompt_context(theme=decided)
                context['analytics_insights'] = analytics_context
                print("[OK] X Analytics insights generated")

            except Exception as e:
                print(f"Error getting analytics insights: {e}")

        # 5. Create context summary
        context['context_summary'] = self._create_summary(context)

        return context

    def find_similar_posts(self, query, top_k=5):
        """
        Find similar past posts using semantic search

        Args:
            query: Query text
            top_k: Number of results

        Returns:
            list: Similar posts with similarity scores
        """
        print(f"\n[DEBUG] find_similar_posts() 開始")
        print(f"   sheets: {'あり' if self.sheets else 'なし'}")
        print(f"   embedding: {'あり' if self.embedding else 'なし'}")
        print(f"   query: {query}")

        if not self.sheets or not self.embedding:
            print(f"⚠️  [警告] sheets または embedding サービスが利用できません")
            return []

        try:
            # Get all past posts
            print(f"[INFO] Google Sheetsから過去投稿を取得中...")
            past_posts = self.sheets.get_past_posts(limit=100)
            print(f"[INFO] 取得した過去投稿数: {len(past_posts) if past_posts else 0}件")

            if not past_posts:
                print(f"⚠️  [警告] 過去投稿が見つかりませんでした")
                return []

            # Extract post texts
            post_texts = []
            post_data = []

            print(f"[INFO] 投稿テキストを抽出中...")

            # デバッグ: 最初の5件を表示
            for i, post in enumerate(past_posts[:5]):
                post_text = (
                    post.get('最終投稿', '') or
                    post.get('ツイート本文', '') or
                    post.get('text', '') or
                    post.get('投稿本文', '') or
                    post.get('内容', '')
                )
                print(f"   投稿{i+1}: キー={list(post.keys())[:5]}..., テキスト長={len(post_text)}")

            # 実際の処理: 全件をループ
            for post in past_posts:
                # Try different field names (including X Analytics format)
                post_text = (
                    post.get('最終投稿', '') or           # PostCrafterPro完成版
                    post.get('ツイート本文', '') or       # X Analytics tweet sheet
                    post.get('text', '') or               # Generic
                    post.get('投稿本文', '') or           # Alternative
                    post.get('内容', '')                  # Alternative
                )

                if post_text and len(post_text) > 10:  # Minimum length
                    post_texts.append(post_text)
                    post_data.append(post)

            print(f"[INFO] 有効な投稿テキスト数: {len(post_texts)}件")

            if not post_texts:
                print(f"⚠️  [警告] 有効な投稿テキストが見つかりませんでした")
                return []

            # Find most similar using embeddings
            print(f"[INFO] エンベディングで類似度計算中...")
            similar = self.embedding.find_most_similar(query, post_texts, top_k)
            print(f"[INFO] 類似投稿 {len(similar)}件 取得")

            # Combine with original post data
            results = []
            for text, score in similar:
                # Find matching post data
                for post in post_data:
                    post_text = (
                        post.get('最終投稿', '') or           # PostCrafterPro完成版
                        post.get('ツイート本文', '') or       # X Analytics tweet sheet
                        post.get('text', '') or               # Generic
                        post.get('投稿本文', '')              # Alternative
                    )
                    if post_text == text:
                        results.append({
                            **post,
                            'text': text,
                            'similarity_score': score
                        })
                        break

            print(f"✅ [完了] find_similar_posts() 終了: {len(results)}件")
            return results

        except Exception as e:
            print(f"❌ [エラー] find_similar_posts()でエラー: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _create_summary(self, context):
        """
        Create a summary from context

        Args:
            context: Context dictionary

        Returns:
            str: Summary text
        """
        summary_parts = []

        # Pinecone results summary
        if context['pinecone_results']:
            pinecone_summary = "【商品情報】\n"
            for i, result in enumerate(context['pinecone_results'][:3], 1):
                title = result.get('title', '')
                desc = result.get('description', '')
                if title or desc:
                    pinecone_summary += f"{i}. {title}: {desc[:100]}\n"

            summary_parts.append(pinecone_summary)

        # Past posts summary
        if context['similar_posts']:
            posts_summary = "【類似の過去投稿】\n"
            for i, post in enumerate(context['similar_posts'][:3], 1):
                text = post.get('text', post.get('最終投稿', ''))
                score = post.get('similarity_score', 0)
                if text:
                    posts_summary += f"{i}. (類似度{score:.2f}) {text[:80]}...\n"

            summary_parts.append(posts_summary)

        return '\n'.join(summary_parts)
