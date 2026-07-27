import os
import sqlite3
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ingest import ingest_data, DB_PATH, DATA_PATH
from llm import answer_query

# 1. FastAPI uygulamasını başlat
app = FastAPI(title="Local RAG Assistant API")

# 2. Statik dosya klasörünü oluştur
os.makedirs("static", exist_ok=True)

# 3. İstek modeli tanımlamaları
class QueryRequest(BaseModel):
    question: str

# 4. API Endpoint'leri
@app.post("/api/query")
async def query_rag(request: QueryRequest):
    """
    Kullanıcı sorusunu alır, yerel RAG araması yapar ve yanıt döndürür.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Soru alanı boş olamaz.")
    
    # Veritabanı var mı kontrol et
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Veritabanı yüklü değil. Önce verileri yükleyin.")
        
    try:
        answer, sources = answer_query(request.question)
        return {
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sorgu işlenirken yerel hata oluştu: {str(e)}")

@app.post("/api/ingest")
async def trigger_ingest():
    """
    data.txt dosyasını yeniden okur, embedding'leri günceller.
    """
    try:
        ingest_data()
        return {"status": "success", "message": "Veritabanı başarıyla güncellendi!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion hatası: {str(e)}")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Web arayüzünden yüklenen .txt dosyasını kaydeder ve RAG ingestion işlemini başlatır.
    """
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Yalnızca .txt uzantılı metin dosyaları desteklenmektedir.")
    
    try:
        # Dosya içeriğini oku
        contents = await file.read()
        text_content = contents.decode("utf-8")
        
        # data.txt dosyasına yaz
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            f.write(text_content)
            
        # Otomatik olarak ingestion işlemini tetikle
        ingest_data()
        
        return {
            "status": "success", 
            "message": f"'{file.filename}' dosyası başarıyla yüklendi ve indekslendi!"
        }
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Dosya UTF-8 formatında kodlanmış olmalıdır.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya işlenirken hata oluştu: {str(e)}")

@app.get("/api/db-status")
async def db_status():
    """
    Veritabanının durumunu döndürür.
    """
    db_exists = os.path.exists(DB_PATH)
    count = 0
    if db_exists:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            count = cursor.fetchone()[0]
            conn.close()
        except Exception:
            pass
    return {
        "exists": db_exists,
        "chunk_count": count
    }

# 5. Ana Sayfa ve Statik Dosya Yönlendirmeleri
@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

# Statik dosyaları en son mount edin ki API rotalarını gölgelemesinler
app.mount("/static", StaticFiles(directory="static"), name="static")
