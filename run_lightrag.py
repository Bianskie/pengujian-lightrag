"""
Service Engine Indexing LightRAG Berbahasa Indonesia (Gemma 4:12B + BGE-M3)

Author      : Pabian
Version     : 2.4.0
Created     : 02-11-2026
Revised     : 10-11-2026
Description : Service Engine LightRAG Independen menggunakan Built-in Storage
              (NetworkX .graphml, NanoVectorDB, dan JsonKVStorage) di
              ../hasil/storage_gemma4_uu45_lightrag/.
              Mengintegrasikan Prompt Indexing Yuridis Bahasa Indonesia (prompt_lightrag_id_v1),
              chunk_token_size=512 & chunk_overlap_token_size=100, proteksi Anti-OOM untuk
              server Ollama bersama (CONCURRENCY=1, num_ctx=4096, num_predict=2048, auto-retry
              terhadap HTTP 500 / unexpected EOF), pelabelan file_paths MinerU, serta
              deduplikasi graf kanonik pasca-indexing (normalisasi_entitas.py).
"""
import os
import sys
import json
import asyncio
import numpy as np
import networkx as nx
from lightrag import LightRAG
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc

# Pastikan modul lokal di folder proses/ dapat diimpor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompt_lightrag_id_v1 import apply_prompts, ENTITY_TYPES
from normalisasi_entitas import dedup_graph, report

WORKING_DIR = os.getenv("WORKING_DIR", "../hasil/storage_gemma4_uu45_lightrag")
DATA_PATH = os.getenv("DATA_PATH", "../data/chunks_uu_45_2009.json")
CONCURRENCY = int(os.getenv("CONCURRENCY", "1"))
NUM_CTX = int(os.getenv("NUM_CTX", "4096"))
NUM_PREDICT = int(os.getenv("NUM_PREDICT", "2048"))

os.makedirs(WORKING_DIR, exist_ok=True)


async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    host = kwargs.pop("host", None) or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11435")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"

    last_err = None
    for attempt in range(1, 6):
        try:
            return await ollama_model_complete(
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                keyword_extraction=keyword_extraction,
                host=host,
                options={
                    "temperature": 0.0,
                    "num_ctx": NUM_CTX,
                    "num_predict": NUM_PREDICT,
                    "top_p": 0.9,
                },
                **kwargs,
            )
        except Exception as e:
            last_err = e
            wait_s = attempt * 5
            print(f"[RETRY LLM {attempt}/5] Menunggu {wait_s}s setelah error Ollama: {e}", flush=True)
            await asyncio.sleep(wait_s)
    raise last_err


async def embedding_func(texts: list[str]) -> np.ndarray:
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11435")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"

    last_err = None
    for attempt in range(1, 6):
        try:
            return await ollama_embed(
                texts,
                embed_model="bge-m3:latest",
                host=host,
            )
        except Exception as e:
            last_err = e
            wait_s = attempt * 5
            print(f"[RETRY EMBED {attempt}/5] Menunggu {wait_s}s setelah error Ollama: {e}", flush=True)
            await asyncio.sleep(wait_s)
    raise last_err


async def main():
    # 1. Pasang Prompt Bahasa Indonesia V1.1 ke dalam lightrag.prompt.PROMPTS
    addon_params = apply_prompts({"entity_types": ENTITY_TYPES})

    # 2. Inisialisasi Engine LightRAG (512 Token Chunking & 100 Token Overlap)
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="gemma4:12b",
        chunk_token_size=512,
        chunk_overlap_token_size=100,
        llm_model_max_async=CONCURRENCY,
        embedding_func_max_async=1,
        embedding_batch_num=16,
        llm_model_func=llm_model_func,
        addon_params=addon_params,
        embedding_func=EmbeddingFunc(
            embedding_dim=1024,
            max_token_size=8192,
            func=embedding_func,
        ),
    )

    await rag.initialize_storages()

    # 3. Resolusi Path Berkas Chunks (mendukung ../data/ maupun data/)
    candidate_paths = [
        DATA_PATH,
        "../data/chunks_uu_45_2009_512.json",
        "../data/chunks_uu_45_2009.json",
        "data/chunks_uu_45_2009_512.json",
        "data/chunks_uu_45_2009.json",
    ]
    resolved_data_path = next((p for p in candidate_paths if os.path.exists(p)), None)
    if not resolved_data_path:
        raise FileNotFoundError(f"Berkas input chunk tidak ditemukan pada kandidat: {candidate_paths}")

    with open(resolved_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    contents = [
        item.get("content") or item.get("text") if isinstance(item, dict) else str(item)
        for item in data
    ]
    file_paths = [
        f"UU_45_2009_MinerU.md#{item.get('chunk_id', f'chunk-{idx+1:04d}')} ({item.get('pasal_ref', 'Pasal')})"
        if isinstance(item, dict)
        else f"UU_45_2009_MinerU.md#chunk-{idx+1:04d}"
        for idx, item in enumerate(data)
    ]

    print("=" * 70)
    print("MEMULAI INDEXING LIGHTRAG (GEMMA 4:12B + BGE-M3 | PROMPT ID V1.1)")
    print(f"Working Dir   : {WORKING_DIR}")
    print(f"Input Data    : {resolved_data_path} ({len(contents)} Chunks)")
    print(f"Concurrency   : {CONCURRENCY} async workers | Max Predict: {NUM_PREDICT} tokens")
    print("=" * 70, flush=True)

    await rag.ainsert(contents, file_paths=file_paths)

    # 4. Normalisasi & Deduplikasi Graf Pasca-Indexing (normalisasi_entitas.py)
    graphml_file = os.path.join(WORKING_DIR, "graph_chunk_entity_relation.graphml")
    if os.path.exists(graphml_file):
        print("\nMenjalankan Normalisasi & Deduplikasi Graf Kanonik...", flush=True)
        G = nx.read_graphml(graphml_file)
        report(G, "Sebelum Dedup")
        H, info = dedup_graph(G)
        merged = len(info["mapping"]) - H.number_of_nodes()
        print(f"Hasil Dedup: Dibuang (sampah)={len(info['dropped_junk'])} | Node digabung={merged}")
        report(H, "Sesudah Dedup")
        nx.write_graphml(H, graphml_file)

    print("==================================================")
    print("INDEXING LIGHTRAG SELESAI SUKSES!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())

