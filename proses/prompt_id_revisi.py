"""
Templat Prompt Ekstraksi Entitas & Relasi Hukum Bahasa Indonesia (Arsip Referensi V1)

Version     : 0.1.0
Created     : 02-11-2026
Description : Templat prompt generasi awal untuk ekstraksi entitas hukum, relasi antar-pasal,
              dan kueri RAG berbahasa Indonesia dengan 7 taksonomi entitas dasar
              (dasar_hukum, struktur, konsep, sanksi, pihak, kewajiban, hak).
              (Catatan: Untuk pipeline LightRAG V2, gunakan prompt_lightrag_id_v1.py).
"""

GRAPH_FIELD_SEP = "<SEP>"

PROMPTS = {}

PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|SELESAI|>"
PROMPTS["process_tickers"] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

PROMPTS["DEFAULT_ENTITY_TYPES"] = ["dasar_hukum", "struktur", "konsep", "sanksi", "pihak", "kewajiban", "hak"]


PROMPTS["entity_extraction"] = """-Tujuan-
Diberikan dokumen teks hukum yang relevan dan daftar jenis entitas, identifikasi semua entitas dari jenis tersebut beserta semua hubungan antar entitas yang teridentifikasi.

-Langkah-
1. Identifikasi semua entitas. Untuk setiap entitas yang teridentifikasi, ekstrak informasi berikut:
- entity_name: Nama entitas, gunakan bahasa Indonesia
- entity_type: Salah satu dari jenis berikut: [{entity_types}]
- entity_description: Deskripsi komprehensif tentang atribut dan aktivitas entitas
Format setiap entitas sebagai ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>

2. Dari entitas yang diidentifikasi pada langkah 1, identifikasi semua pasangan (source_entity, target_entity) yang *jelas berhubungan* satu sama lain.
Untuk setiap pasangan entitas yang berhubungan, ekstrak informasi berikut:
- source_entity: nama entitas sumber, seperti yang diidentifikasi pada langkah 1
- target_entity: nama entitas target, seperti yang diidentifikasi pada langkah 1
- relationship_description: penjelasan mengapa entitas sumber dan entitas target saling berhubungan
- relationship_strength: skor numerik yang menunjukkan kekuatan hubungan antara entitas sumber dan entitas target
- relationship_keywords: satu atau lebih kata kunci tingkat tinggi yang merangkum sifat menyeluruh dari hubungan, fokus pada konsep atau tema daripada detail spesifik
Format setiap hubungan sebagai ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identifikasi kata kunci tingkat tinggi yang merangkum konsep utama, tema, atau topik dari keseluruhan teks. Ini harus menangkap ide-ide menyeluruh yang ada dalam dokumen.
Format kata kunci tingkat konten sebagai ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Kembalikan output dalam Bahasa Indonesia sebagai satu daftar dari semua entitas dan hubungan yang diidentifikasi pada langkah 1 dan 2. Gunakan **{record_delimiter}** sebagai pembatas daftar.

5. Setelah selesai, output {completion_delimiter}

######################
-Data Sebenarnya-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:
"""

