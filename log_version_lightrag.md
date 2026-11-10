# LOG VERSION — PENGUJIAN & OPTIMASI LIGHTRAG (UU NOMOR 45 TAHUN 2009)

# ======================================
Perbaikan V2 (Fondasi Prompt ID, Pipeline MinerU, & Masalah Reasoning Awal)

### 1. Injeksi Prompt Hukum Berbahasa Indonesia Awal (`prompt_lightrag_id_v1.py` - V1.1.0)

* **Tanggal:** 09-11-2026

* **Deskripsi:** Mengganti prompt default bahasa Inggris bawaan `lightrag-hku` dengan taksonomi 7 entitas hukum nasional (UU No. 12/2011). Pada versi ini, *few-shot example* masih menggunakan **Pasal 15 (kewenangan penerbitan SIUP oleh Menteri)**.

### 2. Pipeline Ekstraksi MinerU v4 & Boundary-Aware Chunking 512/100 (`rechunk_512.py`)

* **Tanggal:** 09-11-2026

* **Deskripsi:** Ekstraksi naskah UU No. 45/2009 via MinerU v4 di GPU A100 dan pembagian naskah kaku menjadi 83 chunk berbasis panjang token tetap (`chunk_token_size=512`, `chunk_overlap_token_size=100`) dengan injeksi header kanonik.

### 3. Eksperimen Supresi Reasoning via Prompt Directive & Kendala SDK (`run_lightrag.py` - V2.6.0)

* **Tanggal:** 10-11-2026

* **Masalah Teknis:** Model Gemma 4:12B secara default selalu mengaktifkan *thinking mode*, menghabiskan ribuan token hanya untuk penalaran internal. Upaya mematikan reasoning melalui SDK resmi Ollama menghasilkan error:
  `TypeError: AsyncClient.chat() got an unexpected keyword argument 'thinking'`

* **Mitigasi Sementara (V2.6.0):** Dilakukan supresi reasoning secara verbal melalui instruksi keras pada *system prompt directive* ("Langsung jawab format tuple, dilarang reasoning").

* **Kelemahan:** Model tidak konsisten; sesekali tetap mengeluarkan token `<thought>` di latar belakang, memicu pemotongan format tuple output ekstraksi.

# ======================================
Perbaikan V3 (Stabilisasi Komputasi, Resolusi Desinkronisasi Graf, & Kalibrasi Query)

### 1. Transisi ke Direct HTTP Request, Penanganan Timeout & Concurrency (`run_lightrag.py` - V3.1.0)

* **Tanggal:** 10-11-2026

* **Tindakan:** Mengabaikan SDK wrapper bawaan dan beralih ke pemanggilan REST API langsung (`httpx.post`) ke endpoint `/api/chat` dengan payload native `"think": False`.

* **Kendala yang Ditemui & Solusi Faktual:**

  * **Error `httpx.ReadTimeout`:** Timeout default `httpx` (5 detik) terlampaui saat LLM memproses teks hukum panjang. **Solusi:** Menyetel batas eksplisit `httpx.AsyncClient(timeout=240.0)`.

  * **Error `HTTP 500 Internal Server Error`:** Terjadi karena LightRAG default membuka 4 antrean paralel (`max_async=4`) yang membebani instance Ollama bersama di `mahoni01:11435`. **Solusi:** Menyetel `CONCURRENCY=1` (`llm_model_max_async=1`) dan menyematkan loop *exponential backoff retry* (1–5 kali percobaan dengan jeda tunggu `wait_s = attempt * 5`).

### 2. Eliminasi Total Deduplikasi Destruktif & Pemulihan Integritas Graf (`run_lightrag.py` - V3.2.0)

* **Tanggal:** 10-11-2026

* **Akar Masalah:** Pemanggilan `dedup_graph(G)` dari `normalisasi_entitas.py` pasca-indexing mengubah format casing node di file `graph_chunk_entity_relation.graphml` tanpa memperbarui `vdb_entities.json`. Hal ini menyebabkan desinkronisasi fatal: hanya **3 dari 588 node yang cocok (0.5%)**, memicu peringatan `WARNING: Some nodes are missing, maybe the storage is damaged` dan membuang 99.5% simpul saat query.

