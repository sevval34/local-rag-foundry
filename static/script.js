document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatHistory = document.getElementById("chat-history");
    const btnSend = document.getElementById("btn-send");
    const btnIngest = document.getElementById("btn-ingest");
    const dbStatusBadge = document.getElementById("db-status-badge");
    const dbChunkCount = document.getElementById("db-chunk-count");
    
    // Dosya yükleme elemanları
    const fileInput = document.getElementById("file-input");
    const uploadFilename = document.getElementById("upload-filename");
    const uploadLabel = document.querySelector(".upload-label");

    // 1. Veritabanı Durumunu Güncelle
    async function updateDbStatus() {
        try {
            const response = await fetch("/api/db-status");
            const data = await response.json();
            
            if (data.exists && data.chunk_count > 0) {
                dbStatusBadge.textContent = "Aktif";
                dbStatusBadge.className = "badge-status online";
                dbChunkCount.textContent = data.chunk_count;
            } else {
                dbStatusBadge.textContent = "Boş / Eksik";
                dbStatusBadge.className = "badge-status offline";
                dbChunkCount.textContent = "0";
            }
        } catch (error) {
            console.error("Durum alınamadı:", error);
            dbStatusBadge.textContent = "Hata";
            dbStatusBadge.className = "badge-status offline";
        }
    }

    // 2. Mesaj Ekleme Fonksiyonu
    function appendMessage(sender, text, sources = null) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", `${sender}-message`);

        const contentDiv = document.createElement("div");
        contentDiv.classList.add("message-content");
        contentDiv.innerHTML = `<p>${text.replace(/\n/g, "<br>")}</p>`;
        messageDiv.appendChild(contentDiv);

        // Kaynaklar varsa ekle
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement("div");
            sourcesDiv.classList.add("sources-container");
            
            const title = document.createElement("div");
            title.classList.add("sources-title");
            title.innerHTML = '<i class="fa-solid fa-book-open"></i> Doğrulama Kaynakları';
            sourcesDiv.appendChild(title);

            sources.forEach(src => {
                const item = document.createElement("div");
                item.classList.add("source-item");
                item.innerHTML = `
                    <div class="source-header">
                        <span>[Kaynak ${src.id}]</span>
                        <span>Skor: ${src.score.toFixed(4)}</span>
                    </div>
                    <div>${src.text}</div>
                `;
                sourcesDiv.appendChild(item);
            });
            messageDiv.appendChild(sourcesDiv);
        }

        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return messageDiv;
    }

    // 3. Yükleniyor (Thinking) Efekti Ekle
    function appendLoader() {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", "assistant-message", "loader-msg");

        const contentDiv = document.createElement("div");
        contentDiv.classList.add("message-content");
        contentDiv.innerHTML = `
            <div class="loader-container">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        messageDiv.appendChild(contentDiv);
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return messageDiv;
    }

    // 4. Form Gönderimi (Soru Sorma)
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const question = userInput.value.strip ? userInput.value.strip() : userInput.value.trim();
        if (!question) return;

        // Kullanıcı mesajını ekle ve input'u temizle
        appendMessage("user", question);
        userInput.value = "";
        userInput.style.height = "auto";

        // Yükleniyor animasyonunu ekle
        const loader = appendLoader();

        try {
            const response = await fetch("/api/query", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ question })
            });

            // Yükleniyor alanını kaldır
            loader.remove();

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Sorgu işlenemedi.");
            }

            const data = await response.json();
            appendMessage("assistant", data.answer, data.sources);
        } catch (error) {
            loader.remove();
            appendMessage("assistant", `Hata: ${error.message || "Model yanıt veremedi. Lütfen Foundry Local servisinin çalıştığından emin olun."}`);
        }
    });

    // Enter tuşuna basıldığında formu gönder (Shift+Enter alt satıra geçer)
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    // Textarea otomatik yükseklik ayarı
    userInput.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight) + "px";
    });

    // 5. Verileri Yeniden Yükle (Ingest) Tetikleme
    btnIngest.addEventListener("click", async () => {
        if (!confirm("data.txt dosyasını yeniden okumak ve gömmeleri sıfırdan oluşturmak istiyor musunuz?")) {
            return;
        }

        btnIngest.disabled = true;
        btnIngest.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Yükleniyor...';
        dbStatusBadge.textContent = "İşleniyor...";
        dbStatusBadge.className = "badge-status offline";

        try {
            const response = await fetch("/api/ingest", { method: "POST" });
            if (!response.ok) throw new Error("Yükleme işlemi başarısız oldu.");

            const data = await response.json();
            alert(data.message);
        } catch (error) {
            alert("Veri yüklenirken hata: " + error.message);
        } finally {
            btnIngest.disabled = false;
            btnIngest.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Yeniden İndeksle';
            updateDbStatus();
        }
    });

    // 6. Dosya Seçimi ve Yükleme İşlemi (Upload)
    fileInput.addEventListener("change", async () => {
        const file = fileInput.files[0];
        if (!file) return;

        uploadFilename.textContent = `Yükleniyor: ${file.name}`;
        uploadLabel.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Dosya Gönderiliyor...';
        
        // Arayüz durumunu güncelle
        dbStatusBadge.textContent = "İşleniyor...";
        dbStatusBadge.className = "badge-status offline";

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("/api/upload", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Dosya yüklenemedi.");
            }

            const data = await response.json();
            uploadFilename.textContent = `Aktif: ${file.name}`;
            alert(data.message);
        } catch (error) {
            uploadFilename.textContent = "";
            alert("Hata: " + error.message);
        } finally {
            uploadLabel.innerHTML = '<i class="fa-solid fa-file-arrow-up"></i> Belge Yükle (.txt)';
            fileInput.value = ""; // Input sıfırla
            updateDbStatus();
        }
    });

    // İlk yüklemede durum kontrolü
    updateDbStatus();
});
