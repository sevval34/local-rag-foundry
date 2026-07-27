import json
import sqlite3
import numpy as np
from ingest import DB_PATH, get_embedding_client, get_sdk_manager

def cosine_similarity(v1, v2):
    """
    İki vektör arasındaki kosinüs benzerliğini hesaplar.
    """
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))

def get_top_chunks(query, top_k=3):
    """
    Sorguyu alır, embedding'e dönüştürür, veritabanındaki tüm dökümanlarla
    benzerliklerini karşılaştırır ve en yakın top-k dökümanı döndürür.
    """
    # Güvenli şekilde SDK manager'ı al
    manager = get_sdk_manager()
    
    # Embedding client nesnesini al
    embedding_client = get_embedding_client(manager)
    
    # Sorgunun vektörünü çıkar
    response = embedding_client.generate_embedding(query)
    query_vector = np.array(response.data[0].embedding)
    
    # Veritabanındaki dökümanları çek
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT text, embedding FROM documents")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("Veritabanında hiç döküman bulunamadı. Lütfen önce veri yükleme (ingest) işlemini yapın.")
        return []
        
    # Her bir döküman ile kosinüs benzerliğini hesapla
    scored_chunks = []
    for text, embedding_str in rows:
        doc_vector = np.array(json.loads(embedding_str))
        similarity = cosine_similarity(query_vector, doc_vector)
        scored_chunks.append((text, similarity))
        
    # Benzerlik skoruna göre azalan sırada sırala
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    
    # En yüksek top-k benzerliğe sahip parçaları al
    top_chunks = scored_chunks[:top_k]
    
    return top_chunks

if __name__ == "__main__":
    # Küçük bir yerel doğrulama testi
    try:
        results = get_top_chunks("RAG nedir ne işe yarar?")
        print("\nTest Arama Sonuçları:")
        for idx, (text, score) in enumerate(results):
            print(f"\n[{idx+1}] Skor: {score:.4f}")
            print(text)
    except Exception as e:
        print(f"Hata oluştu: {e}")