* **Solusi Faktual:** Menghapus skrip `dedup_graph()` eksternal dan menyerahkan pembentukan graf murni ke engine internal LightRAG.

* **Hasil Verifikasi:** Tingkat sinkronisasi GraphML vs VectorDB melonjak menjadi **629 / 629 node cocok sempurna (100.0%)**.

### 3. Pembaruan Prompt Berbasis Relasi Sanksi (`prompt_lightrag_id_v1.py` - V1.3.0)

* **Tanggal:** 10-11-2026

* **Perubahan Inti:**

  * Memperbarui *few-shot example* dari Pasal 15 menjadi **Pasal 93 ayat (2) jo. Pasal 27 ayat (2)**.

  * Menambahkan Aturan 4 (Kewajiban Relasi Sanksi): Setiap pasal sanksi wajib disambungkan secara kausal ke pasal pelanggaran primernya (`sanksi_pelanggaran`) dan subjek pelakunya (`ancaman_pidana`).

  * Menambahkan Aturan 5 (Anti-Hub Bloat): Melarang pembentukan entitas kata tunggal umum tanpa konteks yuridis ("Kapal", "Orang", "Ikan") guna mencegah terbentuknya simpul raksasa (*hub node*) yang membanjiri konteks pencarian.

### 4. Pembangunan Engine Query & Kalibrasi Parameter Resmi (`query.py` - V1.0.0)

* **Tanggal:** 10-11-2026

* **Akar Masalah Query Awal:**

  * Penggunaan parameter non-resmi (`max_token_for_local_context`) memicu `TypeError: QueryParam.__init__() got an unexpected keyword argument`.

  * Pembatasan konteks di `NUM_CTX=4096` memotong teks naskah UU (*prompt hard-cut*).

  * Parameter default `top_k=40` menyebabkan *hub-node crowding*, di mana puluhan chunk entitas graf (`E`) merebut kuota, sehingga chunk teks naskah Pasal 93 ayat (2) (`C2`) terlempar dari antrean round-robin.

* **Kalibrasi Resmi QueryParam:**

  * Membuka jendela konteks inferensi ke `NUM_CTX=8192` dan `NUM_PREDICT=1500`.

  * Menyetel `top_k=6` agar kamus entitas graf tetap ringkas dan tidak merebut slot teks pasal.

  * Memperluas `chunk_top_k=25` untuk mengantisipasi pasal sanksi yang terbelah akibat pemotongan 512 token (Pasal 93 ayat 1 dan ayat 2).

  * Mengunci alokasi token resmi: `max_entity_tokens=1500`, `max_relation_tokens=1500`, `max_total_tokens=7000`.

### Matriks Pengujian & Validasi Inferensi Akhir

| No | Kasus Uji / Pertanyaan | Target Yuridis | Respon Model | Status | 
| ----- | ----- | ----- | ----- | ----- | 
| 1 | Sanksi pidana kapal asing tanpa SIPI di ZEEI | Pasal 93 ayat (2) jo. Pasal 27 ayat (2) | Menyebutkan penjara maksimal 6 tahun dan denda maksimal Rp20.000.000.000,00 secara presisi dengan sitasi Chunk 38. | **SUKSES** | 
| 2 | Tugas dan wewenang syahbandar di pelabuhan | Pasal 42 ayat (2) UU No. 45/2009 | Menyajikan 3 klaster kewenangan (administrasi pelayaran, teknis kelaikan, keselamatan/SAR/pencemaran) dengan sitasi Chunk 21. | **SUKSES** | 
| 3 | Mekanisme pemulangan ABK berkewarganegaraan asing | Pasal 83A UU No. 45/2009 | Menjelaskan pemulangan ABK non-tersangka oleh instansi imigrasi melalui perwakilan negara asal dengan sitasi Chunk 37. | **SUKSES** | 

### Rekomendasi Operasional Workspace Antigravity

1. **Eksekusi Query CLI:** Gunakan perintah `python query.py "Pertanyaan hukum anda"` untuk pengujian interaktif maupun evaluasi batch.

2. **Persistensi Parameter:** Pertahankan nilai `DEFAULT_LEGAL_QUERY_PARAM` saat mengintegrasikan pipeline ke framework evaluasi benchmark (RAGAS / TruLens) untuk menjamin konsistensi metrik *faithfulness* dan *answer correctness*.