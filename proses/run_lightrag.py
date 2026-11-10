"""
Service Engine Indexing LightRAG Berbahasa Indonesia (Gemma 4:12B + BGE-M3)

Author      : Pabian
Version     : 3.2.0
Created     : 02-11-2026
Revised     : 10-11-2026
Description : Service Engine LightRAG Independen menggunakan Built-in Storage
              (NetworkX .graphml, NanoVectorDB, dan JsonKVStorage) di working directory.
              - Direct HTTP Request ke Ollama (/api/chat) dengan payload '"think": False'
                untuk bypass token reasoning engine secara native.
              - Eliminasi total normalisasi_entitas.dedup_graph() pasca-indexing guna
                mencegah casing mismatch dan desinkronisasi GraphML vs VectorDB (100% Match).
              - Konfigurasi batas token stabil: NUM_CTX=4096, NUM_PREDICT=2500, CONCURRENCY=1.
              - Mekanisme exponential backoff retry (1-5x) atas respon HTTP 500 / overload.
"""
import os
import sys
import json
import asyncio
import httpx
import numpy as np
from lightrag import LightRAG
from lightrag.llm.ollama import ollama_embed
from lightrag.utils import EmbeddingFunc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompt_lightrag_id_v1 import apply_prompts, ENTITY_TYPES

WORKING_DIR = os.getenv("WORKING_DIR", "../hasil/storage_gemma4_uu45_lightrag")
DATA_PATH = os.getenv("DATA_PATH", "../data/chunks_uu_45_2009.json")
CONCURRENCY = int(os.getenv("CONCURRENCY", "1"))
NUM_CTX = int(os.getenv("NUM_CTX", "4096"))
NUM_PREDICT = int(os.getenv("NUM_PREDICT", "2500"))

os.makedirs(WORKING_DIR, exist_ok=True)

async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11435")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if prompt:
        messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "gemma4:12b",
        "think": False,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT,
            "top_p": 0.9,
        },
        "messages": messages,
    }

    async with httpx.AsyncClient(timeout=240.0) as client:
        last_err = None
        for attempt in range(1, 6):
            try:
                resp = await client.post(f"{host}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "")
            except Exception as e:
                last_err = e
                wait_s = attempt * 5
                print(f"[RETRY LLM {attempt}/5] Menunggu {wait_s}s setelah error: {e}", flush=True)
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
    addon_params = apply_prompts({"entity_types": ENTITY_TYPES})

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="gemma4:12b",
        chunk_token_size=512,
        chunk_overlap_token_size=100,
        llm_model_max_async=CONCURRENCY,
        embedding_func_max_async=1,
        embedding_batch_num=16,
        entity_extract_max_gleaning=0,
        llm_model_func=llm_model_func,
        addon_params=addon_params,
        embedding_func=EmbeddingFunc(
            embedding_dim=1024,
            max_token_size=4096,
            func=embedding_func,
        ),
    )

    await rag.initialize_storages()

    candidate_paths = [
        DATA_PATH,
        "../data/chunks_uu_45_2009.json",
        "../data/chunks_uu_45_2009_512.json",
        "data/chunks_uu_45_2009.json",
    ]
    resolved_data_path = next((p for p in candidate_paths if os.path.exists(p)), None)
    if not resolved_data_path:
        raise FileNotFoundError(f"Berkas input chunk tidak ditemukan pada: {candidate_paths}")

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

    print("MEMULAI INDEXING LIGHTRAG (PURE SYNC | NO MANUAL DEDUP CORRUPTION)")
    print(f"Working Dir   : {WORKING_DIR}")
    print(f"Input Data    : {resolved_data_path} ({len(contents)} Chunks)")
    print(f"Context Window: {NUM_CTX} | Max Predict: {NUM_PREDICT}")

    await rag.ainsert(contents, file_paths=file_paths)
    print("INDEXING LIGHTRAG SELESAI SUKSES 100%!")

if __name__ == "__main__":
    asyncio.run(main())