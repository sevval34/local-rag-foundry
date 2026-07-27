# 🤖 Microsoft Foundry Local - Yerel RAG Soru-Cevap Asistanı

> **👑 Bu proje Şevval Başkan tarafından yapılmıştır.** 😎

Bu proje, **Microsoft Foundry Local** altyapısını kullanarak sıfır internet bağımlılığıyla çalışan, yerel bir **RAG (Retrieval-Augmented Generation)** Soru-Cevap asistanıdır. Verileriniz tamamen kendi bilgisayarınızda kalır, hiçbir harici API (OpenAI, Anthropic vb.) çağrısı yapılmaz.

---

## 🌟 Özellikler

*   **Tamamen Çevrimdışı (Offline):** İnternet bağlantısı olmadan yerel donanım ivmelendirmesi ile çalışır.
*   **Modern Web Arayüzü:** Koyu tema (Glassmorphism) ve neon geçişlere sahip şık bir sohbet ekranı sunar.
*   **Dinamik Belge Yükleme:** Web arayüzünden doğrudan `.txt` dosyası yükleyip anında yeni döküman üzerinden RAG sorgulaması yapabilirsiniz.
*   **Doğrulanmış Kaynaklar:** Asistan cevap üretirken veritabanında en yakın bulduğu 3 metin parçasını benzerlik skorları (Cosine Similarity) ile birlikte referans gösterir.
*   **Güvenli Başlatıcı (Singleton Safe):** Tekil örnek yönetim altyapısı sayesinde sistem kaynakları kilitlenmez.

---

## 🛠 Kullanılan Teknolojiler

*   **Dil ve Embedding Modelleri:** `phi-3.5-mini` (Chat) & `qwen3-embedding-0.6b` (Vektörleştirme)
*   **Backend:** Python 3.12+, FastAPI, Uvicorn, SQLite3, NumPy
*   **Frontend:** Vanilla HTML5, CSS3 (Glassmorphism & Custom Keyframe Animations), JavaScript (ES6 Fetch API)

---

## 🚀 Kurulum ve Çalıştırma

### 1. Proje Klasörüne Geçin
```powershell
cd C:\Users\sevva\.gemini\antigravity\scratch\local_rag_foundry
```

### 2. Gereksinimleri Yükleyin
```powershell
pip install -r requirements.txt
```

### 3. Web Arayüzünü Başlatın
```powershell
python -m uvicorn app:app --reload --port 8000
```
Başlattıktan sonra tarayıcınızdan **`http://localhost:8000`** adresine giderek asistanla sohbet etmeye başlayabilirsiniz.

---

## 📂 Proje Yapısı

```bash
local_rag_foundry/
├── app.py              # FastAPI Backend Sunucusu
├── ingest.py           # Metin bölme ve Vektörleştirme (SQLite kayıt)
├── retrieval.py        # Kosinüs benzerliği ile döküman arama
├── llm.py              # Yerel LLM phi-3.5-mini bağlantısı
├── main.py             # CLI (Terminal) Arayüzü (Alternatif)
├── requirements.txt    # Python Bağımlılıkları
├── .gitignore          # Git dışı bırakılacaklar (data.txt, db vb.)
└── static/             # Web Arayüzü Dosyaları (HTML, CSS, JS)
```
