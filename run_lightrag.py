import os
import json
import asyncio
import numpy as np
from lightrag import LightRAG
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc

WORKING_DIR = "../hasil_indexing/storage_gemma4_uu45_lightrag"
DATA_PATH = "data/chunks_uu_45_2009.json"

if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    # Bypass thinking process agar LLM langsung mengekstrak entitas/relasi
    thinking_bypass_prefix = "RESPOND DIRECTLY WITH THE REQUIRED EXTRACTED ENTITIES AND RELATIONS. DO NOT THINK STEP-BY-STEP. DO NOT INCLUDE PREAMBLE OR REASONING PROCESS.\n\n"
    final_prompt = thinking_bypass_prefix + prompt

    return await ollama_model_complete(
        final_prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        keyword_extraction=keyword_extraction,
        host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11500"),
        options={
            "temperature": 0.0,
            "num_ctx": 4096,
            "top_p": 0.9,
        },
        **kwargs
    )

async def embedding_func(texts: list[str]) -> np.ndarray:
    return await ollama_embed(
        texts,
        embed_model="bge-m3:latest",
        host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11500")
    )

async def main():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="gemma4:12b",
        llm_model_max_async=10,       # 10 chunk berjalan bersamaan di GPU A100
        embedding_func_max_async=4,
        embedding_batch_num=32,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=1024,
            max_token_size=8192,
            func=embedding_func
        )
    )

    await rag.initialize_storages()

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Tetap memproses seluruh 144 chunks utuh
    contents = [
        item.get("content") or item.get("text") if isinstance(item, dict) else str(item)
        for item in data
    ]

    print(f"=== Memulai Indexing Low-Latency (Total {len(contents)} Chunks Utuh) ===")
    await rag.ainsert(contents)
    print("==================================================")
    print("INDEXING LIGHTRAG SELESAI SUKSES!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())