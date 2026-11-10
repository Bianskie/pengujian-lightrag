#!/bin/bash
#SBATCH --job-name=lightrag_indexing_v3
#SBATCH --account=student
#SBATCH --partition=a100-short
#SBATCH --qos=a100_1gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=100G
#SBATCH --output=indexing_lightrag_%j.log

# ==============================================================================
# SLURM Batch Script: Indexing Knowledge Graph LightRAG (Gemma 4:12B + BGE-M3)
#
# Author      : Pabian
# Version     : 3.2.0
# Revised     : 10-11-2026
# Description : Pipeline indexing LightRAG V3 (Prompt Legal-Relation V1.3,
#               Direct HTTP "think": False, Pure Synchronized Storage 100%).
#               Menghubungkan GPU DGX A100 ke server Ollama bersama di port 11435
#               (mahoni01:11435) dengan proteksi Anti-OOM (CONCURRENCY=1,
#               NUM_CTX=4096, NUM_PREDICT=2500).
# ==============================================================================

# 0. Pindah ke Direktori Submit SLURM (Dinamis untuk Antigravity / Workspace Aktif)
cd "${SLURM_SUBMIT_DIR:-$(pwd)}"

# 1. Muat ~/.bashrc & Aktifkan Environment Conda
[ -f "$HOME/.bashrc" ] && source "$HOME/.bashrc"
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lightrag_env

# 2. Konfigurasi Folder Hasil & Parameter Ekstraksi Selaras V3.2.0
export WORKING_DIR="${WORKING_DIR:-../hasil/storage_gemma4_uu45_lightrag}"
export CONCURRENCY=1
export NUM_CTX=4096
export NUM_PREDICT=2500

# 3. Hubungkan ke Ollama Server Bersama di Port 11435 (mahoni01:11435)
if ! curl -s "http://127.0.0.1:11435/api/tags" >/dev/null 2>&1; then
    echo "[INFO] Membuka jembatan SSH Client ke Ollama bersama di mahoni01:11435..."
    ssh -f -N -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -L 11435:127.0.0.1:11435 mahoni01
    sleep 3
fi

export OLLAMA_HOST="http://127.0.0.1:11435"

echo "[VERIFIKASI] Mengecek koneksi ke Ollama bersama ($OLLAMA_HOST):"
if curl -s "$OLLAMA_HOST/api/tags" | grep -q "gemma4"; then
    echo "[SUKSES] Terhubung ke Ollama bersama! Model gemma4:12b & bge-m3 siap."
else
    echo "[ERROR] Belum dapat menjangkau port 11435 di mahoni01!"
    exit 1
fi

# 4. Eksekusi Script Indexing LightRAG V3
python run_lightrag.py