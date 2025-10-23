"""
Embedding generation service using Claude API
"""
import os
from anthropic import Anthropic
import numpy as np


class EmbeddingService:
    """
    Generate embeddings for semantic search
    Compatible with Pinecone (1536 dimensions)
    """

    def __init__(self):
        """Initialize Anthropic client for embeddings"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.client = Anthropic(api_key=api_key)
        self.cache = {}  # Simple in-memory cache

        print("[OK] Embedding Service initialized")

    def create_embedding(self, text):
        """
        Create embedding vector for text

        Args:
            text: Text to embed

        Returns:
            list: 1536-dimensional embedding vector
        """
        # Check cache
        cache_key = text[:100]  # Use first 100 chars as key
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Use Claude's voyage-3-lite model (1536 dimensions)
            response = self.client.embeddings.create(
                model="voyage-3-lite",
                input=[text]
            )

            embedding = response.embeddings[0]

            # Cache result
            self.cache[cache_key] = embedding

            return embedding

        except Exception as e:
            print(f"Error creating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536

    def batch_embed(self, texts, batch_size=20):
        """
        Embed multiple texts in batches

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch

        Returns:
            list: List of embedding vectors
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                response = self.client.embeddings.create(
                    model="voyage-3-lite",
                    input=batch
                )

                batch_embeddings = response.embeddings
                embeddings.extend(batch_embeddings)

            except Exception as e:
                print(f"Error in batch embedding: {e}")
                # Add zero vectors for failed batch
                embeddings.extend([[0.0] * 1536] * len(batch))

        return embeddings

    def cosine_similarity(self, vec1, vec2):
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1, vec2: Embedding vectors

        Returns:
            float: Similarity score (0-1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        # Normalize
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-10)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-10)

        # Cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)

        return float(similarity)

    def find_most_similar(self, query_text, texts, top_k=5):
        """
        Find most similar texts to query

        Args:
            query_text: Query text
            texts: List of texts to search
            top_k: Number of results to return

        Returns:
            list: [(text, similarity_score), ...]
        """
        # Embed query
        query_embedding = self.create_embedding(query_text)

        # Embed all texts
        text_embeddings = self.batch_embed(texts)

        # Calculate similarities
        similarities = []
        for i, text_embedding in enumerate(text_embeddings):
            similarity = self.cosine_similarity(query_embedding, text_embedding)
            similarities.append((texts[i], similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def clear_cache(self):
        """Clear embedding cache"""
        self.cache = {}
        print("Embedding cache cleared")
