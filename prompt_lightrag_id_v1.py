"""
Prompt Indexing LightRAG Berbahasa Indonesia - V1.1 (Setara Prompt MiniRAG v2.2.0 BRIN)

Author      : Pabian
Version     : 1.1.0
Created     : 02-11-2026
Revised     : 09-11-2026
Description : Modul injeksi prompt ekstraksi entitas dan relasi hukum berbahasa Indonesia
              untuk engine LightRAG (lightrag-hku). Mengadopsi Standar Taksonomi Yuridis
              Nasional (UU No. 12/2011), aturan penamaan entitas kanonik, penanganan
              otomatis klausul non-normatif ('Cukup jelas.'), serta pencegahan ekstraksi
              rincian spesies biologis (anti-species bloat).

Pemakaian:
    from prompt_lightrag_id_v1 import apply_prompts, ENTITY_TYPES
    addon_params = apply_prompts({"entity_types": ENTITY_TYPES})  # panggil SEBELUM membuat objek LightRAG
    rag = LightRAG(..., addon_params=addon_params)
"""

PROMPT_VERSION = "v1.1"
LANGUAGE = "Indonesian"
ENTITY_TYPES = ['dasar_hukum', 'struktur', 'pihak', 'kewajiban', 'hak', 'sanksi', 'konsep']

ENTITY_TYPES_GUIDANCE = """Gunakan HANYA jenis berikut:
- dasar_hukum: nama peraturan (UU, PP, Peraturan Menteri, KUHP).
- struktur: pasal, ayat, huruf, angka, atau bagian penjelasan.
- pihak: orang, badan, jabatan, atau lembaga (Setiap Orang, Nelayan Kecil, Menteri, Pengawas Perikanan, Pengadilan Perikanan).
- kewajiban: perbuatan yang diwajibkan atau dilarang.
- hak: hak atau kewenangan suatu pihak.
- sanksi: pidana penjara, pidana denda, atau sanksi administratif beserta besarannya.
- konsep: istilah hukum, izin, dokumen, kapal, alat, atau wilayah (Surat Izin Penangkapan Ikan, Zona Ekonomi Eksklusif Indonesia)."""

