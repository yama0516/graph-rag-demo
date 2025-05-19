#!/bin/bash
echo "Starting Graph RAG App..."

PY=$(command -v python3 || command -v python || echo "./venv/Scripts/python.exe")

"$PY" -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0
