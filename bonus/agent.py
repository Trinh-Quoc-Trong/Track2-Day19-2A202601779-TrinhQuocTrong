import uuid
from typing import Optional

from fastembed import TextEmbedding
from feast import FeatureStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams


class HybridMemoryAgent:
    """
    A Hybrid Memory Agent that combines Episodic Memory (Qdrant Vector Store) 
    with a Stable Profile (Feast Feature Store).
    """
    def __init__(self, qdrant_client: QdrantClient, feature_store: FeatureStore, embedder: TextEmbedding):
        self.client = qdrant_client
        self.fs = feature_store
        self.embedder = embedder
        self.collection_name = "episodic_memory"
        
        # Ensure collection exists
        existing = {c.name for c in self.client.get_collections().collections}
        if self.collection_name not in existing:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def remember(self, text: str, user_id: str = "u_001") -> None:
        """Add a new piece of episodic memory for this user."""
        # Simple per-message chunking for POC
        vector = next(self.embedder.embed([text])).tolist()
        point_id = str(uuid.uuid4())
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"user_id": user_id, "text": text}
                )
            ]
        )

    def recall(self, query: str, user_id: str = "u_001") -> str:
        """Retrieve top-K memories + user profile features → return assembled context."""
        
        # 1. Get user profile + recent activity from Feast online store
        features = None
        try:
            fs_response = self.fs.get_online_features(
                features=[
                    "user_profile_features:reading_speed_wpm",
                    "user_profile_features:preferred_language",
                    "user_profile_features:topic_affinity",
                    "query_velocity_features:queries_last_hour",
                ],
                entity_rows=[{"user_id": user_id}],
            ).to_dict()
            features = {k: v[0] for k, v in fs_response.items()}
        except Exception:
            # Fallback if feast data is not fully populated for the given user
            pass

        # 2. Semantic search Qdrant filtered by user_id to prevent data leakage
        q_vec = next(self.embedder.embed([query])).tolist()
        
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=q_vec,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            ),
            limit=3
        )
        
        top_memories = [hit.payload["text"] for hit in search_result.points]
        
        # 3. Assemble context string
        context_parts = []
        if features and features.get('topic_affinity'):
            context_parts.append(
                f"User likes {features.get('topic_affinity')} "
                f"reading at {features.get('reading_speed_wpm')}wpm."
            )
            context_parts.append(
                f"Recent activity: {features.get('queries_last_hour')} queries last hour."
            )
        else:
            context_parts.append("User Profile: Not found.")
            
        context_parts.append(f"Top memories for query '{query}':")
        if top_memories:
            for i, mem in enumerate(top_memories, 1):
                context_parts.append(f"  {i}. {mem}")
        else:
            context_parts.append("  (No relevant episodic memories found)")
            
        return "\n".join(context_parts)
