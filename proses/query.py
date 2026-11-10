"""
Service Engine Query & Inference LightRAG Berbahasa Indonesia (Gemma 4:12B + BGE-M3)

Author      : Pabian
Version     : 1.0.0
Created     : 10-11-2026
Description : Modul query terkalibrasi untuk inferensi Knowledge Graph regulasi hukum.
              - Mode 'mix' seimbang: menelusuri relasi topologis graf dan dense vector chunks.
              - Mengatasi 'hub-node crowding' dengan membatasi entitas graf (top_k=6)
                dan memperlebar jaring tangkapan pasal terbelah (chunk_top_k=25).
              - Pembatasan alokasi token resmi QueryParam: max_entity_tokens=1500,
                max_relation_tokens=1500, max_total_tokens=7000.
              - Jendela konteks inferensi penuh NUM_CTX=8192 dengan direct HTTP think=False.
              - Fleksibel: dapat menerima pertanyaan langsung dari argumen CLI (sys.argv)
                atau diimpor sebagai fungsi `ask_lightrag(query)`.
"""
import os
import sys
import asyncio
import httpx
import numpy as np
from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_embed
from lightrag.utils import EmbeddingFunc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompt_lightrag_id_v1 import apply_prompts, ENTITY_TYPES

WORKING_DIR = os.getenv("WORKING_DIR", "../hasil/storage_gemma4_uu45_lightrag")
NUM_CTX = int(os.getenv("NUM_CTX", "8192"))
NUM_PREDICT = int(os.getenv("NUM_PREDICT", "1500"))

# Profil parameter penelusuran hukum terkalibrasi
DEFAULT_LEGAL_QUERY_PARAM = QueryParam(
    mode="mix",
    top_k=6,                   # Batas simpul graf agar tidak membanjiri prompt
    chunk_top_k=25,            # Mengangkut seluruh belahan pasal (misal ayat 1 & ayat 2)
    max_entity_tokens=1500,    # Alokasi token untuk kamus entitas
    max_relation_tokens=1500,  # Alokasi token untuk relasi graf
    max_total_tokens=7000,     # Plafon total token di dalam batas konteks 8192
    enable_rerank=False
)

async def llm_model_func(prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs) -> str:
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
            "num_predict": NUM_PREDICT
        },
        "messages": messages,
    }

    async with httpx.AsyncClient(timeout=240.0) as client:
        last_err = None
        for attempt in range(1, 6):
            try:
                resp = await client.post(f"{host}/api/chat", json=payload)
                resp.raise_for_status()
                return resp.json().get("message", {}).get("content", "")
            except Exception as e:
                last_err = e
                wait_s = attempt * 5
                print(f"[RETRY LLM {attempt}/5] Ollama sibuk (HTTP Error/Timeout), menunggu {wait_s}s: {e}", flush=True)
                await asyncio.sleep(wait_s)
        raise last_err

async def embedding_func(texts: list[str]) -> np.ndarray:
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11435")
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"
    return await ollama_embed(texts, embed_model="bge-m3:latest", host=host)

def get_rag_instance():
    return LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="gemma4:12b",
        llm_model_max_async=1,
        llm_model_func=llm_model_func,
        addon_params=apply_prompts({"entity_types": ENTITY_TYPES}),
        embedding_func=EmbeddingFunc(embedding_dim=1024, max_token_size=4096, func=embedding_func),
    )

async def ask_lightrag(pertanyaan: str, param: QueryParam = DEFAULT_LEGAL_QUERY_PARAM) -> str:
    rag = get_rag_instance()
    await rag.initialize_storages()
    return await rag.aquery(pertanyaan, param=param)

async def main():
    if len(sys.argv) > 1:
        pertanyaan = " ".join(sys.argv[1:])
    else:
        pertanyaan = "Apa sanksi pidana bagi kapal penangkap ikan berbendera asing yang menangkap ikan di ZEEI tanpa SIPI?"

    print("\n" + "="*60)
    print(f"[PERTANYAAN]\n{pertanyaan}")
    print("="*60)

    rag = get_rag_instance()
    await rag.initialize_storages()
    response = await rag.aquery(pertanyaan, param=DEFAULT_LEGAL_QUERY_PARAM)

    print("\n[JAWABAN LIGHTRAG - MODE MIX]")
    print(response)
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())