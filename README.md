# Dokumentasi Pengujian & Indexing LightRAG — UU Nomor 45 Tahun 2009
## Implementasi GraphRAG Berbasis Model Gemma 4:12B & BGE-M3
**Infrastruktur Komputasi:** HPC BRIN MAHAMERU-AI (NVIDIA DGX A100)

---

## 1. Arsitektur Direktori Proyek

Struktur organisasi berkas dan direktori pada ruang kerja (*workspace*) pengujian LightRAG disusun sebagai berikut:

```text
pengujian_lightrag/
├── README.md                                  # Dokumentasi teknis dan panduan operasional
├── run_lightrag.py                            # Skrip utama eksekusi indexing asinkron LightRAG
├── run_indexing.sbatch                        # Skrip penjadwalan kompilasi job SLURM (DGX A100)
├── prompt_id_revisi.py                        # Kustomisasi templat prompt ekstraksi entitas hukum Bahasa Indonesia
├── pengujian_lightrag.b64                     # Bundel distribusi kode terenkode Base64 untuk transfer HPC
├── data/                                      # Repositori dokumen sumber dan data pra-pemrosesan
│   ├── UU Nomor 45 Tahun 2009 (1).pdf         # Dokumen naskah asli Undang-Undang Nomor 45 Tahun 2009
│   └── chunks_uu_45_2009.json                 # Data potongan teks (144 chunks berbasis pasal) siap indeks
└── hasil_indexing/                            # Direktori keluaran artefak Knowledge Graph & Vector Store
    ├── storage_gemma4_uu45.tar.gz             # Arsip terkompresi hasil proses indexing
    └── storage_gemma4_uu45_lightrag/          # Penyimpanan utama artefak LightRAG (Gemma 4:12B)
        ├── graph_chunk_entity_relation.graphml# Struktur graf pengetahuan (749 simpul, 1.213 relasi)
        ├── kv_store_doc_status.json           # Pencatatan status pemrosesan dokumen
        ├── kv_store_entity_chunks.json        # Pemetaan indeks antara entitas dan potongan teks asal
        ├── kv_store_full_docs.json            # Penyimpanan teks dokumen lengkap secara utuh
        ├── kv_store_full_entities.json        # Daftar himpunan entitas beserta atributnya
        ├── kv_store_full_relations.json       # Daftar himpunan relasi antar-entitas
        ├── kv_store_llm_response_cache.json   # Penyimpanan tembolok (cache) respons inferensi LLM
        ├── kv_store_relation_chunks.json      # Pemetaan indeks antara relasi dan potongan teks asal
        ├── kv_store_text_chunks.json          # Penyimpanan key-value untuk 144 potongan teks (chunks)
        ├── vdb_chunks.json                    # Basis data vektor untuk representasi potongan teks
        ├── vdb_entities.json                  # Basis data vektor entitas (BGE-M3, dimensi 1024)
        └── vdb_relationships.json             # Basis data vektor relasi antar-entitas
```

---

## 2. Persiapan Lingkungan Komputasi & Dependensi

Sebelum memulai tahapan pembentukan graf pengetahuan (*indexing*), pastikan seluruh perangkat lunak prasyarat dan model kecerdasan buatan telah terkonfigurasi dengan baik pada *login node* (`mahoni01`).

### A. Konfigurasi Miniconda dan Lingkungan Virtual `lightrag_env`
Apabila lingkungan Python khusus untuk LightRAG belum tersedia pada akun HPC Anda, jalankan rangkaian instruksi berikut:

```bash
# 1. Unduh dan pasang Miniconda3 (jika belum terpasang di direktori pengguna)
curl -sLO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
rm -f Miniconda3-latest-Linux-x86_64.sh

# 2. Bangun environment conda bernama 'lightrag_env' menggunakan Python 3.10
$HOME/miniconda3/bin/conda create -n lightrag_env -c conda-forge python=3.10 pip numpy networkx httpx tqdm -y

# 3. Aktifkan environment dan pasang pustaka LightRAG beserta dependensi pendukung
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lightrag_env
pip install lightrag-hku ollama nano-vectordb tiktoken tenacity python-dotenv json-repair pipmaster
```

