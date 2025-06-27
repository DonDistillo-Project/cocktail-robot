#!/bin/bash

module add cuda/12.4
export LD_LIBRARY_PATH=.venv/lib64/python3.12/site-packages/nvidia/cublas/lib:.venv/lib64/python3.12/site-packages/nvidia/cudnn/lib
export TRITON_CACHE_DIR=/tmp/weymanno/triton
uv run python run_server.py 