ENTITY_EXTRACTION_SYSTEM_PROMPT = """---Peran---
Anda adalah spesialis knowledge graph hukum yang mengekstrak entitas dan hubungan dari bagian `---Input Text---` pada prompt pengguna. Teks berasal dari peraturan perundang-undangan Indonesia.

---Instruksi---
1. **Ekstraksi Entitas:**
  - Ekstrak hanya entitas hukum yang TERTULIS di bagian `---Input Text---` prompt pengguna saat ini.
  - Untuk setiap entitas tulis:
    - `nama_entitas`: nama entitas menurut aturan penamaan di butir 6.
    - `jenis_entitas`: salah satu jenis di bagian `---Jenis Entitas---`. Jangan membuat jenis baru.
    - `deskripsi_entitas`: 1-2 kalimat berdasarkan teks saja; sertakan singkatan resmi, besaran sanksi, dan jangka waktu (hari) bila ada.

2. **Ekstraksi Hubungan:**
  - Identifikasi hubungan yang langsung, jelas, dan bermakna antar-entitas yang sudah diekstrak.
  - Pernyataan yang melibatkan lebih dari dua entitas dipecah menjadi beberapa hubungan berpasangan.
  - Untuk setiap hubungan tulis: `entitas_sumber` dan `entitas_target` (sama persis dengan nama entitas), `kata_kunci_hubungan` (satu atau lebih kata kunci tingkat tinggi), dan `deskripsi_hubungan` (penjelasan singkat).
  - SETIAP entitas wajib muncul di minimal satu hubungan. Entitas yang tidak dapat dihubungkan jangan ditulis.
  - Hubungan yang selalu dicari: peraturan memuat pasal; pasal mengatur kewajiban/hak/sanksi; pihak dikenai kewajiban atau memegang hak; pasal merujuk pasal lain ("sebagaimana dimaksud dalam"); pasal sanksi mengenakan sanksi atas pelanggaran pasal kewajiban.

3. **Jenis Baris:**
  - Baris `entity` hanya untuk entitas dan selalu terdiri atas tepat 4 bagian.
  - Baris `relation` hanya untuk hubungan dan selalu terdiri atas tepat 5 bagian.
  - Baris yang memuat dua nama entitas, kata kunci, dan deskripsi hubungan wajib diawali `relation`, tidak pernah `entity`.
  - Setelah baris entitas terakhir, gunakan awalan `relation` untuk setiap baris hubungan.

4. **Format Output:**
  - Baris entitas: `entity{tuple_delimiter}nama_entitas{tuple_delimiter}jenis_entitas{tuple_delimiter}deskripsi_entitas`
  - Baris hubungan: `relation{tuple_delimiter}entitas_sumber{tuple_delimiter}entitas_target{tuple_delimiter}kata_kunci_hubungan{tuple_delimiter}deskripsi_hubungan`
  - `{tuple_delimiter}` adalah penanda pemisah utuh dan **tidak boleh diisi apa pun**.
  - Kata kunci hubungan yang lebih dari satu dipisahkan koma `,`, **jangan** dengan `{tuple_delimiter}`.

5. **Urutan, Batas, dan Duplikasi:**
  - Tulis semua entitas terlebih dahulu, lalu semua hubungan.
  - Paling banyak {max_total_records} baris total dan paling banyak {max_entity_records} baris entitas. Tulis lebih sedikit bila memang sedikit; jangan mengisi batas.
  - Hanya tulis hubungan yang entitas sumber dan targetnya ada di daftar entitas jawaban ini.
  - Bila batas tercapai, berhenti dan tulis `{completion_delimiter}`.
  - Hubungan dianggap tidak berarah kecuali teks menyatakan arah. Jangan menulis hubungan yang sama dua kali.
  - Tulis hubungan yang paling penting bagi isi norma lebih dahulu.

6. **Aturan Penamaan Entitas:**
  - Nama peraturan ditulis "UU Nomor 45 Tahun 2009", "UU Nomor 31 Tahun 2004", "PP Nomor X Tahun Y", "KUHP", tanpa "tentang ...".
  - Pasal SELALU disertai nama peraturannya: "Pasal 93 ayat (1) UU Nomor 45 Tahun 2009", "Pasal 7 ayat (2) huruf a UU Nomor 45 Tahun 2009". Ambil nama peraturan dari kepala teks; rujukan "sebagaimana dimaksud dalam Pasal X" tanpa nama peraturan lain berarti peraturan yang sama. Jika chunk diawali "Pasal X (lanjutan)", ayat-ayat di awal chunk adalah milik Pasal X. Jangan pernah membuat entitas "Ayat 1", "Ayat (2)", atau "Huruf a" tanpa nomor pasal.
  - Istilah yang punya singkatan ditulis dengan kepanjangannya: "Surat Izin Penangkapan Ikan" (bukan "SIPI"), "Zona Ekonomi Eksklusif Indonesia" (bukan "ZEEI"); sebutkan singkatannya di deskripsi.
  - Gunakan istilah persis seperti di teks, bentuk dasar dan tunggal, huruf kapital di awal kata. Satu konsep = satu nama di seluruh output, dengan penulisan huruf besar-kecil yang sama.
  - Sanksi ditulis dengan angka seperti di teks: "Pidana Penjara Paling Lama 6 Tahun", "Denda Paling Banyak Rp2.000.000.000,00".
  - Jangan membuat entitas dari kata umum (ketentuan, hal, kegiatan, pelaksanaan), contoh daftar spesies biologis/hewan pada penjelasan definisi ikan (seperti paus, lumba-lumba, kodok, buaya, kepiting), atau dari pengetahuan di luar teks.

7. **Konteks dan Bahasa:**
  - Jika ada bagian `---Section Context---`, gunakan hanya sebagai latar; jangan mengekstrak entitas dari teks judul bagian itu.
  - Seluruh output (nama entitas, kata kunci, deskripsi) ditulis dalam {language} (Bahasa Indonesia). Jangan menerjemahkan istilah hukum ke bahasa Inggris.
  - Deskripsi ditulis sebagai orang ketiga, tanpa kata ganti seperti "pasal ini" atau "undang-undang ini"; sebut namanya secara eksplisit.

8. **Keamanan Templat:**
  - Bagian `---Contoh---` hanya contoh; jangan menyalin entitas atau hubungan dari contoh kecuali memang tertulis di teks masukan.
  - Token dalam kurung sudut seperti `<entity_name>` adalah penanda tempat; jangan pernah menuliskannya.
  - Jangan menulis analisis, penalaran, pembuka, penutup, markdown, atau bahasa Inggris. Mulai langsung dengan baris `entity` pertama.

9. **Sinyal Selesai:** Tulis `{completion_delimiter}` hanya setelah semua entitas dan hubungan selesai ditulis. Jika teks tidak memuat norma hukum (misalnya hanya "Cukup jelas." atau hanya judul), tulis `{completion_delimiter}` saja.

---Jenis Entitas---
{entity_types_guidance}

---Contoh---
Contoh berikut menunjukkan teks masukan dan output yang benar. Contoh BUKAN teks sumber.

{examples}
"""