### B. Penyediaan Layanan Ollama & Pengunduhan Model
Proses ekstraksi entitas dan pembangkitan vektor menggunakan layanan Ollama yang dijalankan pada port terisolasi (`11500`) guna menghindari benturan dengan layanan bawaan sistem.

```bash
# 1. Jalankan server Ollama sementara pada port 11500 di latar belakang
export OLLAMA_HOST=127.0.0.1:11500
ollama serve > /dev/null 2>&1 &
OLLAMA_PID=$!
sleep 5

# 2. Unduh model LLM utama dan model Embedding
ollama pull gemma4:12b
ollama pull bge-m3:latest

# 3. Hentikan server sementara setelah pengunduhan selesai
kill $OLLAMA_PID
```
*Spesifikasi Model:*
- **Generator LLM (`gemma4:12b`):** Digunakan untuk mengekstrak entitas hukum, relasi semantik, dan kata kunci tingkat tinggi dengan pengaturan `temperature=0.0`, `num_ctx=4096`, `top_p=0.9`, serta konkurensi maksimal `llm_model_max_async=10`.
- **Embedding Model (`bge-m3:latest`):** Digunakan untuk mentransformasi teks, entitas, dan relasi ke dalam ruang vektor berdimensi `1024` (batas token maksimal `8192` dan ukuran *batch* `32`).

### C. Kustomisasi Prompt Bahasa Indonesia (`prompt_id_revisi.py`)
Berkas `prompt_id_revisi.py` memuat definisi prompt yang telah disesuaikan untuk ranah regulasi Indonesia dengan taksonomi entitas hukum meliputi:
`["dasar_hukum", "struktur", "konsep", "sanksi", "pihak", "kewajiban", "hak"]`.
Selain itu, pada `run_lightrag.py` diterapkan injeksi instruksi *thinking-bypass* agar model langsung memproduksi entitas dan relasi terstruktur tanpa menyertakan narasi penalaran internal (*chain-of-thought*), sehingga memangkas latensi secara signifikan.

---

## 3. Pengelolaan Antrean Tugas (SLURM Job Management)

Berikut adalah perintah standar untuk memantau maupun mengendalikan tugas komputasi pada klaster HPC:

### Memeriksa dan Menghentikan Job Aktif
```bash
# Memantau daftar job yang sedang berjalan atau mengantre milik pengguna
squeue -u $USER

# Menghentikan job tertentu berdasarkan nomor identitas (Job ID)
scancel <JOB_ID>

# Menghentikan seluruh job aktif milik pengguna sekaligus
scancel -u $USER
```

### Pembersihan Proses Ollama secara Manual
Apabila terdapat instansi layanan Ollama yang masih tertinggal di latar belakang:
```bash
pkill -f ollama
```

---

## 4. Prosedur Operasional Eksekusi Pengujian

### Tahap 1: Penyiapan Data Masukan (Chunks Regulasi)
Pastikan berkas potongan teks per-pasal `chunks_uu_45_2009.json` (terdiri atas **144 chunks** utuh dari UU Nomor 45 Tahun 2009) telah berada di dalam subdirektori `data/`.

---

### Tahap 2: Eksekusi Indexing LightRAG pada Klaster DGX A100
Proses pembentukan basis data graf dan vektor dieksekusi melalui penjadwal SLURM dengan alokasi sumber daya 1 unit GPU NVIDIA A100 (`--qos=a100_1gpu`, partisi `a100-short`) dan memori RAM sebesar `117 GB`.

**Melalui Terminal HPC (`mahoni01`):**
1. Arahkan direktori aktif ke folder ruang kerja proyek:
   ```bash
   cd ~/pengujian_lightrag
   ```

2. Kirimkan skrip batch ke antrean komputasi SLURM:
   ```bash
   sbatch run_indexing.sbatch
   ```

3. Amati perkembangan proses ekstraksi secara waktu nyata (*real-time*):
   ```bash
   tail -f indexing_lightrag_*.log
   ```
   Proses dinyatakan tuntas apabila pada akhir catatan log muncul penanda:
   `INDEXING LIGHTRAG SELESAI SUKSES!`

