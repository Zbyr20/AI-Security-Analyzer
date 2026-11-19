"""Yapay zekâ modeli ayarları.

Varsayılanlar yerel Foundry Local kurulumuna göredir. Kodu değiştirmeden
farklı bir model/sunucu kullanmak için ortam değişkenlerini ayarlayın:

    PowerShell:  $env:AI_MODEL = "qwen3-8b"
    Bash:        export AI_MODEL=qwen3-8b

Desteklenen değişkenler: AI_BASE_URL, AI_MODEL, AI_API_KEY
"""
import os

FOUNDRY_BASE_URL = os.getenv("AI_BASE_URL", "http://127.0.0.1:56661/v1")

MODEL_NAME = os.getenv("AI_MODEL", "qwen3-4b-cuda-gpu")

API_KEY = os.getenv("AI_API_KEY", "local")
