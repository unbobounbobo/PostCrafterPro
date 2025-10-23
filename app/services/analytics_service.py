"""
X Analytics Service for PostCrafterPro
Analyze past tweet performance to inform new post creation
"""
from app.services.sheets_service import SheetsService
import statistics


class AnalyticsService:
    """
    Analyze X (Twitter) analytics data to identify high-performing content patterns
    """

    def __init__(self):
        """Initialize analytics service"""
        self.sheets = SheetsService()
        self.tweet_data = []  # 投稿別データ (tweetシート)
        self.daily_data = []  # 日次データ (dayシート)
        self._load_analytics()

    def _load_analytics(self):
        """Load all analytics data from tweet and day sheets"""
        # Load tweet data (投稿別パフォーマンス)
        if not self.sheets.analytics_sheet:
            print("[WARN]  Tweet analytics sheet not available")
        else:
            try:
                self.tweet_data = self.sheets.get_past_posts(limit=None)  # Get all tweets
                print(f"[OK] Loaded {len(self.tweet_data)} tweets from X analytics")
            except Exception as e:
                print(f"[ERROR] Error loading tweet data: {e}")

        # Load daily data (日次統計)
        if not self.sheets.analytics_day_sheet:
            print("[WARN]  Daily analytics sheet not available")
        else:
            try:
                self.daily_data = self.sheets.get_daily_stats(limit=None)  # Get all days
                print(f"[OK] Loaded {len(self.daily_data)} days from X analytics")
            except Exception as e:
                print(f"[ERROR] Error loading daily data: {e}")

    def get_top_performing_posts(self, limit=10, metric='エンゲージメント率'):
        """
        Get top performing posts by specified metric

        Args:
            limit: Number of posts to return
            metric: Metric to sort by ('エンゲージメント率', 'インプレッション', 'エンゲージメント', 'いいね')

        Returns:
            list: Top performing posts
        """
        if not self.tweet_data:
            return []

        try:
            # Filter posts with valid metrics
            valid_posts = [
                post for post in self.tweet_data
                if post.get(metric) and post.get('ツイート本文')
            ]

            # Convert metric to float for sorting
            for post in valid_posts:
                try:
                    post['_sort_value'] = float(post[metric])
                except (ValueError, TypeError):
                    post['_sort_value'] = 0

            # Sort by metric (descending)
            sorted_posts = sorted(valid_posts, key=lambda x: x['_sort_value'], reverse=True)

            # Return top N
            return sorted_posts[:limit]

        except Exception as e:
            print(f"Error getting top posts: {e}")
            return []

    def analyze_content_patterns(self, top_n=50):
        """
        Analyze patterns in high-performing content

        Args:
            top_n: Number of top posts to analyze

        Returns:
            dict: Analysis results
        """
        top_posts = self.get_top_performing_posts(limit=top_n)

        if not top_posts:
            return {}

        analysis = {
            'average_length': 0,
            'has_url_percentage': 0,
            'has_hashtag_percentage': 0,
            'common_themes': [],
            'average_engagement_rate': 0,
            'sample_posts': []
        }

        # Calculate averages
        lengths = []
        engagement_rates = []
        has_url_count = 0
        has_hashtag_count = 0

        for post in top_posts:
            text = post.get('ツイート本文', '')

            # Length
            lengths.append(len(text))

            # Engagement rate
            try:
                engagement_rate = float(post.get('エンゲージメント率', 0))
                engagement_rates.append(engagement_rate)
            except (ValueError, TypeError):
                pass

            # Has URL
            if 'http' in text:
                has_url_count += 1

            # Has hashtag
            if '#' in text:
                has_hashtag_count += 1

        # Calculate statistics
        if lengths:
            analysis['average_length'] = int(statistics.mean(lengths))
        if engagement_rates:
            analysis['average_engagement_rate'] = statistics.mean(engagement_rates)
        analysis['has_url_percentage'] = (has_url_count / len(top_posts)) * 100
        analysis['has_hashtag_percentage'] = (has_hashtag_count / len(top_posts)) * 100

        # Sample top 5 posts
        analysis['sample_posts'] = [
            {
                'text': post.get('ツイート本文', ''),
                'engagement_rate': post.get('エンゲージメント率', 0),
                'impressions': post.get('インプレッション', 0),
                'likes': post.get('いいね', 0),
                'retweets': post.get('リツイート', 0)
            }
            for post in top_posts[:5]
        ]

        return analysis

    def find_similar_high_performers(self, keyword, limit=5):
        """
        Find high-performing posts similar to a keyword/theme

        Args:
            keyword: Keyword to search for
            limit: Number of results

        Returns:
            list: Similar high-performing posts
        """
        if not self.tweet_data:
            return []

        try:
            # Filter posts containing keyword
            matching_posts = [
                post for post in self.tweet_data
                if keyword and keyword.lower() in post.get('ツイート本文', '').lower()
            ]

            # Sort by engagement rate
            for post in matching_posts:
                try:
                    post['_engagement_rate'] = float(post.get('エンゲージメント率', 0))
                except (ValueError, TypeError):
                    post['_engagement_rate'] = 0

            sorted_posts = sorted(
                matching_posts,
                key=lambda x: x['_engagement_rate'],
                reverse=True
            )

            return sorted_posts[:limit]

        except Exception as e:
            print(f"Error finding similar posts: {e}")
            return []

    def get_daily_performance_trends(self, days=30):
        """
        Get daily performance trends

        Args:
            days: Number of recent days to analyze

        Returns:
            dict: Daily performance trends
        """
        if not self.daily_data:
            return {}

        try:
            recent_days = self.daily_data[-days:] if len(self.daily_data) > days else self.daily_data

            # Calculate averages
            total_impressions = 0
            total_engagement = 0
            total_engagement_rate = 0
            valid_days = 0

            for day in recent_days:
                try:
                    impressions = float(day.get('インプレッション', 0))
                    engagement = float(day.get('エンゲージメント', 0))
                    engagement_rate = float(day.get('エンゲージメント率', 0))

                    if impressions > 0:
                        total_impressions += impressions
                        total_engagement += engagement
                        total_engagement_rate += engagement_rate
                        valid_days += 1
                except (ValueError, TypeError):
                    continue

            if valid_days == 0:
                return {}

            return {
                'period_days': days,
                'avg_daily_impressions': total_impressions / valid_days,
                'avg_daily_engagement': total_engagement / valid_days,
                'avg_engagement_rate': total_engagement_rate / valid_days,
                'total_impressions': total_impressions,
                'total_engagement': total_engagement
            }

        except Exception as e:
            print(f"Error analyzing daily trends: {e}")
            return {}

    def get_performance_insights(self, theme=None):
        """
        Get actionable insights for new post creation

        Args:
            theme: Optional theme/keyword to focus on

        Returns:
            dict: Performance insights
        """
        insights = {
            'overall_stats': {},
            'content_recommendations': [],
            'top_examples': []
        }

        # Overall performance analysis
        overall_analysis = self.analyze_content_patterns(top_n=50)
        insights['overall_stats'] = overall_analysis

        # Content recommendations
        recommendations = []

        # Length recommendation
        avg_length = overall_analysis.get('average_length', 0)
        if avg_length > 0:
            recommendations.append(
                f"高エンゲージメント投稿の平均文字数は{avg_length}文字です。"
            )

        # URL recommendation
        url_pct = overall_analysis.get('has_url_percentage', 0)
        if url_pct > 50:
            recommendations.append(
                f"上位投稿の{url_pct:.0f}%がURLを含んでいます。商品URLの追加を推奨します。"
            )

        # Hashtag recommendation
        hashtag_pct = overall_analysis.get('has_hashtag_percentage', 0)
        if hashtag_pct > 30:
            recommendations.append(
                f"上位投稿の{hashtag_pct:.0f}%がハッシュタグを使用しています。"
            )

        insights['content_recommendations'] = recommendations

        # Theme-specific analysis
        if theme:
            similar_posts = self.find_similar_high_performers(theme, limit=3)
            if similar_posts:
                insights['top_examples'] = [
                    {
                        'text': post.get('ツイート本文', ''),
                        'engagement_rate': post.get('エンゲージメント率', 0),
                        'impressions': post.get('インプレッション', 0)
                    }
                    for post in similar_posts
                ]

        return insights

    def create_prompt_context(self, theme=None):
        """
        Create context string for Claude prompt based on analytics (tweet + day data)

        Args:
            theme: Optional theme/keyword

        Returns:
            str: Formatted context for prompt
        """
        insights = self.get_performance_insights(theme)
        daily_trends = self.get_daily_performance_trends(days=30)

        context_parts = ["【過去のX投稿パフォーマンス分析】\n"]

        # Daily performance trends (最近30日)
        if daily_trends:
            context_parts.append("《最近30日のトレンド》")
            context_parts.append(
                f"- 1日あたり平均インプレッション: {daily_trends['avg_daily_impressions']:.0f}"
            )
            context_parts.append(
                f"- 1日あたり平均エンゲージメント: {daily_trends['avg_daily_engagement']:.0f}"
            )
            context_parts.append(
                f"- 平均エンゲージメント率: {daily_trends['avg_engagement_rate']:.2%}"
            )
            context_parts.append("")

        # Overall stats from high-performing tweets
        stats = insights.get('overall_stats', {})
        if stats:
            context_parts.append("《高パフォーマンス投稿の特徴》")
            avg_length = stats.get('average_length', 0)
            avg_engagement = stats.get('average_engagement_rate', 0)

            context_parts.append(f"- 平均文字数: {avg_length}文字")
            context_parts.append(f"- 平均エンゲージメント率: {avg_engagement:.2%}")

            url_pct = stats.get('has_url_percentage', 0)
            hashtag_pct = stats.get('has_hashtag_percentage', 0)
            context_parts.append(f"- URL含有率: {url_pct:.0f}%")
            context_parts.append(f"- ハッシュタグ使用率: {hashtag_pct:.0f}%")
            context_parts.append("")

        # Recommendations
        recommendations = insights.get('content_recommendations', [])
        if recommendations:
            context_parts.append("《推奨事項》")
            for rec in recommendations:
                context_parts.append(f"- {rec}")
            context_parts.append("")

        # Top examples
        top_examples = insights.get('top_examples', [])
        if top_examples:
            context_parts.append("《類似テーマの高パフォーマンス投稿例》")
            for i, example in enumerate(top_examples, 1):
                engagement_rate = example.get('engagement_rate', 0)
                try:
                    engagement_pct = float(engagement_rate) * 100
                except (ValueError, TypeError):
                    engagement_pct = 0
                context_parts.append(
                    f"{i}. (エンゲージメント率: {engagement_pct:.2f}%, "
                    f"インプレッション: {example.get('impressions', 0):.0f})"
                )
                context_parts.append(f"   {example['text'][:120]}")
            context_parts.append("")

        # Sample top posts
        sample_posts = stats.get('sample_posts', [])
        if sample_posts and not top_examples:  # Only if no theme-specific examples
            context_parts.append("《全体の高パフォーマンス投稿例（Top 3）》")
            for i, post in enumerate(sample_posts[:3], 1):
                engagement_rate = post.get('engagement_rate', 0)
                try:
                    engagement_pct = float(engagement_rate) * 100
                except (ValueError, TypeError):
                    engagement_pct = 0
                context_parts.append(
                    f"{i}. (エンゲージメント率: {engagement_pct:.2f}%, "
                    f"いいね: {post.get('likes', 0)})"
                )
                context_parts.append(f"   {post['text'][:120]}")

        return "\n".join(context_parts)