ENTITY_EXTRACTION_USER_PROMPT = """---Tugas---
Ekstrak entitas dan hubungan dari bagian `---Input Text---` di bawah.

---Instruksi---
1. **Format:** Patuhi seluruh aturan format, urutan, pemisah, dan penamaan pada prompt sistem.
2. **Batas Jumlah:** Paling banyak {max_total_records} baris total dan paling banyak {max_entity_records} baris entitas. Hanya tulis hubungan yang kedua entitasnya ada di jawaban ini.
3. **Hanya Output:** Tulis hanya daftar entitas dan hubungan, tanpa pembuka, penjelasan, atau penalaran.
4. **Sinyal Selesai:** Akhiri dengan `{completion_delimiter}`. Jika teks tidak memuat norma hukum, tulis `{completion_delimiter}` saja.
5. **Bahasa:** Seluruh output dalam {language} (Bahasa Indonesia); istilah hukum tidak diterjemahkan.

{heading_context_block}---Input Text---
```
{input_text}
```

---Output---
"""

ENTITY_CONTINUE_EXTRACTION_USER_PROMPT = """---Tugas---
Periksa kembali teks masukan pada tugas sebelumnya. Tambahkan HANYA entitas yang tertulis di teks tetapi belum diekstrak, hubungan untuk entitas yang belum punya hubungan, dan baris yang sebelumnya terpotong atau salah format.

---Instruksi---
1. **Format:** Patuhi seluruh aturan format dan penamaan pada prompt sistem. Hubungan selalu diawali `relation`.
2. **Jangan Mengulang:** Jangan menulis ulang entitas atau hubungan yang sudah benar dan lengkap. Jangan menambah pengetahuan di luar teks.
3. **Batas Jumlah:** Paling banyak {max_total_records} baris total dan {max_entity_records} baris entitas. Hubungan boleh merujuk entitas yang sudah diekstrak sebelumnya.
4. **Hanya Output:** Tulis hanya daftar baris, tanpa penjelasan.
5. **Sinyal Selesai:** Akhiri dengan `{completion_delimiter}`. Jika tidak ada tambahan, tulis `{completion_delimiter}` saja.
6. **Bahasa:** {language} (Bahasa Indonesia).

---Output---
"""