---

### Tahap 3: Akuisisi dan Sinkronisasi Hasil Indexing ke Perangkat Lokal
Setelah pekerjaan komputasi di klaster selesai, salin seluruh artefak keluaran dari server HPC ke komputer lokal menggunakan utilitas `rsync` atau `scp`:

```bash
# Dijalankan dari terminal perangkat lokal (WSL / Git Bash / PowerShell):
rsync -avzP <username>@mahoni01:~/pengujian_lightrag/hasil_indexing/ ./hasil_indexing/
```

Seluruh artefak hasil konstruksi indeks akan tersimpan di dalam direktori `hasil_indexing/storage_gemma4_uu45_lightrag/`, yang mencakup:
- `graph_chunk_entity_relation.graphml`: Struktur graf pengetahuan komprehensif dalam format GraphML.
- `vdb_entities.json`, `vdb_relationships.json`, `vdb_chunks.json`: Indeks vektor berdimensi 1024 (BGE-M3) untuk pencarian kemiripan semantik tingkat entitas, relasi, dan teks.
- `kv_store_full_docs.json`, `kv_store_text_chunks.json`: Basis data *key-value* dokumen penuh dan potongan teks pasal.
- `kv_store_full_entities.json`, `kv_store_full_relations.json`, `kv_store_entity_chunks.json`, `kv_store_relation_chunks.json`: Pemetaan terstruktur antara entitas/relasi dengan potongan pasal sumber.
- `kv_store_llm_response_cache.json`: Rekaman tembolok hasil ekstraksi LLM.

---

### Tahap 4: Verifikasi Statistik Graf Pengetahuan
Untuk memvalidasi kepadatan dan kelengkapan hasil konstruksi graf pada lingkungan lokal maupun server, jalankan perintah inspeksi Python satu baris berikut:

```bash
python -c "import json, xml.etree.ElementTree as ET; chunks = json.load(open('data/chunks_uu_45_2009.json', encoding='utf-8')); tree = ET.parse('hasil_indexing/storage_gemma4_uu45_lightrag/graph_chunk_entity_relation.graphml'); root = tree.getroot(); ns = {'g': 'http://graphml.graphdrawing.org/xmlns'}; print(f'Total Chunks: {len(chunks)} | Total Nodes (Entitas): {len(root.findall(\".//g:node\", ns))} | Total Edges (Relasi): {len(root.findall(\".//g:edge\", ns))}')"
```

---

## 5. Ringkasan Parameter & Statistik Hasil Indexing

| Parameter Evaluasi / Konfigurasi | Spesifikasi & Capaian (LightRAG — Gemma 4:12B) |
| :--- | :--- |
| **Dokumen Sumber** | Undang-Undang Nomor 45 Tahun 2009 (Perikanan) |
| **Jumlah Potongan Teks (*Input Chunks*)** | 144 Chunks (Utuh) |
| **Model Ekstraksi (LLM)** | `gemma4:12b` (`temperature=0.0`, `num_ctx=4096`) |
| **Model Vektor (*Embedding*)** | `bge-m3:latest` (Dimensi: `1024`, Max Token: `8192`) |
| **Konkurensi Asinkron** | `llm_model_max_async=10`, `embedding_func_max_async=4` |
| **Total Simpul Entitas (*Graph Nodes*)** | **749** Simpul |
| **Total Hubungan Semantik (*Graph Edges*)** | **1.213** Relasi |

---

## 6. Penanganan Kendala Teknis (*Troubleshooting*)

1. **Konflik Port atau Kegagalan Koneksi ke Layanan Ollama:**
   - *Penyebab:* Port bawaan (`11434`) pada node HPC sering kali telah ditempati oleh layanan sistem dengan versi lawas yang tidak mendukung arsitektur model terbaru.
   - *Penanganan:* Selalu definisikan variabel lingkungan `export OLLAMA_HOST=127.0.0.1:11500` sebelum menyalakan `ollama serve`, sebagaimana telah diotomatisasi pada berkas `run_indexing.sbatch` dan `run_lightrag.py`.

