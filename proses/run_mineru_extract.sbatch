#!/bin/bash
#SBATCH --job-name=mineru_extract_uu45
#SBATCH --account=student
#SBATCH --partition=a100-short
#SBATCH --qos=a100_1gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --output=mineru_extract_%j.log

# ==============================================================================
# SLURM Batch Script: Ekstraksi Dokumen MinerU v4 & Boundary-Aware Rechunking
#
# Author      : Pabian
# Version     : 1.2.0
# Created     : 02-11-2026
# Revised     : 09-11-2026
# Description : Menjalankan ekstraksi PDF UU Nomor 45 Tahun 2009 menggunakan
#               MinerU v4 pada GPU NVIDIA A100 untuk menghasilkan content_list.json,
#               output.md, serta rechunking semantik 512 token + 100 overlap
#               ber-header kanonik yang langsung menimpa data/chunks_uu_45_2009.json.
# ==============================================================================

set -e

# 1. Pindah ke Direktori Submit SLURM (Anti-Error /var/spool/slurmd)
cd "${SLURM_SUBMIT_DIR:-$HOME/task/lightrag_testing/proses}"

# 2. Aktifkan Environment Conda
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate lightrag_env || conda activate minirag

echo "=== [1/2] Menjalankan Ekstraksi MinerU v4 & Chunker Pasal ==="
python extract_mineru_hpc.py --pdf "../data/UU Nomor 45 Tahun 2009 (1).pdf" --device cuda

echo "=== [2/2] Menjalankan Re-Chunking Boundary-Aware (512 Token / 100 Overlap) ==="
python rechunk_512.py

echo "=================================================="
echo "EKSTRAKSI MINERU & RECHUNKING SELESAI SUKSES!"
echo "=================================================="