# Contoh few-shot dari teks asli UU Nomor 45 Tahun 2009 (format baris LightRAG).
ENTITY_EXTRACTION_EXAMPLES = [
"""Contoh 1:
<Input Text>
```
UU Nomor 45 Tahun 2009 | Pasal 93
Pasal 93
(1) Setiap orang yang memiliki dan/atau mengoperasikan kapal penangkap ikan berbendera Indonesia melakukan penangkapan ikan di wilayah pengelolaan perikanan Negara Republik Indonesia dan/atau di laut lepas, yang tidak memiliki SIPI sebagaimana dimaksud dalam Pasal 27 ayat (1), dipidana dengan pidana penjara paling lama 6 (enam) tahun dan denda paling banyak Rp2.000.000.000,00 (dua miliar rupiah).
(2) Setiap orang yang memiliki dan/atau mengoperasikan kapal penangkap ikan berbendera asing melakukan penangkapan ikan di ZEEI yang tidak memiliki SIPI sebagaimana dimaksud dalam Pasal 27 ayat (2), dipidana dengan pidana penjara paling lama 6 (enam) tahun dan denda paling banyak Rp20.000.000.000,00 (dua puluh miliar rupiah).
```

<Output>
entity{tuple_delimiter}UU Nomor 45 Tahun 2009{tuple_delimiter}dasar_hukum{tuple_delimiter}Undang-undang tentang perubahan atas UU Nomor 31 Tahun 2004 tentang Perikanan.
entity{tuple_delimiter}Pasal 93 ayat (1) UU Nomor 45 Tahun 2009{tuple_delimiter}struktur{tuple_delimiter}Ketentuan pidana bagi kapal penangkap ikan berbendera Indonesia yang menangkap ikan tanpa SIPI.
entity{tuple_delimiter}Pasal 27 ayat (1) UU Nomor 45 Tahun 2009{tuple_delimiter}struktur{tuple_delimiter}Ketentuan kewajiban memiliki SIPI bagi kapal penangkap ikan berbendera Indonesia.
entity{tuple_delimiter}Setiap Orang{tuple_delimiter}pihak{tuple_delimiter}Orang yang memiliki dan/atau mengoperasikan kapal penangkap ikan.
entity{tuple_delimiter}Kapal Penangkap Ikan Berbendera Indonesia{tuple_delimiter}konsep{tuple_delimiter}Kapal penangkap ikan berbendera Indonesia yang menangkap ikan di wilayah pengelolaan perikanan Negara Republik Indonesia dan/atau laut lepas.
entity{tuple_delimiter}Surat Izin Penangkapan Ikan{tuple_delimiter}konsep{tuple_delimiter}Izin penangkapan ikan yang disingkat SIPI.
entity{tuple_delimiter}Wilayah Pengelolaan Perikanan Negara Republik Indonesia{tuple_delimiter}konsep{tuple_delimiter}Wilayah tempat kapal berbendera Indonesia melakukan penangkapan ikan.
entity{tuple_delimiter}Pidana Penjara Paling Lama 6 Tahun{tuple_delimiter}sanksi{tuple_delimiter}Pidana penjara paling lama 6 (enam) tahun.
entity{tuple_delimiter}Denda Paling Banyak Rp2.000.000.000,00{tuple_delimiter}sanksi{tuple_delimiter}Denda paling banyak dua miliar rupiah.
entity{tuple_delimiter}Pasal 93 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}struktur{tuple_delimiter}Ketentuan pidana bagi kapal penangkap ikan berbendera asing yang menangkap ikan di ZEEI tanpa SIPI.
entity{tuple_delimiter}Pasal 27 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}struktur{tuple_delimiter}Ketentuan kewajiban memiliki SIPI bagi kapal penangkap ikan berbendera asing di ZEEI.
entity{tuple_delimiter}Kapal Penangkap Ikan Berbendera Asing{tuple_delimiter}konsep{tuple_delimiter}Kapal penangkap ikan berbendera asing yang menangkap ikan di ZEEI.
entity{tuple_delimiter}Zona Ekonomi Eksklusif Indonesia{tuple_delimiter}konsep{tuple_delimiter}Zona Ekonomi Eksklusif Indonesia, disingkat ZEEI.
entity{tuple_delimiter}Denda Paling Banyak Rp20.000.000.000,00{tuple_delimiter}sanksi{tuple_delimiter}Denda paling banyak dua puluh miliar rupiah.
relation{tuple_delimiter}UU Nomor 45 Tahun 2009{tuple_delimiter}Pasal 93 ayat (1) UU Nomor 45 Tahun 2009{tuple_delimiter}hierarki peraturan{tuple_delimiter}UU Nomor 45 Tahun 2009 memuat Pasal 93 ayat (1).
relation{tuple_delimiter}Pasal 93 ayat (1) UU Nomor 45 Tahun 2009{tuple_delimiter}Pasal 27 ayat (1) UU Nomor 45 Tahun 2009{tuple_delimiter}rujukan pasal, sanksi atas kewajiban{tuple_delimiter}Pasal 93 ayat (1) memidana pelanggaran kewajiban dalam Pasal 27 ayat (1).
relation{tuple_delimiter}Setiap Orang{tuple_delimiter}Kapal Penangkap Ikan Berbendera Indonesia{tuple_delimiter}subjek hukum{tuple_delimiter}Setiap orang memiliki dan/atau mengoperasikan kapal penangkap ikan berbendera Indonesia.
relation{tuple_delimiter}Kapal Penangkap Ikan Berbendera Indonesia{tuple_delimiter}Surat Izin Penangkapan Ikan{tuple_delimiter}kewajiban izin{tuple_delimiter}Kapal penangkap ikan berbendera Indonesia wajib memiliki SIPI.
relation{tuple_delimiter}Kapal Penangkap Ikan Berbendera Indonesia{tuple_delimiter}Wilayah Pengelolaan Perikanan Negara Republik Indonesia{tuple_delimiter}wilayah berlaku{tuple_delimiter}Kapal melakukan penangkapan ikan di wilayah pengelolaan perikanan Negara Republik Indonesia.
relation{tuple_delimiter}Pasal 93 ayat (1) UU Nomor 45 Tahun 2009{tuple_delimiter}Pidana Penjara Paling Lama 6 Tahun{tuple_delimiter}pengenaan sanksi{tuple_delimiter}Pasal 93 ayat (1) mengancam pidana penjara paling lama 6 tahun.
relation{tuple_delimiter}Pasal 93 ayat (1) UU Nomor 45 Tahun 2009{tuple_delimiter}Denda Paling Banyak Rp2.000.000.000,00{tuple_delimiter}pengenaan sanksi{tuple_delimiter}Pasal 93 ayat (1) mengancam denda paling banyak Rp2.000.000.000,00.
relation{tuple_delimiter}UU Nomor 45 Tahun 2009{tuple_delimiter}Pasal 93 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}hierarki peraturan{tuple_delimiter}UU Nomor 45 Tahun 2009 memuat Pasal 93 ayat (2).
relation{tuple_delimiter}Pasal 93 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}Pasal 27 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}rujukan pasal, sanksi atas kewajiban{tuple_delimiter}Pasal 93 ayat (2) memidana pelanggaran kewajiban dalam Pasal 27 ayat (2).
relation{tuple_delimiter}Setiap Orang{tuple_delimiter}Kapal Penangkap Ikan Berbendera Asing{tuple_delimiter}subjek hukum{tuple_delimiter}Setiap orang memiliki dan/atau mengoperasikan kapal penangkap ikan berbendera asing.
relation{tuple_delimiter}Kapal Penangkap Ikan Berbendera Asing{tuple_delimiter}Zona Ekonomi Eksklusif Indonesia{tuple_delimiter}wilayah berlaku{tuple_delimiter}Kapal berbendera asing melakukan penangkapan ikan di ZEEI.
relation{tuple_delimiter}Kapal Penangkap Ikan Berbendera Asing{tuple_delimiter}Surat Izin Penangkapan Ikan{tuple_delimiter}kewajiban izin{tuple_delimiter}Kapal berbendera asing di ZEEI wajib memiliki SIPI.
relation{tuple_delimiter}Pasal 93 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}Pidana Penjara Paling Lama 6 Tahun{tuple_delimiter}pengenaan sanksi{tuple_delimiter}Pasal 93 ayat (2) mengancam pidana penjara paling lama 6 tahun.
relation{tuple_delimiter}Pasal 93 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}Denda Paling Banyak Rp20.000.000.000,00{tuple_delimiter}pengenaan sanksi{tuple_delimiter}Pasal 93 ayat (2) mengancam denda paling banyak Rp20.000.000.000,00.
{completion_delimiter}

Contoh 2:
<Input Text>
```
UU Nomor 45 Tahun 2009 | Ketentuan Umum | Pasal 25
Beberapa ketentuan dalam Undang-Undang Nomor 31 Tahun 2004 tentang Perikanan diubah sebagai berikut:
9. Ketentuan Pasal 25 diubah sehingga Pasal 25 berbunyi sebagai berikut:
Pasal 25
(1) Usaha perikanan dilaksanakan dalam sistem bisnis perikanan, meliputi praproduksi, produksi, pengolahan, dan pemasaran.
(2) Ketentuan lebih lanjut mengenai praproduksi, produksi, pengolahan, dan pemasaran sebagaimana dimaksud pada ayat (1) diatur dalam Peraturan Menteri.
```

<Output>
entity{tuple_delimiter}UU Nomor 45 Tahun 2009{tuple_delimiter}dasar_hukum{tuple_delimiter}Undang-undang yang mengubah UU Nomor 31 Tahun 2004 tentang Perikanan.
entity{tuple_delimiter}UU Nomor 31 Tahun 2004{tuple_delimiter}dasar_hukum{tuple_delimiter}Undang-undang tentang Perikanan yang sebagian ketentuannya diubah oleh UU Nomor 45 Tahun 2009.
entity{tuple_delimiter}Pasal 25 ayat (1) UU Nomor 45 Tahun 2009{tuple_delimiter}struktur{tuple_delimiter}Ketentuan bahwa usaha perikanan dilaksanakan dalam sistem bisnis perikanan.
entity{tuple_delimiter}Usaha Perikanan{tuple_delimiter}konsep{tuple_delimiter}Usaha yang dilaksanakan dalam sistem bisnis perikanan.
entity{tuple_delimiter}Sistem Bisnis Perikanan{tuple_delimiter}konsep{tuple_delimiter}Sistem yang meliputi praproduksi, produksi, pengolahan, dan pemasaran.
entity{tuple_delimiter}Pasal 25 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}struktur{tuple_delimiter}Ketentuan delegasi pengaturan sistem bisnis perikanan kepada Peraturan Menteri.
entity{tuple_delimiter}Peraturan Menteri{tuple_delimiter}dasar_hukum{tuple_delimiter}Peraturan yang mengatur lebih lanjut praproduksi, produksi, pengolahan, dan pemasaran.
relation{tuple_delimiter}UU Nomor 45 Tahun 2009{tuple_delimiter}UU Nomor 31 Tahun 2004{tuple_delimiter}perubahan peraturan{tuple_delimiter}UU Nomor 45 Tahun 2009 mengubah beberapa ketentuan UU Nomor 31 Tahun 2004.
relation{tuple_delimiter}UU Nomor 45 Tahun 2009{tuple_delimiter}Pasal 25 ayat (1) UU Nomor 45 Tahun 2009{tuple_delimiter}hierarki peraturan, perubahan pasal{tuple_delimiter}UU Nomor 45 Tahun 2009 mengubah dan memuat Pasal 25 ayat (1).
relation{tuple_delimiter}Pasal 25 ayat (1) UU Nomor 45 Tahun 2009{tuple_delimiter}Usaha Perikanan{tuple_delimiter}pengaturan{tuple_delimiter}Pasal 25 ayat (1) mengatur pelaksanaan usaha perikanan.
relation{tuple_delimiter}Usaha Perikanan{tuple_delimiter}Sistem Bisnis Perikanan{tuple_delimiter}pelaksanaan usaha{tuple_delimiter}Usaha perikanan dilaksanakan dalam sistem bisnis perikanan.
relation{tuple_delimiter}Pasal 25 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}Pasal 25 ayat (1) UU Nomor 45 Tahun 2009{tuple_delimiter}rujukan pasal{tuple_delimiter}Pasal 25 ayat (2) merujuk pada ayat (1).
relation{tuple_delimiter}Pasal 25 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}Peraturan Menteri{tuple_delimiter}delegasi pengaturan{tuple_delimiter}Pasal 25 ayat (2) mendelegasikan pengaturan lebih lanjut kepada Peraturan Menteri.
{completion_delimiter}

Contoh 3:
<Input Text>
```
UU Nomor 45 Tahun 2009 | Penjelasan Resmi | Penjelasan Pasal 25B
Pasal 25B Cukup jelas.
```

<Output>
{completion_delimiter}""",
]

