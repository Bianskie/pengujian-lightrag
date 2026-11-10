"""
Prompt Indexing LightRAG Berbahasa Indonesia - V1.3 Legal-Relation

Updated     : Pabian
Version     : 1.3.0
Created     : 02-11-2026
Revised     : 10-11-2026
Description : Modul injeksi prompt ekstraksi entitas dan relasi hukum berbahasa Indonesia
              untuk engine LightRAG (lightrag-hku). Mengadopsi Standar Taksonomi Yuridis
              Nasional (UU No. 12/2011), penamaan entitas kanonik, eliminasi entitas
              umum/biologis (anti-hub bloat), penanganan otomatis teks non-normatif,
              serta mewajibkan edge kausal antara norma pelanggaran dan sanksi pidana.
"""

PROMPT_VERSION = "v1.3-legal-relation"
LANGUAGE = "Indonesian"
ENTITY_TYPES = ['dasar_hukum', 'struktur', 'pihak', 'kewajiban', 'hak', 'sanksi', 'konsep']

ENTITY_TYPES_GUIDANCE = """- dasar_hukum: UU/PP/Peraturan Menteri/UUD 1945
- struktur: pasal/ayat/huruf (contoh: Pasal 27 ayat (2) UU Nomor 45 Tahun 2009)
- pihak: subjek hukum spesifik (contoh: Kapal Penangkap Ikan Berbendera Asing, Pengawas Perikanan)
- kewajiban: perintah atau larangan perbuatan
- hak: wewenang atau hak
- sanksi: pidana penjara/kurungan/denda beserta angka/nominal eksplisit
- konsep: izin/dokumen teknis/wilayah (contoh: SIPI, ZEEI)"""

ENTITY_EXTRACTION_SYSTEM_PROMPT = """Peran: Analis Knowledge Graph Hukum Indonesia.
Tugas: Ekstrak entitas dan relasi hukum dari `---Input Text---`.

Aturan Format:
1. Format Entitas: entity{tuple_delimiter}nama_entitas{tuple_delimiter}jenis_entitas{tuple_delimiter}deskripsi
2. Format Relasi: relation{tuple_delimiter}entitas_sumber{tuple_delimiter}entitas_target{tuple_delimiter}kata_kunci{tuple_delimiter}deskripsi
3. Penamaan: UU ditulis "UU Nomor X Tahun Y", Pasal/Ayat wajib menyertakan nama UU ("Pasal 93 ayat (2) UU Nomor 45 Tahun 2009").
4. Aturan Relasi Sanksi: Setiap pasal/ayat yang memuat sanksi pidana/denda WAJIB dihubungkan langsung ke pasal pelanggaran acuannya dan ke subjek pelakunya dengan kata kunci "sanksi_pelanggaran" atau "ancaman_pidana".
5. Hindari Entitas Terlalu Umum: Jangan membuat entitas kata tunggal seperti "Orang", "Kapal", atau "Ikan" tanpa konteks yuridis.
6. Mulai langsung dengan baris entity pertama dan akhiri dengan {completion_delimiter}. Bahasa: {language}.

Jenis Entitas:
{entity_types_guidance}

Contoh:
{examples}
"""

ENTITY_EXTRACTION_USER_PROMPT = """Ekstrak entitas dan relasi dari teks berikut sesuai aturan. Akhiri dengan {completion_delimiter}.

{heading_context_block}---Input Text---
{input_text}

---Output---
"""

ENTITY_CONTINUE_EXTRACTION_USER_PROMPT = """Tambahkan entitas/relasi yang belum sempat terekstrak dari teks sebelumnya. Akhiri dengan {completion_delimiter}.

---Output---
"""

ENTITY_EXTRACTION_EXAMPLES = [
"""Contoh:
<Input Text>
Pasal 93 ayat (2) UU Nomor 45 Tahun 2009
Setiap orang yang mengoperasikan kapal penangkap ikan berbendera asing melakukan penangkapan ikan di ZEEI yang tidak memiliki SIPI sebagaimana dimaksud dalam Pasal 27 ayat (2), dipidana dengan pidana penjara paling lama 6 tahun dan denda paling banyak Rp20.000.000.000,00.
<Output>
entity{tuple_delimiter}Pasal 93 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}struktur{tuple_delimiter}Ketentuan pidana penangkapan ikan tanpa SIPI di ZEEI oleh kapal asing.
entity{tuple_delimiter}Pasal 27 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}struktur{tuple_delimiter}Kewajiban memiliki SIPI bagi kapal penangkap ikan berbendera asing di ZEEI.
entity{tuple_delimiter}Kapal Penangkap Ikan Berbendera Asing{tuple_delimiter}pihak{tuple_delimiter}Kapal perikanan berbendera selain Indonesia yang beroperasi di ZEEI.
entity{tuple_delimiter}Surat Izin Penangkapan Ikan{tuple_delimiter}konsep{tuple_delimiter}Izin tertulis penangkapan ikan (SIPI).
entity{tuple_delimiter}Pidana Penjara Paling Lama 6 Tahun dan Denda Paling Banyak Rp20.000.000.000,00{tuple_delimiter}sanksi{tuple_delimiter}Ancaman pidana penjara maksimal 6 tahun dan denda maksimal 20 miliar rupiah.
relation{tuple_delimiter}Pasal 93 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}Pasal 27 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}sanksi_pelanggaran{tuple_delimiter}Pasal 93 ayat (2) memuat sanksi pidana atas pelanggaran kewajiban pada Pasal 27 ayat (2).
relation{tuple_delimiter}Pasal 93 ayat (2) UU Nomor 45 Tahun 2009{tuple_delimiter}Pidana Penjara Paling Lama 6 Tahun dan Denda Paling Banyak Rp20.000.000.000,00{tuple_delimiter}ancaman_pidana{tuple_delimiter}Pasal 93 ayat (2) menjatuhkan sanksi penjara paling lama 6 tahun dan denda 20 miliar rupiah.
relation{tuple_delimiter}Kapal Penangkap Ikan Berbendera Asing{tuple_delimiter}Surat Izin Penangkapan Ikan{tuple_delimiter}kewajiban izin{tuple_delimiter}Kapal asing wajib memiliki SIPI untuk menangkap ikan di ZEEI.
{completion_delimiter}"""
]

SUMMARIZE_ENTITY_DESCRIPTIONS = """Gabungkan deskripsi entitas/relasi hukum berikut menjadi ringkasan faktual tanpa opini. Maksimal {summary_length} token. Bahasa: {language}.

{description_type} Name: {description_name}
Daftar Deskripsi:
{description_list}

---Output---
"""

def apply_prompts(extra_addon_params=None):
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