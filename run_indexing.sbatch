#!/bin/bash
#SBATCH --job-name=lightrag_indexing
#SBATCH --account=student
#SBATCH --partition=a100-short
#SBATCH --qos=a100_1gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=117G
#SBATCH --output=indexing_lightrag_%j.log

# 1. Jalankan Ollama Service di Node Compute (Port 11500)
export OLLAMA_HOST=127.0.0.1:11500
ollama serve > /dev/null 2>&1 &
OLLAMA_PID=$!
sleep 10

# 2. Aktifkan Environment Conda
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lightrag_env

# 3. Eksekusi Script Indexing
python run_lightrag.py

# 4. Bersihkan Process Ollama
kill $OLLAMA_PID