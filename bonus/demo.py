import sys
from pathlib import Path
from fastembed import TextEmbedding
from feast import FeatureStore
from qdrant_client import QdrantClient

# Đảm bảo có thể import module từ thư mục gốc
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from bonus.agent import HybridMemoryAgent

def main():
    print("Khởi tạo Hybrid Memory Agent...")
    client = QdrantClient(":memory:")
    
    # Lấy FeatureStore từ thư mục repo đã setup trong bài Lab (NB4)
    feast_repo = ROOT / "app" / "feast_repo"
    try:
        fs = FeatureStore(repo_path=str(feast_repo))
    except Exception as e:
        print(f"Cảnh báo: Lỗi kết nối Feast FeatureStore: {e}")
        fs = None

    # Khởi tạo model embedding (dùng model nhỏ cho local)
    embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    agent = HybridMemoryAgent(client, fs, embedder)
    user_id = "u_001"
    
    print("\nThêm dữ liệu vào Episodic Memory (Qdrant Vector Store)...")
    memories = [
        "Tôi đã đọc một bài rất hay về Kubernetes và cách triển khai container.",
        "Tôi quan tâm đến bảo mật đám mây (cloud security) và các lỗ hổng OWASP.",
        "Tôi đang cấu hình tự động mở rộng (autoscaling) cho hạ tầng của công ty.",
    ]
    for m in memories:
        agent.remember(text=m, user_id=user_id)
        
    print(f"Đã ghi nhớ {len(memories)} sự kiện cho người dùng {user_id}.\n")
    
    queries = [
        "Tôi đã đọc gì về Kubernetes?",                                # 1. Vector hit
        "Recommend đọc gì tiếp?",                                      # 2. Profile context (affinity)
        "Tôi đang quan tâm gì gần đây?",                               # 3. Fresh activity (queries_last_hour)
        "Tài liệu về tự động mở rộng hạ tầng?",                        # 4. Paraphrase vector hit
        "Cho tôi summary cloud security"                               # 5. Mixed: episodic + profile
    ]
    
    for i, q in enumerate(queries, 1):
        print("=" * 70)
        print(f"Query {i}: {q}")
        print(">>> CONTEXT ASSEMBLED CHO LLM:")
        context = agent.recall(query=q, user_id=user_id)
        print(context)
    
    print("=" * 70)

if __name__ == "__main__":
    main()
