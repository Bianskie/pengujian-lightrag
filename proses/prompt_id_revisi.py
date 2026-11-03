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
-Contoh-
######################
Contoh 1:

Entity_types: [dasar_hukum, struktur, konsep, sanksi, pihak, kewajiban]
Text:
Pasal 5 ayat (1) UU PDP menyatakan bahwa Pengendali Data Pribadi wajib memperoleh persetujuan dari Subjek Data Pribadi sebelum melakukan pemrosesan data. Pelanggaran terhadap ketentuan ini dapat dikenakan sanksi administratif berupa denda paling banyak 2% dari pendapatan tahunan, sebagaimana diatur dalam Pasal 57. Korporasi yang melakukan pelanggaran ini juga dapat dikenakan sanksi pidana berupa pidana penjara paling lama 5 tahun.

################
Output:
("entity"{tuple_delimiter}"UU PDP"{tuple_delimiter}"dasar_hukum"{tuple_delimiter}"Undang-Undang Pelindungan Data Pribadi yang mengatur hak dan kewajiban terkait pemrosesan data pribadi di Indonesia."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 5"{tuple_delimiter}"struktur"{tuple_delimiter}"Pasal yang mengatur kewajiban perolehan persetujuan dalam pemrosesan data pribadi."){record_delimiter}
("entity"{tuple_delimiter}"Ayat 1"{tuple_delimiter}"struktur"{tuple_delimiter}"Ayat pertama dari Pasal 5 yang menjelaskan kewajiban persetujuan."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 57"{tuple_delimiter}"struktur"{tuple_delimiter}"Pasal yang mengatur sanksi administratif atas pelanggaran UU PDP."){record_delimiter}
("entity"{tuple_delimiter}"Pengendali Data Pribadi"{tuple_delimiter}"pihak"{tuple_delimiter}"Pihak yang menentukan tujuan dan melakukan kendali pemrosesan data pribadi."){record_delimiter}
("entity"{tuple_delimiter}"Subjek Data Pribadi"{tuple_delimiter}"pihak"{tuple_delimiter}"Orang perseorangan yang data pribadinya diproses."){record_delimiter}
("entity"{tuple_delimiter}"Korporasi"{tuple_delimiter}"pihak"{tuple_delimiter}"Badan hukum yang dapat bertanggung jawab atas pelanggaran ketentuan data pribadi."){record_delimiter}
("entity"{tuple_delimiter}"Persetujuan"{tuple_delimiter}"konsep"{tuple_delimiter}"Pernyataan izin dari subjek data pribadi untuk pemrosesan datanya."){record_delimiter}
("entity"{tuple_delimiter}"Pemrosesan Data"{tuple_delimiter}"konsep"{tuple_delimiter}"Kegiatan pengolahan data pribadi yang dilakukan oleh pengendali data."){record_delimiter}
("entity"{tuple_delimiter}"Sanksi Administratif"{tuple_delimiter}"sanksi"{tuple_delimiter}"Denda administratif paling banyak 2% dari pendapatan tahunan."){record_delimiter}
("entity"{tuple_delimiter}"Sanksi Pidana"{tuple_delimiter}"sanksi"{tuple_delimiter}"Pidana penjara paling lama 5 tahun untuk korporasi yang melanggar."){record_delimiter}
("entity"{tuple_delimiter}"Kewajiban Persetujuan"{tuple_delimiter}"kewajiban"{tuple_delimiter}"Kewajiban pengendali data untuk memperoleh persetujuan sebelum pemrosesan data."){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 5"{tuple_delimiter}"Ayat 1"{tuple_delimiter}"Pasal 5 memuat Ayat 1 sebagai bagian struktural hierarkis."{tuple_delimiter}"hierarki struktur"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"UU PDP"{tuple_delimiter}"Pasal 5"{tuple_delimiter}"UU PDP memuat Pasal 5 sebagai salah satu pasalnya."{tuple_delimiter}"hierarki peraturan"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Ayat 1"{tuple_delimiter}"Pengendali Data Pribadi"{tuple_delimiter}"Ayat 1 mengatur kewajiban yang harus dipenuhi oleh Pengendali Data Pribadi."{tuple_delimiter}"pengaturan kewajiban"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pengendali Data Pribadi"{tuple_delimiter}"Kewajiban Persetujuan"{tuple_delimiter}"Pengendali Data Pribadi wajib melakukan kewajiban persetujuan."{tuple_delimiter}"subjek kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pengendali Data Pribadi"{tuple_delimiter}"Subjek Data Pribadi"{tuple_delimiter}"Pengendali Data Pribadi harus memperoleh persetujuan dari Subjek Data Pribadi."{tuple_delimiter}"hubungan hukum"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 57"{tuple_delimiter}"Sanksi Administratif"{tuple_delimiter}"Pasal 57 mengatur jenis dan besaran sanksi administratif."{tuple_delimiter}"pengaturan sanksi"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Korporasi"{tuple_delimiter}"Sanksi Pidana"{tuple_delimiter}"Korporasi dapat dikenakan sanksi pidana atas pelanggaran."{tuple_delimiter}"pengenaan sanksi"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 5"{tuple_delimiter}"Pasal 57"{tuple_delimiter}"Pasal 5 merujuk pada Pasal 57 untuk sanksi pelanggaran."{tuple_delimiter}"rujukan pasal"{tuple_delimiter}7){record_delimiter}
("content_keywords"{tuple_delimiter}"perlindungan data pribadi, kewajiban persetujuan, sanksi pelanggaran, pengendali data"){completion_delimiter}
#############################
Contoh 2:

Entity_types: [dasar_hukum, struktur, konsep, sanksi, pihak, kewajiban, hak]
Text:
Bab III UU Cipta Kerja mengatur tentang Kemudahan Berusaha. Pasal 18 menyebutkan bahwa setiap pelaku usaha berhak mendapatkan pelayanan perizinan yang cepat dan sederhana. Pemerintah wajib menyediakan sistem Online Single Submission (OSS) untuk mempermudah proses perizinan. Pelanggaran terhadap batas waktu penerbitan izin dapat diajukan gugatan ke Pengadilan Tata Usaha Negara.

#############
Output:
("entity"{tuple_delimiter}"UU Cipta Kerja"{tuple_delimiter}"dasar_hukum"{tuple_delimiter}"Undang-Undang yang mengatur tentang penciptaan lapangan kerja dan kemudahan berusaha."){record_delimiter}
("entity"{tuple_delimiter}"Bab III"{tuple_delimiter}"struktur"{tuple_delimiter}"Bab yang mengatur tentang Kemudahan Berusaha dalam UU Cipta Kerja."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 18"{tuple_delimiter}"struktur"{tuple_delimiter}"Pasal yang mengatur hak pelaku usaha atas pelayanan perizinan."){record_delimiter}
("entity"{tuple_delimiter}"Pelaku Usaha"{tuple_delimiter}"pihak"{tuple_delimiter}"Orang atau badan yang melakukan kegiatan usaha."){record_delimiter}
("entity"{tuple_delimiter}"Pemerintah"{tuple_delimiter}"pihak"{tuple_delimiter}"Institusi negara yang berkewajiban menyediakan sistem perizinan."){record_delimiter}
("entity"{tuple_delimiter}"Pengadilan Tata Usaha Negara"{tuple_delimiter}"pihak"{tuple_delimiter}"Lembaga peradilan yang berwenang mengadili sengketa administrasi negara."){record_delimiter}
("entity"{tuple_delimiter}"Kemudahan Berusaha"{tuple_delimiter}"konsep"{tuple_delimiter}"Prinsip penyederhanaan proses dan persyaratan berusaha."){record_delimiter}
("entity"{tuple_delimiter}"Pelayanan Perizinan"{tuple_delimiter}"konsep"{tuple_delimiter}"Layanan penerbitan izin usaha yang harus cepat dan sederhana."){record_delimiter}
("entity"{tuple_delimiter}"Online Single Submission"{tuple_delimiter}"konsep"{tuple_delimiter}"Sistem perizinan berusaha terintegrasi secara elektronik."){record_delimiter}
("entity"{tuple_delimiter}"Hak Pelayanan"{tuple_delimiter}"hak"{tuple_delimiter}"Hak pelaku usaha untuk mendapat pelayanan perizinan yang cepat dan sederhana."){record_delimiter}
("entity"{tuple_delimiter}"Kewajiban Penyediaan OSS"{tuple_delimiter}"kewajiban"{tuple_delimiter}"Kewajiban pemerintah untuk menyediakan sistem OSS."){record_delimiter}
("relationship"{tuple_delimiter}"UU Cipta Kerja"{tuple_delimiter}"Bab III"{tuple_delimiter}"UU Cipta Kerja memuat Bab III sebagai bagian strukturnya."{tuple_delimiter}"hierarki struktur"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Bab III"{tuple_delimiter}"Pasal 18"{tuple_delimiter}"Bab III memuat Pasal 18 di dalamnya."{tuple_delimiter}"hierarki pasal"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 18"{tuple_delimiter}"Hak Pelayanan"{tuple_delimiter}"Pasal 18 mengatur tentang hak pelayanan bagi pelaku usaha."{tuple_delimiter}"pengaturan hak"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pelaku Usaha"{tuple_delimiter}"Hak Pelayanan"{tuple_delimiter}"Pelaku Usaha memiliki hak untuk mendapat pelayanan perizinan."{tuple_delimiter}"subjek hak"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pemerintah"{tuple_delimiter}"Kewajiban Penyediaan OSS"{tuple_delimiter}"Pemerintah wajib menyediakan sistem OSS."{tuple_delimiter}"subjek kewajiban"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pelaku Usaha"{tuple_delimiter}"Pengadilan Tata Usaha Negara"{tuple_delimiter}"Pelaku Usaha dapat mengajukan gugatan ke PTUN atas pelanggaran batas waktu perizinan."{tuple_delimiter}"upaya hukum"{tuple_delimiter}7){completion_delimiter}
("content_keywords"{tuple_delimiter}"kemudahan berusaha, perizinan, sistem OSS, hak pelaku usaha"){completion_delimiter}
#############################
Contoh 3:

Entity_types: [dasar_hukum, struktur, konsep, sanksi, pihak, kewajiban, hak]
Text:
Pasal 362 KUHP mengatur tentang tindak pidana pencurian. Barangsiapa mengambil barang sesuatu yang seluruhnya atau sebagian kepunyaan orang lain, dengan maksud untuk dimiliki secara melawan hukum, diancam karena pencurian dengan pidana penjara paling lama lima tahun atau pidana denda paling banyak enam puluh juta rupiah. Jika pencurian dilakukan oleh dua orang atau lebih secara bersama-sama, maka berlaku ketentuan Pasal 363 tentang pencurian dengan pemberatan.

#############
Output:
("entity"{tuple_delimiter}"KUHP"{tuple_delimiter}"dasar_hukum"{tuple_delimiter}"Kitab Undang-Undang Hukum Pidana yang mengatur berbagai tindak pidana dan sanksinya."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 362"{tuple_delimiter}"struktur"{tuple_delimiter}"Pasal yang mengatur tindak pidana pencurian biasa."){record_delimiter}
("entity"{tuple_delimiter}"Pasal 363"{tuple_delimiter}"struktur"{tuple_delimiter}"Pasal yang mengatur pencurian dengan pemberatan."){record_delimiter}
("entity"{tuple_delimiter}"Pencurian"{tuple_delimiter}"konsep"{tuple_delimiter}"Tindak pidana mengambil barang milik orang lain dengan maksud memiliki secara melawan hukum."){record_delimiter}
("entity"{tuple_delimiter}"Melawan Hukum"{tuple_delimiter}"konsep"{tuple_delimiter}"Perbuatan yang bertentangan dengan hukum atau tanpa hak."){record_delimiter}
("entity"{tuple_delimiter}"Pencurian dengan Pemberatan"{tuple_delimiter}"konsep"{tuple_delimiter}"Pencurian yang dilakukan dengan keadaan memberatkan seperti dilakukan bersama-sama."){record_delimiter}
("entity"{tuple_delimiter}"Pidana Penjara"{tuple_delimiter}"sanksi"{tuple_delimiter}"Sanksi pidana berupa penjara paling lama lima tahun."){record_delimiter}
("entity"{tuple_delimiter}"Pidana Denda"{tuple_delimiter}"sanksi"{tuple_delimiter}"Sanksi pidana berupa denda paling banyak enam puluh juta rupiah."){record_delimiter}
("entity"{tuple_delimiter}"Pelaku"{tuple_delimiter}"pihak"{tuple_delimiter}"Orang yang melakukan tindak pidana pencurian."){record_delimiter}
("entity"{tuple_delimiter}"Korban"{tuple_delimiter}"pihak"{tuple_delimiter}"Orang yang barangnya diambil oleh pelaku pencurian."){record_delimiter}
("relationship"{tuple_delimiter}"KUHP"{tuple_delimiter}"Pasal 362"{tuple_delimiter}"KUHP memuat Pasal 362 sebagai salah satu ketentuan pidananya."{tuple_delimiter}"hierarki peraturan"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 362"{tuple_delimiter}"Pencurian"{tuple_delimiter}"Pasal 362 mendefinisikan dan mengatur tindak pidana pencurian."{tuple_delimiter}"definisi konsep"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 362"{tuple_delimiter}"Pidana Penjara"{tuple_delimiter}"Pasal 362 mengatur sanksi pidana penjara untuk tindak pencurian."{tuple_delimiter}"pengaturan sanksi"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 362"{tuple_delimiter}"Pidana Denda"{tuple_delimiter}"Pasal 362 mengatur sanksi pidana denda untuk tindak pencurian."{tuple_delimiter}"pengaturan sanksi"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Pasal 362"{tuple_delimiter}"Pasal 363"{tuple_delimiter}"Pasal 362 merujuk pada Pasal 363 untuk kasus pencurian dengan pemberatan."{tuple_delimiter}"rujukan pasal"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"Pelaku"{tuple_delimiter}"Korban"{tuple_delimiter}"Pelaku mengambil barang kepunyaan korban secara melawan hukum."{tuple_delimiter}"hubungan tindak pidana"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"Pencurian"{tuple_delimiter}"Pencurian dengan Pemberatan"{tuple_delimiter}"Pencurian dapat menjadi pencurian dengan pemberatan jika memenuhi unsur tertentu."{tuple_delimiter}"gradasi tindak pidana"{tuple_delimiter}7){completion_delimiter}
("content_keywords"{tuple_delimiter}"tindak pidana pencurian, sanksi pidana, melawan hukum, pemberatan"){completion_delimiter}
#############################
-Data Sebenarnya-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:
"""


PROMPTS[
    "summarize_entity_descriptions"
] = """Anda adalah asisten yang bertanggung jawab menghasilkan ringkasan komprehensif dari data yang diberikan di bawah ini.
Diberikan satu atau dua entitas, dan daftar deskripsi, semuanya terkait dengan entitas yang sama atau kelompok entitas.
Silakan gabungkan semua ini menjadi satu deskripsi komprehensif. Pastikan untuk menyertakan informasi yang dikumpulkan dari semua deskripsi.
Jika deskripsi yang diberikan bertentangan, silakan selesaikan kontradiksi tersebut dan berikan ringkasan tunggal yang koheren.
Pastikan ditulis dalam orang ketiga, dan sertakan nama entitas sehingga kita memiliki konteks lengkap.

#######
-Data-
Entitas: {entity_name}
Daftar Deskripsi: {description_list}
#######
Output:
"""

PROMPTS[
    "entiti_continue_extraction"
] = """BANYAK entitas yang terlewat dalam ekstraksi terakhir. Tambahkan di bawah ini menggunakan format yang sama:
"""


PROMPTS[
    "entiti_continue_extraction_mini"
] = """BANYAK entitas yang terlewat dalam ekstraksi terakhir.
Setelah merangkum semua informasi yang sebelumnya diekstrak, dibandingkan dengan teks asli, terlihat bahwa informasi berikut terutama dihilangkan:
{omit}

Jenis entitas yang perlu ditambahkan dapat diperoleh dari Entity_types,
atau Anda dapat menambahkannya sendiri.

Entity_types: {entity_types}


Tambahkan di bawah ini menggunakan format yang sama:
"""


PROMPTS["minirag_query2kwd"] = """---Peran---

Anda adalah asisten yang bertugas mengidentifikasi kata kunci jenis-jawaban dan kata kunci tingkat rendah dalam pertanyaan pengguna.

---Tujuan---

Diberikan pertanyaan, buat daftar kata kunci jenis-jawaban dan kata kunci tingkat rendah.
kata kunci jenis-jawaban fokus pada jenis jawaban untuk pertanyaan tertentu, sedangkan kata kunci tingkat rendah fokus pada entitas spesifik, detail, atau istilah konkret.
Kata kunci jenis-jawaban harus dipilih dari kumpulan jenis jawaban.
Kumpulan ini dalam bentuk kamus, di mana kunci mewakili Jenis yang harus Anda pilih dan nilai mewakili contoh sampel.

---Instruksi---

- Output kata kunci dalam format JSON.
- JSON harus memiliki tiga kunci:
  - "answer_type_keywords" untuk jenis jawaban. Dalam daftar ini, jenis dengan kemungkinan tertinggi harus ditempatkan di depan. Tidak lebih dari 3.
  - "entities_from_query" untuk entitas atau detail spesifik. Harus diekstrak dari pertanyaan.
######################
-Contoh-
######################
Contoh 1:

Query: "Apa sanksi bagi perusahaan yang melanggar UU Perlindungan Data Pribadi?"
Answer type pool: {{
 'DASAR HUKUM': ['UU PDP', 'PERMENKOMINFO', 'PP NOMOR 71 TAHUN 2019'],
 'SANKSI': ['PIDANA PENJARA', 'DENDA ADMINISTRATIF', 'PENCABUTAN IZIN'],
 'KONSEP': ['DATA PRIBADI', 'PENGENDALI DATA', 'PERSETUJUAN'],
 'PIHAK': ['KORPORASI', 'PEMERINTAH', 'SUBJEK DATA'],
 'STRUKTUR': ['BAB I', 'PASAL 5', 'AYAT 1'],
 'KEWAJIBAN': ['PERLINDUNGAN DATA', 'PELAPORAN INSIDEN'],
 'HAK': ['HAK AKSES', 'HAK HAPUS DATA'],
 'PROSEDUR': ['PENGAJUAN KEBERATAN', 'AUDIT KEAMANAN']
}}
################
Output:
{{
  "answer_type_keywords": ["SANKSI", "DASAR HUKUM"],
  "entities_from_query": ["perusahaan", "UU Perlindungan Data Pribadi", "pelanggaran", "korporasi"]
}}
#############################
Contoh 2:

Query: "Siapa yang berwenang menangani sengketa perizinan usaha?"
Answer type pool: {{
 'PIHAK': ['PENGADILAN TATA USAHA NEGARA', 'OMBUDSMAN', 'PELAKU USAHA'],
 'PROSEDUR': ['GUGATAN', 'MEDIASI', 'ARBITRASE'],
 'KONSEP': ['SENGKETA ADMINISTRASI', 'PERIZINAN BERUSAHA', 'OSS'],
 'DASAR HUKUM': ['UU CIPTA KERJA', 'UU PERATUN'],
 'SANKSI': ['PEMBATALAN KEPUTUSAN', 'GANTI RUGI'],
 'STRUKTUR': ['PASAL 18', 'BAB III'],
 'KEWAJIBAN': ['PENERBITAN IZIN TEPAT WAKTU'],
 'HAK': ['HAK GUGAT', 'HAK BANDING']
}}

################
Output:
{{
  "answer_type_keywords": ["PIHAK", "PROSEDUR"],
  "entities_from_query": ["sengketa", "perizinan usaha", "kewenangan", "penyelesaian sengketa"]
}}
#############################
Contoh 3:

Query: "Apa yang dimaksud dengan pencurian dengan pemberatan dalam KUHP?"
Answer type pool: {{
 'KONSEP': ['PENCURIAN', 'PENCURIAN DENGAN PEMBERATAN', 'MELAWAN HUKUM'],
 'DASAR HUKUM': ['KUHP', 'PASAL 362', 'PASAL 363'],
 'SANKSI': ['PIDANA PENJARA', 'PIDANA DENDA'],
 'PIHAK': ['PELAKU', 'KORBAN', 'SAKSI'],
 'STRUKTUR': ['PASAL 363 AYAT 1', 'PASAL 363 AYAT 2'],
 'PROSEDUR': ['PENYIDIKAN', 'PENUNTUTAN']
}}

################
Output:
{{
  "answer_type_keywords": ["KONSEP", "DASAR HUKUM"],
  "entities_from_query": ["pencurian dengan pemberatan", "KUHP", "definisi", "unsur"]
}}
#############################

-Data Sebenarnya-
######################
Query: {query}
Answer type pool:{TYPE_POOL}
######################
Output:

"""


PROMPTS[
    "entiti_if_loop_extraction"
] = """Sepertinya beberapa entitas mungkin masih terlewat. Jawab YA | TIDAK jika masih ada entitas yang perlu ditambahkan.
"""

PROMPTS["fail_response"] = "Maaf, saya tidak dapat memberikan jawaban untuk pertanyaan tersebut."

PROMPTS["rag_response"] = """---Konteks---

{context_data}

---Peran---

Anda adalah asisten hukum yang ahli dan menjawab pertanyaan berbasis skenario kasus menggunakan HANYA
informasi dari konteks yang diberikan.

---Instruksi---

1. Jawab dalam Bahasa Indonesia yang baku dan jelas.
2. Dasarkan jawaban HANYA pada konteks yang diberikan. Jika informasi tidak ditemukan dalam konteks,
   nyatakan secara jujur bahwa informasi tidak tersedia -- JANGAN mengarang pasal atau ketentuan.
3. Sebutkan dasar hukum secara eksplisit (nama undang-undang, nomor pasal, dan ayat jika ada) untuk
   setiap klaim hukum yang Anda buat.
4. Jika pertanyaan melibatkan lebih dari satu ketentuan hukum, jelaskan keterkaitan antar-pasal tersebut.
5. Jawab mengalir dalam bentuk prosa, tanpa sub-bagian, header, atau markdown.
6. Jawab langsung pada substansi tanpa mengulang pertanyaan.

{response_type}
"""

PROMPTS["keywords_extraction"] = """---Peran---

Anda adalah asisten yang bertugas mengidentifikasi kata kunci tingkat tinggi dan tingkat rendah dalam pertanyaan pengguna.

---Tujuan---

Diberikan pertanyaan, buat daftar kata kunci tingkat tinggi dan tingkat rendah. Kata kunci tingkat tinggi fokus pada konsep atau tema menyeluruh, sedangkan kata kunci tingkat rendah fokus pada entitas spesifik, detail, atau istilah konkret.

---Instruksi---

- Output kata kunci dalam format JSON.
- JSON harus memiliki dua kunci:
  - "high_level_keywords" untuk konsep atau tema menyeluruh.
  - "low_level_keywords" untuk entitas atau detail spesifik.

######################
-Contoh-
######################
Contoh 1:

Query: "Bagaimana prosedur pengajuan gugatan pelanggaran data pribadi?"
################
Output:
{{
  "high_level_keywords": ["Prosedur hukum", "Gugatan", "Perlindungan data pribadi"],
  "low_level_keywords": ["Pengadilan", "Bukti pelanggaran", "Subjek data", "Tata cara pengajuan", "Persyaratan gugatan"]
}}
#############################
Contoh 2:

Query: "Apa sanksi pidana bagi pelaku pencurian dengan kekerasan?"
################
Output:
{{
  "high_level_keywords": ["Sanksi pidana", "Tindak pidana pencurian", "Hukum pidana"],
  "low_level_keywords": ["Pencurian dengan kekerasan", "Pidana penjara", "KUHP Pasal 365", "Pemberatan hukuman"]
}}
#############################
Contoh 3:

Query: "Siapa yang bertanggung jawab atas perlindungan data pribadi dalam suatu perusahaan?"
################
Output:
{{
  "high_level_keywords": ["Tanggung jawab hukum", "Perlindungan data", "Tata kelola perusahaan"],
  "low_level_keywords": ["Pengendali data", "Data protection officer", "Korporasi", "Kewajiban hukum"]
}}
#############################
-Data Sebenarnya-
######################
Query: {query}
######################
Output:

"""

PROMPTS["naive_rag_response"] = """---Peran---

Anda adalah asisten yang menjawab pertanyaan dengan sangat singkat, padat, dan langsung pada intinya.

---Tujuan---

Jawab pertanyaan pengguna berdasarkan dokumen yang diberikan.
PENTING:
1. Jawaban HARUS sangat singkat (maksimal 3 kalimat).
2. Langsung ke inti jawaban. Jangan gunakan kata pengantar.
3. Jangan mencoba merangkum semua dokumen. Ambil saja poin utamanya.

---Panjang dan format respons target---

{response_type}

---Dokumen---

{content_data}
"""