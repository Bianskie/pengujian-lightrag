#!/usr/bin/env python3
"""
Script Re-Chunking Semantik Boundary-Aware (512 Token + 100 Overlap + Header Regulasi Kanonik)

Author      : Pabian
Version     : 1.4.0
Created     : 02-11-2026
Revised     : 09-11-2026
Description : Pemotongan teks regulasi hasil ekstraksi MinerU (output.md) berbasis
              batas paragraf dan kalimat utuh dengan ukuran tepat 512 token dan
              100 token overlap (CHUNK_SIZE=512, CHUNK_OVERLAP=100) disertai injeksi
              kepala teks kanonik ('UU Nomor 45 Tahun 2009 | Pasal X') bebas lookahead leak.
              Langsung menggantikan berkas data/chunks_uu_45_2009.json untuk input LightRAG.
"""
import os
import sys
import json
import re
import shutil
import tiktoken

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "proses" else SCRIPT_DIR
DOC_PATH = os.path.join(ROOT_DIR, "data", "UU_Nomor_45_Tahun_2009", "output.md")
OUT_MAIN_PATH = os.path.join(ROOT_DIR, "data", "chunks_uu_45_2009.json")
OUT_512_PATH = os.path.join(ROOT_DIR, "data", "chunks_uu_45_2009_512.json")
BACKUP_144_PATH = os.path.join(ROOT_DIR, "data", "chunks_uu_45_2009_pasal_old.json")

CHUNK_SIZE = 512
CHUNK_OVERLAP = 100


