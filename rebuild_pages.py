# -*- coding: utf-8 -*-
"""Перерендерить все страницы public/articles из generated/ с текущим шаблоном PAGE.
Нужно после правки подвала (контакты убраны). Gemini-ключ не требуется."""
import os, re, html, json, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import run_factory as rf
from factory_config import CFG, HERE

PUBLIC = os.path.join(HERE, "public")
GEN = os.path.join(HERE, "generated")
idx = json.load(open(os.path.join(GEN, "index.json"), encoding="utf-8"))

n = 0
for e in idx:
    slug, title = e["slug"], e["title"]
    bp = os.path.join(GEN, slug + ".html")
    if not os.path.exists(bp):
        print("нет тела:", slug); continue
    body = open(bp, encoding="utf-8").read()
    desc = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', body)).strip()[:160]
    page = (rf.PAGE.replace("__TITLE__", html.escape(title))
                .replace("__DESC__", html.escape(desc)).replace("__SLUG__", slug)
                .replace("__BODY__", body).replace("__BRAND__", html.escape(CFG["brand_display"]))
                .replace("__BRANDLINE__", html.escape(CFG.get("brand_line", "")))
                .replace("__COMPANY__", html.escape(CFG["company"])))
    open(os.path.join(PUBLIC, "articles", slug + ".html"), "w", encoding="utf-8").write(page)
    n += 1
    print("ok:", slug)
print(f"\nПеререндерено страниц: {n}")
