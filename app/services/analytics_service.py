"""
X Analytics Service for PostCrafterPro
Analyze past tweet performance to inform new post creation
"""
from app.services.sheets_service import SheetsService
import statistics
import re
from collections import defaultdict


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

    def _extract_emojis(self, text):
        """
        Extract all emojis from text

        Args:
            text: Text to extract emojis from

        Returns:
            list: List of emojis found in text
        """
        if not text:
            return []

        # Unicode emoji ranges
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # enclosed characters
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA00-\U0001FA6F"  # extended symbols
            "\U00002600-\U000026FF"  # miscellaneous symbols
            "]+",
            flags=re.UNICODE
        )

        emojis = emoji_pattern.findall(text)
        return emojis

    def analyze_emoji_performance(self, min_occurrences=5):
        """
        Analyze emoji performance based on X Analytics data

        Args:
            min_occurrences: Minimum number of times an emoji must appear to be included

        Returns:
            dict: {
                'top_emojis': [(emoji, avg_engagement_rate, count), ...],
                'low_emojis': [(emoji, avg_engagement_rate, count), ...],
                'emoji_stats': {emoji: {'avg_er': float, 'count': int, 'total_er': float}}
            }
        """
        print(f"\n[INFO] 絵文字パフォーマンス分析を開始...")
        print(f"   分析対象: {len(self.tweet_data)}件の投稿")

        if not self.tweet_data:
            print(f"[WARN]  分析データがありません")
            return {'top_emojis': [], 'low_emojis': [], 'emoji_stats': {}}

        # Collect emoji usage with engagement rates
        emoji_data = defaultdict(lambda: {'total_er': 0, 'count': 0, 'posts': []})

        for post in self.tweet_data:
            text = post.get('ツイート本文', '')
            if not text:
                continue

            # Get engagement rate
            try:
                engagement_rate = float(post.get('エンゲージメント率', 0))
            except (ValueError, TypeError):
                continue

            if engagement_rate == 0:
                continue

            # Extract emojis
            emojis = self._extract_emojis(text)

            # Record each emoji's performance
            for emoji in set(emojis):  # Use set to avoid duplicates in same post
                emoji_data[emoji]['total_er'] += engagement_rate
                emoji_data[emoji]['count'] += 1
                emoji_data[emoji]['posts'].append({
                    'text': text[:100],
                    'er': engagement_rate
                })

        print(f"[INFO] 発見した絵文字の種類: {len(emoji_data)}種類")

        # Calculate average engagement rate for each emoji
        emoji_stats = {}
        for emoji, data in emoji_data.items():
            if data['count'] >= min_occurrences:
                avg_er = data['total_er'] / data['count']
                emoji_stats[emoji] = {
                    'avg_er': avg_er,
                    'count': data['count'],
                    'total_er': data['total_er']
                }

        print(f"[INFO] 最低出現回数{min_occurrences}回以上の絵文字: {len(emoji_stats)}種類")

        if not emoji_stats:
            print(f"[WARN]  統計的に有意な絵文字データがありません")
            return {'top_emojis': [], 'low_emojis': [], 'emoji_stats': {}}

        # Sort by average engagement rate
        sorted_emojis = sorted(
            emoji_stats.items(),
            key=lambda x: x[1]['avg_er'],
            reverse=True
        )

        # Calculate median for threshold
        median_er = statistics.median([data['avg_er'] for data in emoji_stats.values()])
        print(f"[INFO] 絵文字使用時の中央エンゲージメント率: {median_er:.4f}")

        # Top and low performers
        top_emojis = [
            (emoji, data['avg_er'], data['count'])
            for emoji, data in sorted_emojis
            if data['avg_er'] > median_er
        ][:20]  # Top 20

        low_emojis = [
            (emoji, data['avg_er'], data['count'])
            for emoji, data in sorted_emojis
            if data['avg_er'] < median_er * 0.8  # 20% below median
        ][:20]  # Bottom 20

        print(f"[OK] 高パフォーマンス絵文字: {len(top_emojis)}種類")
        print(f"[OK] 低パフォーマンス絵文字: {len(low_emojis)}種類")

        return {
            'top_emojis': top_emojis,
            'low_emojis': low_emojis,
            'emoji_stats': emoji_stats,
            'median_er': median_er
        }

    def get_emoji_guidelines(self, min_occurrences=5, top_n=15):
        """
        Generate emoji usage guidelines based on X Analytics performance

        Args:
            min_occurrences: Minimum number of times an emoji must appear
            top_n: Number of top emojis to include in recommendations

        Returns:
            dict: {
                'recommended': [
                    {'emoji': '🚨', 'avg_er': 0.0456, 'count': 23, 'boost': '+35%'},
                    ...
                ],
                'avoid': [
                    {'emoji': '💙', 'avg_er': 0.0234, 'count': 12, 'impact': '-15%'},
                    ...
                ],
                'guidelines_text': str  # Formatted text for Claude prompt
            }
        """
        print(f"\n[INFO] 絵文字ガイドライン生成中...")

        # Analyze performance
        analysis = self.analyze_emoji_performance(min_occurrences=min_occurrences)

        if not analysis['emoji_stats']:
            return {
                'recommended': [],
                'avoid': [],
                'guidelines_text': '※ 絵文字パフォーマンスデータが不足しています'
            }

        median_er = analysis.get('median_er', 0)
        top_emojis = analysis['top_emojis'][:top_n]
        low_emojis = analysis['low_emojis'][:10]  # Top 10 to avoid

        # Format recommendations
        recommended = []
        for emoji, avg_er, count in top_emojis:
            boost = ((avg_er / median_er) - 1) * 100 if median_er > 0 else 0
            recommended.append({
                'emoji': emoji,
                'avg_er': avg_er,
                'count': count,
                'boost': f"+{boost:.0f}%"
            })

        # Format avoid list
        avoid = []
        for emoji, avg_er, count in low_emojis:
            impact = ((avg_er / median_er) - 1) * 100 if median_er > 0 else 0
            avoid.append({
                'emoji': emoji,
                'avg_er': avg_er,
                'count': count,
                'impact': f"{impact:.0f}%"
            })

        # Generate guidelines text for Claude prompt
        guidelines_parts = []
        guidelines_parts.append("【X実績に基づく絵文字ガイドライン】")
        guidelines_parts.append("")
        guidelines_parts.append("《高エンゲージメント絵文字 - 積極的に使用推奨》")
        for item in recommended[:10]:
            guidelines_parts.append(
                f"  {item['emoji']} (ER: {item['avg_er']:.4f}, {item['count']}回使用, "
                f"平均比{item['boost']})"
            )

        guidelines_parts.append("")
        guidelines_parts.append("《低エンゲージメント絵文字 - 使用を避ける》")
        for item in avoid[:5]:
            guidelines_parts.append(
                f"  {item['emoji']} (ER: {item['avg_er']:.4f}, {item['count']}回使用, "
                f"平均比{item['impact']})"
            )

        guidelines_parts.append("")
        guidelines_parts.append(f"※ 分析データ: {len(self.tweet_data)}件の投稿")
        guidelines_parts.append(f"※ 最低出現回数: {min_occurrences}回")

        guidelines_text = "\n".join(guidelines_parts)

        print(f"[OK] ガイドライン生成完了")
        print(f"   推奨絵文字: {len(recommended)}種類")
        print(f"   非推奨絵文字: {len(avoid)}種類")

        return {
            'recommended': recommended,
            'avoid': avoid,
            'guidelines_text': guidelines_text
        }