def clean_markdown_text(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n\s*-\s*\d+\s*-\s*\n", "\n", text)
    text = re.sub(r"www\.djpp\.depkumham\.go\.id[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Lembaran Negara Republik Indonesia[^\n]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def detect_article_label(text: str, current_state: str) -> str:
    """Melacak pasal aktif secara kontekstual tanpa lookahead leak."""
    p_lower = text.lower()
    is_penjelasan = (
        "penjelasan" in current_state.lower()
        or "penjelasan atas" in p_lower
        or "# penjelasan" in p_lower
    )

    if is_penjelasan:
        m_penj_pasal = re.search(
            r"(?:(?:##|\*\*|Angka\s+\d+)\s*)?(?:Pasal|PASAL)\s+(\d+[a-zA-Z]?|[IVXLCDM]+)", text
        )
        if (
            m_penj_pasal
            and ("angka" in p_lower or "pasal" in p_lower)
            and (
                "cukup jelas" in p_lower
                or "ayat" in p_lower
                or "huruf" in p_lower
                or text.startswith("##")
                or text.startswith("**Pasal")
            )
        ):
            return f"Penjelasan Pasal {m_penj_pasal.group(1).upper()}"
        return current_state if "penjelasan" in current_state.lower() else "Penjelasan Umum"

    if any(
        k in p_lower
        for k in ["menimbang", "mengingat", "memutuskan", "presiden republik indonesia"]
    ) and not ("pasal i" in p_lower or "ketentuan pasal" in p_lower):
        if not re.search(r"##\s*Pasal", text, re.I):
            return "Pembukaan & Konsiderans"

    m_ins = re.search(
        r"disisipkan[^\n.]+?yakni\s+(?:Pasal|PASAL)\s+(\d+[a-zA-Z]?)", text, re.IGNORECASE
    )
    if m_ins:
        return f"Pasal {m_ins.group(1).upper()}"

    m_pasal = re.search(
        r"(?:##\s*|\*\*|Ketentuan\s+|Angka\s+\d+\s+)(?:Pasal|PASAL)\s+(\d+[a-zA-Z]?|[IVXLCDM]+)",
        text,
        re.IGNORECASE,
    )
    if m_pasal:
        return f"Pasal {m_pasal.group(1).upper()}"

    m_standalone = re.match(
        r"^(?:##|\*\*)\s*(?:Pasal|PASAL)\s+(\d+[a-zA-Z]?|[IVXLCDM]+)", text, re.IGNORECASE
    )
    if m_standalone:
        return f"Pasal {m_standalone.group(1).upper()}"

    return current_state


def get_chunk_pasal(paras_list):
    """Mengambil pasal acuan chunk dari paragraf substantif pertama (mengabaikan catchword . . .)."""
    for p_text, p_pasal in paras_list:
        if not re.search(r"\.\s*\.\s*\.(?:\*\*)?\s*$", p_text):
            return p_pasal
    return paras_list[0][1]


def chunk_with_legal_headers(text: str, chunk_size: int = 512, overlap: int = 100):
    enc = tiktoken.get_encoding("cl100k_base")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    curr_paras = []  # list of tuple: (p_text, p_pasal)
    curr_tokens = 0
    current_pasal = "Pembukaan"
    header_reserve = 12  # Cadangan token untuk header 'UU Nomor 45 Tahun 2009 | Pasal X\n\n'
    effective_limit = chunk_size - header_reserve

    for p in paragraphs:
        current_pasal = detect_article_label(p, current_pasal)
        p_tokens = len(enc.encode(p))

        if p_tokens > 420:
            sentences = re.split(r"(?<=[.;])\s+", p)
            for s in sentences:
                s_tok = len(enc.encode(s))
                if curr_tokens + s_tok > effective_limit and curr_paras:
                    start_pasal = get_chunk_pasal(curr_paras)
                    header = f"UU Nomor 45 Tahun 2009 | {start_pasal}\n\n"
                    raw_chunk = "\n\n".join([cp[0] for cp in curr_paras])
                    full_content = header + raw_chunk
                    chunks.append(
                        {
                            "chunk_id": f"chunk-{len(chunks)+1:04d}",
                            "tokens": len(enc.encode(full_content)),
                            "pasal_ref": start_pasal,
                            "content": full_content,
                        }
                    )
                    overlap_paras = []
                    overlap_toks = 0
                    for op_text, op_pasal in reversed(curr_paras):
                        ot = len(enc.encode(op_text))
                        if overlap_toks + ot <= overlap:
                            overlap_paras.insert(0, (op_text, op_pasal))
                            overlap_toks += ot
                        else:
                            break
                    curr_paras = list(overlap_paras)
                    curr_tokens = overlap_toks
                curr_paras.append((s, current_pasal))
                curr_tokens += s_tok
        else:
            if curr_tokens + p_tokens > effective_limit and curr_paras:
                start_pasal = get_chunk_pasal(curr_paras)
                header = f"UU Nomor 45 Tahun 2009 | {start_pasal}\n\n"
                raw_chunk = "\n\n".join([cp[0] for cp in curr_paras])
                full_content = header + raw_chunk
                chunks.append(
                    {
                        "chunk_id": f"chunk-{len(chunks)+1:04d}",
                        "tokens": len(enc.encode(full_content)),
                        "pasal_ref": start_pasal,
                        "content": full_content,
                    }
                )
                overlap_paras = []
                overlap_toks = 0
                for op_text, op_pasal in reversed(curr_paras):
                    ot = len(enc.encode(op_text))
                    if overlap_toks + ot <= overlap:
                        overlap_paras.insert(0, (op_text, op_pasal))
                        overlap_toks += ot
                    else:
                        break
                curr_paras = list(overlap_paras)
                curr_tokens = overlap_toks
            curr_paras.append((p, current_pasal))
            curr_tokens += p_tokens

    if curr_paras:
        start_pasal = get_chunk_pasal(curr_paras)
        header = f"UU Nomor 45 Tahun 2009 | {start_pasal}\n\n"
        raw_chunk = "\n\n".join([cp[0] for cp in curr_paras])
        full_content = header + raw_chunk
        chunks.append(
            {
                "chunk_id": f"chunk-{len(chunks)+1:04d}",
                "tokens": len(enc.encode(full_content)),
                "pasal_ref": start_pasal,
                "content": full_content,
            }
        )

    return chunks


def main():
    raw_text = ""
    if os.path.exists(DOC_PATH):
        print(f"Membaca naskah resmi MinerU v4: {DOC_PATH} ...")
        with open(DOC_PATH, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        # Fallback Plan 2: Rekonstruksi naskah utuh dari chunk pasal MinerU yang sudah ada
        fallback_json = BACKUP_144_PATH if os.path.exists(BACKUP_144_PATH) else OUT_MAIN_PATH
        if os.path.exists(fallback_json):
            print(f"[PLAN 2 FALLBACK] {DOC_PATH} belum tersedia. Membaca teks MinerU dari {fallback_json} ...")
            with open(fallback_json, "r", encoding="utf-8") as f:
                existing_items = json.load(f)
            paras = []
            for item in existing_items:
                txt = item.get("content") or item.get("text") if isinstance(item, dict) else str(item)
                # Hilangkan header lama jika ada di baris pertama agar tidak duplikat
                lines = txt.strip().splitlines()
                if lines and lines[0].startswith("UU Nomor 45 Tahun 2009 |"):
                    txt = "\n".join(lines[1:]).strip()
                if txt:
                    paras.append(txt)
            raw_text = "\n\n".join(paras)
        else:
            print(f"Error: Dokumen {DOC_PATH} maupun {OUT_MAIN_PATH} belum tersedia!")
            sys.exit(1)

    cleaned_text = clean_markdown_text(raw_text)
    chunks = chunk_with_legal_headers(cleaned_text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

    os.makedirs(os.path.dirname(OUT_MAIN_PATH), exist_ok=True)

    # Backup file chunks lama (144 chunks) jika belum pernah di-backup
    if os.path.exists(OUT_MAIN_PATH) and not os.path.exists(BACKUP_144_PATH):
        shutil.copy2(OUT_MAIN_PATH, BACKUP_144_PATH)
        print(f"File chunk pasal lama di-backup ke: {BACKUP_144_PATH}")

    # Simpan ke chunks_uu_45_2009_512.json DAN timpa langsung chunks_uu_45_2009.json
    with open(OUT_512_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    with open(OUT_MAIN_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    token_lens = [c["tokens"] for c in chunks]
    print("=" * 60)
    print(f"Statistik Chunking Boundary-Aware LightRAG ({CHUNK_SIZE} Token / {CHUNK_OVERLAP} Overlap):")
    print(f"Total Chunks           : {len(chunks)}")
    print(f"Rata-rata Token        : {sum(token_lens)/len(token_lens):.1f} token (Min: {min(token_lens)}, Max: {max(token_lens)})")
    print(f"File Utama (Ditimpakan): {OUT_MAIN_PATH}")
    print(f"File Salinan 512       : {OUT_512_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()

