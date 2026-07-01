# -*- coding: utf-8 -*-
"""Сборка Дзен-совместимого RSS: авто-статьи фабрики (+ опционально статьи блога Tilda).
Настройки — config.json. Запуск: python gen_feed.py public/feed.xml"""
import re, os, sys, time, html, json, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from factory_config import CFG, HERE

OUT = sys.argv[1] if len(sys.argv) > 1 else "feed.xml"
SITE = CFG["site_url"].rstrip("/")
TILDA_RSS = CFG.get("tilda_rss", "").strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
MIN_LEN = 300
GENDIR = os.path.join(HERE, "generated")

def fetch(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ru"})
            return urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 503) and i < tries-1:
                time.sleep(3*(i+1)); continue
            raise

def article_html(h):
    m = re.search(r'<div[^>]*itemprop="articleBody"[^>]*>', h, re.I)
    if not m: return None
    start = m.end(); depth = 1
    for t in re.finditer(r'<(/?)div\b[^>]*>', h[start:], re.I):
        depth += 1 if t.group(1) == "" else -1
        if depth == 0:
            return h[start:start+t.start()]
    return None

def clean(frag):
    frag = re.sub(r'<(script|style|svg|noscript)\b.*?</\1>', ' ', frag, flags=re.S | re.I)
    frag = re.sub(r'<img[^>]*?\bdata-original="([^"]+)"[^>]*?>', r'<img src="\1" />', frag, flags=re.I)
    def sa(mt):
        tag = mt.group(1); attrs = mt.group(2) or ""
        if tag.lower() == "a":
            hm = re.search(r'\bhref="([^"]*)"', attrs); return f'<a href="{hm.group(1)}">' if hm else "<a>"
        if tag.lower() == "img":
            sm = re.search(r'\bsrc="([^"]*)"', attrs); return f'<img src="{sm.group(1)}" />' if sm else ""
        return f"<{tag}>"
    frag = re.sub(r'<([a-zA-Z0-9]+)((?:\s[^>]*)?)\s*/?>', sa, frag)
    return re.sub(r'[ \t]+', ' ', frag).strip()

def esc(s): return html.escape(s or "", quote=True)

items = []

# 1) опционально: статьи блога Tilda
if TILDA_RSS:
    try:
        rss = fetch(TILDA_RSS)
        for it in ET.fromstring(rss.encode()).find("channel").findall("item"):
            link = (it.findtext("link") or "").strip()
            try:
                h = fetch(link)
            except Exception:
                continue
            raw = article_html(h); ce = clean(raw) if raw else ""
            if len(re.sub('<[^>]+>', '', ce)) < MIN_LEN:
                continue
            img = re.search(r'<meta property="og:image" content="([^"]+)"', h)
            items.append({"title": (it.findtext("title") or "").strip(), "link": link,
                          "pub": (it.findtext("pubDate") or "").strip(),
                          "desc": (it.findtext("description") or "").strip(),
                          "img": img.group(1) if img else "", "ce": ce})
            time.sleep(1.0)
        print(f"Статей из Tilda: {len(items)}", flush=True)
    except Exception as e:
        print("Tilda RSS пропущен:", e)

# 2) авто-статьи фабрики
gidx = os.path.join(GENDIR, "index.json")
if os.path.exists(gidx):
    added = 0
    for g in json.load(open(gidx, encoding="utf-8")):
        bp = os.path.join(GENDIR, g["slug"] + ".html")
        if not os.path.exists(bp): continue
        body = open(bp, encoding="utf-8").read()
        desc = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', body)).strip()[:180]
        items.append({"title": g["title"], "link": f"{SITE}/articles/{g['slug']}.html",
                      "pub": g.get("date", ""), "desc": desc or g["title"],
                      "img": f"{SITE}/{g['cover']}", "ce": body})
        added += 1
    print(f"Авто-статей: {added}", flush=True)

# сборка XML
parts = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">',
         '<channel>', f'<title>{esc(CFG["feed_title"])}</title>',
         f'<link>{esc(CFG["home_url"])}</link>', f'<description>{esc(CFG["feed_desc"])}</description>',
         '<language>ru</language>']
for a in items:
    parts += ["<item>", f"<title>{esc(a['title'])}</title>", f"<link>{esc(a['link'])}</link>",
              f'<guid isPermaLink="true">{esc(a["link"])}</guid>']
    if a["pub"]: parts.append(f"<pubDate>{esc(a['pub'])}</pubDate>")
    parts.append(f"<description>{esc(a['desc'])}</description>")
    if a["img"]:
        mt = "image/png" if a["img"].lower().endswith(".png") else "image/jpeg"
        parts.append(f'<enclosure url="{esc(a["img"])}" type="{mt}" />')
    ce = a["ce"].replace("]]>", "]]]]><![CDATA[>")
    parts += [f"<content:encoded><![CDATA[{ce}]]></content:encoded>", "</item>"]
parts.append("</channel></rss>")
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(parts))
print(f"Готово: {OUT} | статей: {len(items)}")
