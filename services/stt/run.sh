#!/bin/bash

module add cuda
export LD_LIBRARY_PATH=.venv/lib64/python3.12/site-packages/nvidia/cublas/lib:.venv/lib64/python3.12/site-packages/nvidia/cudnn/lib:ffmpeg5.1.6/lib:ffmpeg6.1.2/lib
uv run python run_server.py 