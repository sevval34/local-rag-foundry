import os
import json
import sqlite3
from foundry_local_sdk import Configuration, FoundryLocalManager

# Veritabanı ve veri dosyası yolları
DB_PATH = "documents.db"
DATA_PATH = "data.txt"

# Varsayılan model isimleri
DEFAULT_EMBEDDING_MODEL = "qwen3-embedding-0.6b"

def get_sdk_manager():
    """
    FoundryLocalManager'ı güvenli şekilde başlatır ve singleton örneği döndürür.
    Zaten başlatıldıysa mevcut örneği kullanır.
    """
    try:
        manager = FoundryLocalManager.instance
        if manager is not None:
            return manager
    except Exception:
        pass
        
    try:
        config = Configuration(app_name="local_rag_app")
        FoundryLocalManager.initialize(config)
        return FoundryLocalManager.instance
    except Exception as e:
        if "already" in str(e).lower():
            return FoundryLocalManager.instance
        raise e

def get_embedding_client(manager):
    """
    Katalogdaki kullanılabilir bir embedding modelini yükler ve client nesnesini döndürür.
    """
    catalog = manager.catalog
    
    # 1. Varsayılan modeli kontrol et
    try:
        model = catalog.get_model(DEFAULT_EMBEDDING_MODEL)
    except Exception:
        model = None
        
    # 2. Eğer varsayılan bulunamadıysa, isminde 'embedding' geçen ilk modeli bulmaya çalış
    if not model:
        print(f"'{DEFAULT_EMBEDDING_MODEL}' modeli katalogda bulunamadı, alternatif aranıyor...")
        try:
            available_models = catalog.list_models()
            for m in available_models:
                if "embedding" in m.alias.lower():
                    print(f"Alternatif embedding modeli bulundu: {m.alias}")
                    model = catalog.get_model(m.alias)
                    break
        except Exception as e:
            print(f"Katalog listelenirken hata oluştu: {e}")
            
    if not model:
        raise ValueError("Kullanılabilir herhangi bir embedding modeli bulunamadı. Lütfen 'foundry model list' komutu ile modellerinizi kontrol edin.")
        
    print(f"Embedding modeli yükleniyor: {model.alias}...")
    
    # Modeli indir (önbelleğe al) ve belleğe yükle
    if hasattr(model, 'download'):
        model.download()
    model.load()
    
    # Client nesnesini güvenli şekilde oluştur (hem get hem create metodunu destekleyecek şekilde)
    if hasattr(model, 'get_embedding_client'):
        return model.get_embedding_client()
    elif hasattr(model, 'create_embedding_client'):
        return model.create_embedding_client()
    else:
        raise AttributeError("Model nesnesinde embedding client oluşturacak metod bulunamadı.")

def chunk_text(text, paragraphs_per_chunk=2):
    """
    Metni satır başlarına göre paragraflara böler ve belirtilen sayıda paragraftan oluşan anlamlı parçalar (chunks) üretir.
    """
    # Boş olmayan paragrafları ayıkla
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    chunks = []
    for i in range(0, len(paragraphs), paragraphs_per_chunk):
        chunk_paras = paragraphs[i:i + paragraphs_per_chunk]
        chunks.append("\n\n".join(chunk_paras))
    return chunks

def init_db():
    """
    SQLite veritabanını ve tabloları hazırlar.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def ingest_data():
    """
    data.txt dosyasını oku, parçalar, embedding'leri hesaplar ve SQLite veritabanına yazar.
    """
    if not os.path.exists(DATA_PATH):
        # Test amaçlı varsayılan bir veri dosyası oluştur
        print(f"'{DATA_PATH}' dosyası bulunamadı. Örnek veri içeren bir dosya oluşturuluyor...")
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            f.write(
                "Yapay Zeka ve Yerel RAG Sistemleri\n\n"
                "RAG (Retrieval-Augmented Generation), büyük dil modellerinin (LLM) harici ve güvenilir bilgi kaynaklarından "
                "veri çekerek daha doğru ve güncel yanıtlar üretmesini sağlayan bir mimaridir. Bu yöntem, modellerin "
                "bilgi sınırlarını genişletir ve uydurma (hallucination) riskini azaltır.\n\n"
                "Microsoft Foundry Local Teknolojisi\n\n"
                "Microsoft Foundry Local, bulut bağımlılığı olmadan yerel donanım üzerinde (NPU, GPU, CPU) yapay zeka "
                "modellerini çalıştırmayı sağlayan hafif bir çalışma zamanı ortamıdır. Kullanıcı verilerinin tamamen cihazda "
                "kalmasını garantileyerek yüksek düzeyde gizlilik ve düşük gecikme süresi sağlar.\n\n"
                "Offline RAG Uygulamalarının Avantajları\n\n"
                "Çevrimdışı çalışan RAG sistemleri, herhangi bir API anahtarı veya internet bağlantısı gerektirmez. "
                "Bu durum özellikle hassas finansal veriler, askeri projeler veya internet erişimi kısıtlı olan "
                "saha operasyonları için mükemmel bir çözüm sunar."
            )

    print("Veritabanı kuruluyor...")
    init_db()

    # Verileri oku
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        text_content = f.read()

    chunks = chunk_text(text_content, paragraphs_per_chunk=2)
    print(f"Metin {len(chunks)} parçaya ayrıldı.")

    # Foundry Local SDK'yı başlat
    print("Foundry Local SDK başlatılıyor...")
    manager = get_sdk_manager()

    embedding_client = get_embedding_client(manager)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Önceki verileri temizle
    cursor.execute("DELETE FROM documents")

    print("Embedding'ler hesaplanıyor ve veritabanına yazılıyor...")
    for i, chunk in enumerate(chunks):
        print(f"İşleniyor ({i+1}/{len(chunks)})...")
        # Embedding üret
        response = embedding_client.generate_embedding(chunk)
        # Yanıttan embedding listesini çek
        embedding_vector = response.data[0].embedding
        
        # SQLite'a kaydet (JSON string olarak saklıyoruz)
        cursor.execute(
            "INSERT INTO documents (text, embedding) VALUES (?, ?)",
            (chunk, json.dumps(embedding_vector))
        )
    
    conn.commit()
    conn.close()
    print("Veri yükleme (Ingestion) başarıyla tamamlandı!")

if __name__ == "__main__":
    ingest_data()
