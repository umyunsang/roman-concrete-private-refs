# 분석 마크다운을 그림이 들어간 HTML로 바꾼다(브라우저에서 바로 확인용). 같은 폴더에 .html로 저장.
import sys, pathlib, markdown
src = pathlib.Path(sys.argv[1]); out = src.with_suffix(".html")
body = markdown.markdown(src.read_text(encoding="utf-8"), extensions=["tables", "fenced_code", "sane_lists", "toc"])
css = """
:root{--bg:#faf7f0;--fg:#222;--muted:#666;--line:#ddd3bf;--accent:#9c3b1f}
@media (prefers-color-scheme:dark){:root{--bg:#1d1b18;--fg:#eee;--muted:#aaa;--line:#4a443a;--accent:#f0a07a}}
body{background:var(--bg);color:var(--fg);font-family:"Apple SD Gothic Neo","Pretendard","Noto Sans KR",sans-serif;line-height:1.65;margin:0;padding:24px 16px}
main{max-width:1100px;margin:0 auto}
h1{font-size:1.8em;border-bottom:3px solid var(--accent);padding-bottom:.3em}
h2{margin-top:2.2em;border-bottom:1px solid var(--line);padding-bottom:.2em}
h3{margin-top:1.6em;color:var(--accent)}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:.92em;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:6px 9px;vertical-align:top}
th{background:rgba(156,59,31,.08)}
img{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px;margin:.6em 0;cursor:zoom-in}
code{background:rgba(127,127,127,.15);padding:1px 5px;border-radius:4px;font-size:.9em}
blockquote{border-left:4px solid var(--accent);margin:1em 0;padding:.2em 1em;color:var(--muted)}
.stamp{color:var(--muted);font-size:.85em}
"""
js = "document.querySelectorAll('img').forEach(i=>i.onclick=()=>window.open(i.src,'_blank'));"
from datetime import datetime
html = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>203X 벤치마크 정밀분석</title><style>{css}</style></head><body><main>
<p class="stamp">생성 시각 {datetime.now():%Y-%m-%d %H:%M} · 원본: {src.name} · 그림을 누르면 원본 크기로 열립니다</p>
{body}</main><script>{js}</script></body></html>"""
out.write_text(html, encoding="utf-8")
print(f"HTML 생성: {out}")