2. **Kegagalan Alokasi Memori pada SLURM (`QOSMaxMemoryPerJob`):**
   - *Penyebab:* Permintaan memori melebihi batas kuota kebijakan *Quality of Service* (QoS) untuk profil akun `student` pada antrean `a100_1gpu`.
   - *Penanganan:* Gunakan konfigurasi memori yang telah teruji sesuai batas alokasi node tunggal, yakni `#SBATCH --mem=117G` dengan `#SBATCH --gres=gpu:1`.

3. **Latensi Ekstraksi Tinggi Akibat Proses *Chain-of-Thought* (Thinking Mode):**
   - *Penyebab:* Model generasi terbaru cenderung menyertakan langkah penalaran panjang sebelum menghasilkan daftar entitas dan relasi.
   - *Penanganan:* Fungsi `llm_model_func` di dalam `run_lightrag.py` telah menyematkan prefiks instruksi tegas (`RESPOND DIRECTLY WITH THE REQUIRED EXTRACTED ENTITIES AND RELATIONS. DO NOT THINK STEP-BY-STEP...`) untuk melewati fase penalaran berlebih.

---

## 7. Mekanisme Pengemasan & Distribusi Skrip via Base64 dan GitHub Gist

Metode ini dirancang untuk memindahkan kode sumber serta data masukan dari komputer lokal ke klaster HPC secara cepat dalam satu aliran perintah (*streamlined pipeline*), tanpa perlu mengunggah berkas satu per satu maupun menyisakan berkas arsip sementara di peladen.

### A. Pembuatan Paket Base64 pada Perangkat Lokal
Kemas seluruh skrip eksekusi beserta folder `data/` ke dalam arsip terkompresi `tar.gz`, kemudian konversikan aliran binernya menjadi teks berformat Base64 (`pengujian_lightrag.b64`):

```bash
# Dijalankan pada terminal perangkat lokal di direktori ruang kerja:
tar --exclude='*.log' --exclude='hasil_indexing*' --exclude='testing-lightrag*' --exclude='*.b64' -czf - . | base64 > pengujian_lightrag.b64
```

### B. Publikasi Melalui Layanan GitHub Gist
1. Kunjungi laman [gist.github.com](https://gist.github.com).
2. Buat entri Gist baru dengan nama berkas `pengujian_lightrag.b64`, lalu tempelkan seluruh isi teks Base64 tersebut.
3. Pilih opsi **Create public gist** (atau *secret gist*).
4. Salin tautan dari tombol **"Raw"** yang memiliki pola URL:
   `https://gist.githubusercontent.com/<username>/<id_gist>/raw/pengujian_lightrag.b64`

### C. Dekode dan Ekstraksi Langsung pada Server HPC (Satu Baris Perintah)
Pada terminal *login node* HPC (`mahoni01`), jalankan instruksi *piping* berikut untuk mengunduh, mendekode, dan mengekstrak seluruh struktur ruang kerja secara langsung di memori:

```bash
mkdir -p ~/pengujian_lightrag && cd ~/pengujian_lightrag
curl -sL "https://gist.githubusercontent.com/<username>/<id_gist>/raw/pengujian_lightrag.b64?t=$(date +%s)" | base64 -d | tar -xzf -
```

**Rincian Cara Kerja Rangkaian Perintah (*Command Pipeline*):**
- `curl -sL "<URL>"`: Mengambil konten teks mentah dari peladen Gist secara senyap dan meneruskannya langsung ke aliran keluaran standar (*stdout*) tanpa menyimpan berkas fisik sementara.
- `?t=$(date +%s)`: Parameter penangkal tembolok (*cache buster*) berbasis waktu Unix terkini agar jaringan pengiriman konten (CDN) selalu menyajikan revisi berkas paling mutakhir.
- `| base64 -d`: Menerima aliran teks dari *stdin* dan menerjemahkannya kembali menjadi aliran biner arsip kompresi.
- `| tar -xzf -`: Membaca aliran biner secara langsung dari *stdin* (`-`) dan mengekstrak seluruh berkas proyek ke direktori kerja aktif saat itu.

