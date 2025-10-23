"""
Pinecone RAG integration for PostCrafterPro

Searches the midori-anzen-v2 index (65,098 records) for relevant product information
"""
import os
from pinecone import Pinecone, ServerlessSpec
from anthropic import Anthropic


class PineconeService:
    """
    Pinecone vector database service for product information retrieval
    """

    def __init__(self):
        """Initialize Pinecone connection"""
        # Initialize Pinecone
        api_key = os.getenv('PINECONE_API_KEY')
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables")

        self.pc = Pinecone(api_key=api_key)

        # Connect to index
        self.index_name = os.getenv('PINECONE_INDEX_NAME', 'midori-anzen-v2')
        self.index_host = os.getenv('PINECONE_HOST')

        try:
            self.index = self.pc.Index(
                name=self.index_name,
                host=self.index_host
            )
            print(f"[OK] Connected to Pinecone index: {self.index_name}")

            # Get index stats
            stats = self.index.describe_index_stats()
            print(f"   Total vectors: {stats.get('total_vector_count', 0):,}")

        except Exception as e:
            print(f"[ERROR] Failed to connect to Pinecone: {e}")
            raise

        # Initialize Anthropic for embeddings
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            self.anthropic = Anthropic(api_key=anthropic_key)
        else:
            self.anthropic = None
            print("[WARN]  Warning: ANTHROPIC_API_KEY not found. Embedding generation disabled.")

    def _create_embedding(self, text):
        """
        Create embedding vector for text using Claude API

        Args:
            text: Text to embed

        Returns:
            list: 1536-dimensional embedding vector
        """
        if not self.anthropic:
            raise ValueError("Anthropic client not initialized")

        # Use Claude's embedding endpoint (voyage-3-lite model)
        # Dimensions: 1536 (compatible with Pinecone index)
        try:
            response = self.anthropic.embeddings.create(
                model="voyage-3-lite",
                input=[text]
            )
            return response.embeddings[0]

        except Exception as e:
            print(f"Error creating embedding: {e}")
            # Fallback: return zero vector
            return [0.0] * 1536

    def search_by_url(self, url, top_k=5):
        """
        Search for product information by URL

        Args:
            url: Product URL
            top_k: Number of results to return

        Returns:
            list: List of relevant product information
        """
        try:
            # Create embedding from URL
            query_vector = self._create_embedding(url)

            # Query Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True
            )

            # Format results
            formatted_results = []
            for match in results.get('matches', []):
                formatted_results.append({
                    'id': match.get('id'),
                    'score': match.get('score'),
                    'metadata': match.get('metadata', {}),
                    'title': match.get('metadata', {}).get('title', ''),
                    'description': match.get('metadata', {}).get('description', ''),
                    'content': match.get('metadata', {}).get('content', ''),
                    'url': match.get('metadata', {}).get('url', '')
                })

            return formatted_results

        except Exception as e:
            print(f"Error in Pinecone search by URL: {e}")
            return []

    def search_by_multiple_urls(self, urls, top_k_per_url=3, total_top_k=5):
        """
        Search for product information by multiple URLs

        Args:
            urls: List of product URLs or comma-separated string
            top_k_per_url: Number of results per URL
            total_top_k: Total number of results to return after merging

        Returns:
            list: List of relevant product information (deduplicated and sorted by score)
        """
        # Parse URLs if comma-separated string
        if isinstance(urls, str):
            url_list = [url.strip() for url in urls.split(',') if url.strip()]
        else:
            url_list = urls

        if not url_list:
            return []

        print(f"[INFO] Searching Pinecone for {len(url_list)} URLs...")

        all_results = []
        seen_ids = set()

        # Search each URL
        for url in url_list:
            try:
                results = self.search_by_url(url, top_k=top_k_per_url)

                # Add unique results
                for result in results:
                    if result['id'] not in seen_ids:
                        all_results.append(result)
                        seen_ids.add(result['id'])

            except Exception as e:
                print(f"[WARN] Error searching URL {url}: {e}")
                continue

        # Sort by score (descending)
        all_results.sort(key=lambda x: x['score'], reverse=True)

        # Return top K results
        final_results = all_results[:total_top_k]
        print(f"[OK] Found {len(final_results)} unique products from {len(url_list)} URLs")

        return final_results

    def search_by_keywords(self, keywords, top_k=5):
        """
        Search for information by keywords

        Args:
            keywords: Search keywords (string or list)
            top_k: Number of results to return

        Returns:
            list: List of relevant information
        """
        try:
            # Convert keywords to string if needed
            if isinstance(keywords, list):
                query_text = ' '.join(keywords)
            else:
                query_text = keywords

            # Create embedding from keywords
            query_vector = self._create_embedding(query_text)

            # Query Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True
            )

            # Format results
            formatted_results = []
            for match in results.get('matches', []):
                formatted_results.append({
                    'id': match.get('id'),
                    'score': match.get('score'),
                    'metadata': match.get('metadata', {}),
                    'title': match.get('metadata', {}).get('title', ''),
                    'description': match.get('metadata', {}).get('description', ''),
                    'content': match.get('metadata', {}).get('content', ''),
                    'url': match.get('metadata', {}).get('url', '')
                })

            return formatted_results

        except Exception as e:
            print(f"Error in Pinecone search by keywords: {e}")
            return []

    def get_product_context(self, url, keywords=None, top_k=5):
        """
        Get comprehensive product context from both URL and keywords

        Args:
            url: Product URL
            keywords: Additional keywords (optional)
            top_k: Number of results per search

        Returns:
            dict: Comprehensive product context
        """
        context = {
            'url_results': [],
            'keyword_results': [],
            'combined_summary': ''
        }

        # Search by URL
        if url:
            context['url_results'] = self.search_by_url(url, top_k)

        # Search by keywords
        if keywords:
            context['keyword_results'] = self.search_by_keywords(keywords, top_k)

        # Combine results for summary
        all_results = context['url_results'] + context['keyword_results']

        if all_results:
            # Create a summary from top results
            summaries = []
            seen_ids = set()

            for result in all_results[:top_k]:
                if result['id'] not in seen_ids:
                    seen_ids.add(result['id'])
                    summaries.append(f"- {result['title']}: {result['description']}")

            context['combined_summary'] = '\n'.join(summaries)

        return context

    def get_related_products(self, product_id, top_k=3):
        """
        Get related products based on product ID

        Args:
            product_id: Product ID in Pinecone
            top_k: Number of related products to return

        Returns:
            list: List of related products
        """
        try:
            # Fetch the product vector
            fetch_result = self.index.fetch(ids=[product_id])

            if not fetch_result.get('vectors'):
                return []

            # Get the vector
            product_vector = fetch_result['vectors'][product_id]['values']

            # Find similar vectors
            results = self.index.query(
                vector=product_vector,
                top_k=top_k + 1,  # +1 because the product itself will be in results
                include_metadata=True
            )

            # Filter out the product itself and format results
            formatted_results = []
            for match in results.get('matches', []):
                if match.get('id') != product_id:
                    formatted_results.append({
                        'id': match.get('id'),
                        'score': match.get('score'),
                        'metadata': match.get('metadata', {}),
                        'title': match.get('metadata', {}).get('title', ''),
                        'description': match.get('metadata', {}).get('description', '')
                    })

            return formatted_results[:top_k]

        except Exception as e:
            print(f"Error getting related products: {e}")
            return []
