# Dokumentasi Pengujian & Indexing LightRAG — UU Nomor 45 Tahun 2009
## Implementasi GraphRAG Berbasis Model Gemma 4:12B & BGE-M3
**Infrastruktur Komputasi:** HPC BRIN MAHAMERU-AI (NVIDIA DGX A100)

---

## 1. Arsitektur Direktori Proyek (Lokal & HPC `pharjawirya`)

```text
/home/pharjawirya/ (~)
├── miniconda3/                                  # Instalasi Conda di Home (env: lightrag_env)
├── bin/ollama                                   # Biner portabel Ollama v0.40.13 di Home
├── .ollama/models/                              # Penyimpanan model gemma4:12b & bge-m3 di Home
└── task/lightrag_testing/                       # Folder utama proyek di HPC
    ├── README.md                                # Dokumentasi teknis dan panduan operasional
    ├── LOG_VERSION.md                           # Catatan riwayat perubahan versi & optimasi sistem
    ├── prompt_lightrag_id_v1.py                 # Modul utama prompt yuridis Bahasa Indonesia LightRAG V1.1
    ├── data/                                    # Repositori dokumen sumber dan data pra-pemrosesan
    │   ├── UU Nomor 45 Tahun 2009 (1).pdf       # Dokumen naskah asli Undang-Undang Nomor 45 Tahun 2009
    │   └── chunks_uu_45_2009.json               # Data potongan teks siap indeks (digantikan 512 token oleh rechunk_512.py)
    ├── proses/                                  # Direktori skrip eksekusi ekstraksi, indexing, dan normalisasi
    │   ├── extract_mineru_hpc.py                # Skrip ekstraksi PDF MinerU v4 & chunker pasal hierarkis
    │   ├── rechunk_512.py                       # Skrip re-chunking semantik 512 token + 100 overlap ber-header kanonik
    │   ├── run_mineru_extract.sbatch            # Skrip batch SLURM untuk ekstraksi MinerU & rechunking di A100
    │   ├── prompt_lightrag_id_v1.py             # Salinan modul injeksi prompt LightRAG Bahasa Indonesia V1.1
    │   ├── prompt_id_revisi.py                  # Arsip templat prompt referensi generasi awal (V0.1.0)
    │   ├── normalisasi_entitas.py               # Modul kanonikalisasi ALIASES & deduplikasi GraphML
    │   ├── run_lightrag.py                      # Service engine utama eksekusi indexing asinkron LightRAG
    │   ├── run_indexing.sbatch                  # Skrip batch SLURM indexing LightRAG (port dinamis, A100)
    │   └── pengujian_lightrag.b64               # Bundel distribusi kode terenkode Base64 untuk transfer HPC
    └── hasil/                                   # Direktori keluaran artefak Knowledge Graph & Vector Store
        └── storage_gemma4_uu45_lightrag/        # Penyimpanan utama artefak LightRAG (Gemma 4:12B)
```

---

## 2. Spesifikasi Parameter Konfigurasi V2.4

| Parameter Evaluasi / Konfigurasi | Spesifikasi & Capaian (LightRAG — Gemma 4:12B) |
| :--- | :--- |
| **Penulis & Pengembang (*Author*)** | **Pabian** |
| **Dokumen Sumber** | `data/UU Nomor 45 Tahun 2009 (1).pdf` (Diekstrak ke `data/UU_Nomor_45_Tahun_2009/output.md`) |
| **Ukuran Chunk & Overlap** | **`512` Token** & **`100` Token Overlap** (`rechunk_512.py` & `run_lightrag.py` — 61 Chunks) |
| **Modul Prompt & Normalisasi** | `proses/prompt_lightrag_id_v1.py` (V1.1) & `proses/normalisasi_entitas.py` (V1.1) |
| **Skrip Eksekusi & Batch SLURM** | `proses/run_lightrag.py` (V2.4), `proses/run_mineru_extract.sbatch`, `proses/run_indexing.sbatch` (V2.4) |
| **Endpoint Ollama HPC** | `http://127.0.0.1:11435` (Jembatan SSH Client ke `mahoni01:11435`) |
| **Direktori Keluaran (*Working Dir*)** | `../hasil/storage_gemma4_uu45_lightrag/` |
| **Model Ekstraksi (LLM)** | `gemma4:12b` (`temperature=0.0`, `num_ctx=4096`, `num_predict=2048`, 5x Auto-Retry) |
| **Model Vektor (*Embedding*)** | `bge-m3:latest` (Dimensi: `1024`, Max Token: `8192`, 5x Auto-Retry) |
| **Konkurensi Asinkron (Anti-OOM)** | `llm_model_max_async=1` (`CONCURRENCY=1`), `embedding_func_max_async=1` |