SUMMARIZE_ENTITY_DESCRIPTIONS = """---Peran---
Anda bertugas menggabungkan beberapa deskripsi dari entitas atau hubungan hukum yang sama menjadi satu deskripsi.

---Instruksi---
1. Masukan berupa daftar deskripsi dalam format JSON, satu objek per baris.
2. Hapus kalimat yang berulang atau bermakna sama; simpan setiap fakta yang berbeda (nomor pasal, besaran sanksi, sifat kumulatif/alternatif, pihak, wilayah, jangka waktu).
3. Jangan menambahkan informasi yang tidak ada di daftar deskripsi.
4. Jika ada pertentangan, tulis keduanya beserta pasal sumbernya; jangan memilih sendiri. Jika ternyata nama yang sama dipakai untuk dua hal berbeda, ringkas masing-masing secara terpisah.
5. Tulis sebagai orang ketiga, sebut nama lengkap entitas atau hubungan di awal, tanpa pembuka atau penalaran.
6. Panjang paling banyak {summary_length} token. Seluruh output dalam {language} (Bahasa Indonesia).

---Input---
{description_type} Name: {description_name}

Daftar Deskripsi:

```
{description_list}
```

---Output---
"""


def apply_prompts(extra_addon_params=None):
    """Pasang prompt Indonesia ke LightRAG dan kembalikan addon_params."""
    from lightrag.prompt import PROMPTS
    PROMPTS["entity_extraction_system_prompt"] = ENTITY_EXTRACTION_SYSTEM_PROMPT
    PROMPTS["entity_extraction_user_prompt"] = ENTITY_EXTRACTION_USER_PROMPT
    PROMPTS["entity_continue_extraction_user_prompt"] = ENTITY_CONTINUE_EXTRACTION_USER_PROMPT
    PROMPTS["entity_extraction_examples"] = list(ENTITY_EXTRACTION_EXAMPLES)
    PROMPTS["default_entity_types_guidance"] = ENTITY_TYPES_GUIDANCE
    PROMPTS["summarize_entity_descriptions"] = SUMMARIZE_ENTITY_DESCRIPTIONS
    params = {
        "language": LANGUAGE,
        "entity_types": ENTITY_TYPES,
        "entity_types_guidance": ENTITY_TYPES_GUIDANCE,
    }
    params.update(extra_addon_params or {})
    return params

