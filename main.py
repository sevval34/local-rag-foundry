import os
import sqlite3
from ingest import ingest_data, DB_PATH
from llm import answer_query

def main():
    print("=" * 60)
    print("      Microsoft Foundry Local - Yerel RAG Soru-Cevap      ")
    print("=" * 60)

    # 1. Veritabanı ve veri kontrolü
    db_exists = os.path.exists(DB_PATH)
    is_db_empty = True

    if db_exists:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            count = cursor.fetchone()[0]
            if count > 0:
                is_db_empty = False
            conn.close()
        except Exception:
            pass

    if not db_exists or is_db_empty:
        print("\nVeritabanı bulunamadı veya boş. Ingestion (veri yükleme) başlatılıyor...")
        try:
            ingest_data()
        except Exception as e:
            print(f"\n[HATA] Veri yüklenirken bir sorun oluştu: {e}")
            print("Lütfen Foundry Local SDK ve modellerinizin hazır olduğundan emin olun.")
            return
    else:
        print("\nHazır veritabanı tespit edildi. RAG uygulaması başlatılıyor...")

    print("\nSistem hazır! Sormak istediğiniz soruları yazın.")
    print("Çıkmak için 'q' veya 'exit' yazabilirsiniz.\n")

    # 2. Kullanıcı Arayüzü Döngüsü
    while True:
        try:
            user_question = input("\nSoru: ").strip()
            if not user_question:
                continue
            
            if user_question.lower() in ['q', 'exit', 'çıkış', 'quit']:
                print("\nYerel RAG asistanı kapatılıyor. İyi günler!")
                break

            print("\nCevap aranıyor, lütfen bekleyin...")
            answer, sources = answer_query(user_question)

            print("\n" + "-" * 50)
            print("YANIT:")
            print(answer)
            print("-" * 50)
            
            if sources:
                print("\nKullanılan Bağlamlar ve Benzerlik Skorları:")
                for src in sources:
                    print(f"- [Kaynak {src['id']}] {src['text']} (Benzerlik: {src['score']:.4f})")
            print("=" * 60)

        except KeyboardInterrupt:
            print("\nProgram sonlandırıldı.")
            break
        except Exception as e:
            print(f"\nBir hata oluştu: {e}")
            print("Lütfen model yüklemelerini ve SDK ayarlarını kontrol edin.")

if __name__ == "__main__":
    main()
