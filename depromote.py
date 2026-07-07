# -*- coding: utf-8 -*-
"""Разовая чистка сгенерированных статей от рекламы (под требования Дзена).
Удаляет абзацы/пункты с промо, телефон, e-mail и ссылки на коммерческий сайт."""
import os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "generated")
PUBART = os.path.join(HERE, "public", "articles")

# маркеры рекламных абзацев (регистронезависимо)
PROMO = re.compile(
    r"(наша команда|мы,?\s*как агентство|мы поможем|global wedding|сотрудничеств\w* с нами|"
    r"доверьте|свяжитесь|обратитесь к нам|наше агентство|мы организ|мы ведём переговоры|"
    r"телефон|8-?911-?127-?86-?53|theglobalwedding@mail\.ru)", re.I)

def strip_block(tag, html):
    # удалить <tag>...</tag>, если внутри есть промо-маркер
    def repl(m):
        return "" if PROMO.search(m.group(0)) else m.group(0)
    return re.sub(rf"<{tag}\b[^>]*>.*?</{tag}>", repl, html, flags=re.I | re.S)

def clean(html):
    # 1) снять ссылки на коммерческий сайт (оставить текст)
    html = re.sub(r'<a\b[^>]*theglobalwedding\.com[^>]*>(.*?)</a>', r'\1', html, flags=re.I | re.S)
    # 2) удалить рекламные <p> и <li>
    html = strip_block("p", html)
    html = strip_block("li", html)
    # 3) пустые списки после чистки
    html = re.sub(r'<ul>\s*</ul>', '', html, flags=re.I)
    # 4) остатки телефона/почты в тексте
    html = re.sub(r'8-?911-?127-?86-?53', '', html)
    html = re.sub(r'\s{2,}', ' ', html)
    return html.strip()

for f in glob.glob(os.path.join(GEN, "*.html")) + glob.glob(os.path.join(PUBART, "*.html")):
    src = open(f, encoding="utf-8").read()
    out = clean(src)
    plain_before = len(re.sub('<[^>]+>', '', src))
    plain_after = len(re.sub('<[^>]+>', '', out))
    gw = len(re.findall(r'(?i)global wedding', out))
    ph = len(re.findall(r'8-?911', out))
    open(f, "w", encoding="utf-8").write(out)
    print(f"{os.path.basename(f)}: {plain_before}→{plain_after} знаков | 'Global Wedding' осталось {gw} | телефон {ph}")
