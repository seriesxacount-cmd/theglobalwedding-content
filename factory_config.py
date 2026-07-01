# -*- coding: utf-8 -*-
"""Загрузка настроек проекта из config.json + ключа Gemini из окружения/.env."""
import os, json

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config.json"), encoding="utf-8"))

def gemini_key():
    k = os.environ.get("GEMINI_API_KEY", "")
    if not k and os.path.exists(os.path.join(HERE, ".env")):
        for line in open(os.path.join(HERE, ".env"), encoding="utf-8"):
            if line.strip().startswith("GEMINI_API_KEY"):
                k = line.split("=", 1)[1].strip()
    return k
