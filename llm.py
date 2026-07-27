from retrieval import get_top_chunks
from ingest import get_sdk_manager

# Varsayılan model ismi
DEFAULT_CHAT_MODEL = "phi-3.5-mini"

def get_chat_client(manager):
    """
    Katalogdaki kullanılabilir bir chat modelini yükler ve client nesnesini döndürür.
    """
    catalog = manager.catalog
    
    # 1. Varsayılan modeli kontrol et
    try:
        model = catalog.get_model(DEFAULT_CHAT_MODEL)
    except Exception:
        model = None
        
    # 2. Eğer varsayılan bulunamadıysa, isminde 'embedding' geçmeyen ilk modeli bulmaya çalış
    if not model:
        print(f"'{DEFAULT_CHAT_MODEL}' modeli katalogda bulunamadı, alternatif aranıyor...")
        try:
            available_models = catalog.list_models()
            for m in available_models:
                if "embedding" not in m.alias.lower():
                    print(f"Alternatif chat modeli bulundu: {m.alias}")
                    model = catalog.get_model(m.alias)
                    break
        except Exception as e:
            print(f"Katalog listelenirken hata oluştu: {e}")
            
    if not model:
        raise ValueError("Kullanılabilir herhangi bir chat modeli bulunamadı. Lütfen 'foundry model list' komutu ile modellerinizi kontrol edin.")
        
    print(f"Chat modeli yükleniyor: {model.alias}...")
    
    # Modeli indir (önbelleğe al) ve belleğe yükle
    if hasattr(model, 'download'):
        model.download()
    model.load()
    
    # Client nesnesini güvenli şekilde oluştur
    if hasattr(model, 'get_chat_client'):
        return model.get_chat_client()
    elif hasattr(model, 'create_chat_client'):
        return model.create_chat_client()
    else:
        raise AttributeError("Model nesnesinde chat client oluşturacak metod bulunamadı.")

def answer_query(user_question):
    """
    Sorguyu alır, veritabanından en alakalı bağlamı bulur, prompt'u hazırlar
    ve LLM'e göndererek yerel olarak yanıtı üretir.
    """
    # 1. En alakalı 3 metin parçasını al
    top_chunks = get_top_chunks(user_question, top_k=3)
    
    if not top_chunks:
        return "Sorguya ilişkin herhangi bir kaynak bulunamadı.", []
        
    # Bağlam (context) metnini oluştur ve kaynakları listele
    context_parts = []
    sources = []
    
    for idx, (text, score) in enumerate(top_chunks):
        context_parts.append(text)
        sources.append({"id": idx + 1, "text": text[:60] + "...", "score": score})
        
    context = "\n---\n".join(context_parts)
    
    # 2. SDK ve Chat Client başlat
    manager = get_sdk_manager()
    chat_client = get_chat_client(manager)
    
    # 3. Sistem Mesajı ve Kullanıcı Prompt'unu oluştur
    system_prompt = (
        "Sen bir asistan olarak, sadece sana sağlanan bağlamdaki bilgileri kullanarak soruları yanıtlayacaksın. "
        "Eğer aradığın bilgi bağlamda yoksa, kesinlikle kendi bilgini kullanma ve sadece 'Bu bilgiye sahip değilim' de. "
        "Mümkünse cevaplarında kaynak belirt."
    )
    
    user_prompt = (
        f"Aşağıdaki BAĞLAM'a göre soruyu yanıtla:\n\n"
        f"[BAĞLAM]\n{context}\n\n"
        f"[SORU]\n{user_question}"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # 4. İnferans çalıştır
    print("Yanıt üretiliyor...")
    response = chat_client.complete_chat(messages)
    
    # Yanıtı döndür
    if hasattr(response, 'choices') and len(response.choices) > 0:
        answer = response.choices[0].message.content
    else:
        answer = str(response)
        
    return answer, sources
