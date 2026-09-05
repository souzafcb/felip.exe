from __future__ import annotations

import html
import re
import unicodedata
from pathlib import Path

from build_fez_documents import (
    SOURCE_MANIFESTO,
    TRACKS,
    YORUBA_TRACK,
    extract_lines,
    extract_track_lines,
    structured_items,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "index.html"

SPOTIFY_LINKS = {
    "TEMPODER": "https://open.spotify.com/track/4GH4AsHD69cgAspFGdLRHl",
    "BOA TARDE MAJESTADE": "https://open.spotify.com/track/6I0ke8FjcWYpF5LAB63ycC",
    "A COBRAR": "https://open.spotify.com/track/0TkAI6aGaVezJUkEjmUSqB",
    "MOSTRE": "https://open.spotify.com/track/0H74XqtEoWQcbfg8LVYj1S",
    "POR UM TRIZ": "https://open.spotify.com/track/4gXPzK6iIZ5zfeyZA0b8S0",
}


def slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")


def track_source(title: str, start: int, end: int):
    if title != "YÔ / IO / RUA / IORUBÁ":
        return extract_track_lines(title, start, end)
    prepared = []
    gap = False
    for raw in YORUBA_TRACK.splitlines():
        if raw.strip():
            prepared.append((raw.strip(), gap))
            gap = False
        else:
            gap = True
    return prepared


def editorial_text(value: str) -> str:
    """Remove artefacts from PDF text positioning without rewriting the content."""
    value = re.sub(r"\s+([,.;:!?])", r"\1", value)
    value = re.sub(r"\(\s+", "(", value)
    value = re.sub(r"\s+\)", ")", value)
    return value


CODE_FIXES = {
    "classCampoRelacional:\ndef__init__(self, dimensoes=512):\nself.vetores = EmbeddingSpace(dimensoes)\nself.relacoes =# infinitas": (
        "class CampoRelacional:\n"
        "    def __init__(self, dimensoes=512):\n"
        "        self.vetores = EmbeddingSpace(dimensoes)\n"
        "        self.relacoes = # infinitas"
    ),
    "defatravessar(self, intencao):": "    def atravessar(self, intencao):",
    "returnself.vetores.navegar(intencao)\n# nada se impõe / tudo precisa ser convencido": (
        "        return self.vetores.navegar(intencao)\n"
        "        # nada se impõe / tudo precisa ser convencido"
    ),
    "aminoacidos =[\"conceito\", \"afeto\", \"timbre\", \"ritmo\"]": (
        "aminoacidos = [\"conceito\", \"afeto\", \"timbre\", \"ritmo\"]"
    ),
    "versoes = [gerar()for_inrange(20)]# iteração": (
        "versoes = [gerar() for _ in range(20)]  # iteração"
    ),
    "stems = processar(Moises, stems)# separação": (
        "stems = processar(Moises, stems)  # separação"
    ),
}


def clean_code(value: str) -> str:
    fixed = value
    for source, replacement in CODE_FIXES.items():
        fixed = fixed.replace(source, replacement)
    return fixed


def render_tracks():
    nav = []
    cards = []
    for number, (title, start, end) in enumerate(TRACKS, 1):
        ident = slug(title)
        spotify_url = SPOTIFY_LINKS.get(title)
        available = '<em aria-label="Disponível no Spotify">↗</em>' if spotify_url else ""
        nav.append(
            f'<a class="track-link" href="#{ident}" data-track-link="{html.escape(title.casefold())}">'
            f'<span>{number:02d}</span><strong>{html.escape(title)} {available}</strong></a>'
        )
        lines = []
        for text, before_gap in track_source(title, start, end):
            safe = html.escape(text)
            gap_class = " gap" if before_gap else ""
            if text.startswith("[") and text.endswith("]"):
                lines.append(f'<div class="stage{gap_class}">{safe}</div>')
            else:
                lines.append(f'<div class="verse-line{gap_class}">{safe}</div>')
        listen = ""
        if spotify_url:
            listen = (
                f'<a class="listen" href="{spotify_url}" target="_blank" rel="noopener noreferrer" '
                f'aria-label="Ouvir {html.escape(title)} no Spotify; abre em uma nova aba">'
                '<span aria-hidden="true">▶</span> Ouvir no Spotify <b aria-hidden="true">↗</b></a>'
            )
        cards.append(f"""
        <article class="track" id="{ident}" data-track="{html.escape(title.casefold())}">
          <header class="track-head">
            <div class="track-index">TRACK_{number:02d} / FEZ</div>
            <h3>{html.escape(title)}</h3>
            <div class="command">&gt; abrir_arquivo --faixa {number:02d} --id {ident.replace('-', '_')}</div>
            {listen}
          </header>
          <div class="lyrics">{''.join(lines)}</div>
        </article>""")
    return "".join(nav), "".join(cards)


def render_manifesto():
    pages = extract_lines(SOURCE_MANIFESTO, list(range(6, 15)))
    skip = {
        "CRIAR NO CALDO DO MUNDO",
        'def ensaio_filosófico(): return "arte + tecnologia + dissolução_do_eu"',
        "Felipe Brito (FEZ)",
        "AlquimiXGriot · RAPP RAPP",
        "Rhythm-Al-Prompt & Poetry · 2025",
    }
    rendered = []
    section_count = 0
    for item in structured_items(pages, skip):
        kind, text = item["kind"], item["text"]
        text = clean_code(text) if kind == "code" else editorial_text(text)
        safe = html.escape(text)
        if kind == "heading":
            clean = text.replace("◈", "").strip()
            if not re.search(r"[A-Za-zÀ-ÿ0-9]", clean):
                continue
            section_count += 1
            rendered.append(
                f'<h3 id="manifesto-{section_count:02d}">{html.escape(clean)}</h3>'
                f'<div class="section-slug">// {slug(clean).replace("-", "_")}</div>'
            )
        elif kind == "code":
            rendered.append(f'<pre><code>{safe}</code></pre>')
        elif kind == "quote":
            rendered.append(f'<blockquote>{safe.replace(chr(10), "<br>")}</blockquote>')
        elif kind == "bold":
            rendered.append(f'<p class="manifesto-emphasis">{safe}</p>')
        else:
            rendered.append(f'<p>{safe}</p>')
    return "".join(rendered)


track_nav, track_cards = render_tracks()
manifesto = render_manifesto()

document = f'''<!doctype html>
<html lang="pt-BR" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="FEZ — rap, poesia, ancestralidade e tecnologia. Manifesto Criar no Caldo do Mundo e caderno de letras.">
  <meta name="theme-color" content="#11110f">
  <meta property="og:title" content="FEZ — Manifesto e Letras">
  <meta property="og:description" content="Criar no Caldo do Mundo. Um arquivo vivo de palavra, ritmo, ancestralidade e tecnologia.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://fez.etc.br/">
  <meta property="og:image" content="https://fez.etc.br/assets/images/FEZ_thumbnail_social.png">
  <meta property="og:image:alt" content="FEZ_ — Manifesto e Letras">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="assets/images/FEZ_favicon.svg" type="image/svg+xml">
  <title>FEZ — Manifesto e Letras</title>
  <style>
    :root {{
      --paper:#f2f0ea; --paper-2:#e8e5dd; --ink:#11110f; --muted:#686761;
      --line:rgba(17,17,15,.18); --line-strong:rgba(17,17,15,.72); --panel:#faf9f5;
      --accent:#7c3529; --mono:"Cascadia Mono","IBM Plex Mono",Consolas,monospace;
      --serif:"Noto Serif",Georgia,"Times New Roman",serif; --sans:"Noto Sans",Arial,sans-serif;
      --content:1180px; --ease:cubic-bezier(.2,.7,.2,1);
    }}
    html[data-theme="dark"] {{
      --paper:#11110f; --paper-2:#1b1b18; --ink:#f2f0e9; --muted:#aaa89f;
      --line:rgba(242,240,233,.16); --line-strong:rgba(242,240,233,.68); --panel:#171714;
      --accent:#d17a63;
    }}
    * {{ box-sizing:border-box; }}
    html {{ scroll-behavior:smooth; background:var(--paper); }}
    body {{ margin:0; color:var(--ink); background:var(--paper); font-family:var(--serif); line-height:1.65; }}
    body::before {{ content:""; position:fixed; inset:0; pointer-events:none; opacity:.22; z-index:-1;
      background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);
      background-size:44px 44px; mask-image:linear-gradient(to bottom,black,transparent 72vh); }}
    a {{ color:inherit; }}
    button,input {{ font:inherit; }}
    .skip {{ position:fixed; left:12px; top:-80px; z-index:99; padding:.65rem 1rem; background:var(--ink); color:var(--paper); font-family:var(--mono); }}
    .skip:focus {{ top:12px; }}
    .topbar {{ position:sticky; top:0; z-index:40; border-bottom:1px solid var(--line); background:color-mix(in srgb,var(--paper) 88%,transparent); backdrop-filter:blur(14px); }}
    .topbar-inner {{ max-width:var(--content); margin:auto; min-height:64px; display:flex; align-items:center; gap:1.2rem; padding:0 24px; }}
    .brand {{ margin-right:auto; text-decoration:none; font:800 1.15rem/1 var(--mono); letter-spacing:-.06em; }}
    .brand i,.hero-mark i {{ display:inline-block; width:.55em; height:.12em; margin-left:.08em; background:var(--accent); animation:blink 1.15s steps(1,end) infinite; }}
    @keyframes blink {{ 0%,48%{{opacity:1}}49%,100%{{opacity:.12}} }}
    .nav {{ display:flex; gap:1.1rem; align-items:center; }}
    .nav a {{ text-decoration:none; font:600 .72rem/1 var(--mono); text-transform:uppercase; letter-spacing:.08em; }}
    .nav a:hover,.nav a:focus-visible {{ color:var(--accent); }}
    .theme {{ border:1px solid var(--line); color:var(--ink); background:transparent; padding:.55rem .7rem; cursor:pointer; font:600 .68rem/1 var(--mono); }}
    .hero {{ min-height:calc(100vh - 64px); display:grid; place-items:center; border-bottom:1px solid var(--line); }}
    .hero-inner {{ width:min(var(--content),100%); padding:9vh 24px 8vh; display:grid; grid-template-columns:1.2fr .8fr; gap:5vw; align-items:end; }}
    .eyebrow,.kicker,.section-slug,.command,.track-index {{ font-family:var(--mono); text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }}
    .eyebrow {{ font-size:.73rem; margin-bottom:1.8rem; }}
    .hero-mark {{ margin:0; font:800 clamp(5.5rem,15vw,12rem)/.78 var(--mono); letter-spacing:-.1em; }}
    .hero h1 {{ margin:2.5rem 0 0; max-width:13ch; font:600 clamp(2rem,4.5vw,4.6rem)/1.03 var(--sans); letter-spacing:-.045em; }}
    .hero-copy {{ padding-bottom:.5rem; border-top:1px solid var(--line-strong); }}
    .hero-copy p {{ font-size:clamp(1.05rem,1.7vw,1.35rem); margin:1.5rem 0 2.2rem; max-width:32ch; }}
    .hero-actions {{ display:flex; flex-wrap:wrap; gap:.65rem; }}
    .button {{ display:inline-block; text-decoration:none; padding:.8rem 1rem; border:1px solid var(--ink); font:700 .72rem/1 var(--mono); text-transform:uppercase; letter-spacing:.05em; transition:.2s var(--ease); }}
    .button.primary {{ background:var(--ink); color:var(--paper); }}
    .button:hover,.button:focus-visible {{ transform:translateY(-2px); box-shadow:4px 4px 0 var(--accent); }}
    .section {{ max-width:var(--content); margin:auto; padding:clamp(5rem,10vw,9rem) 24px; }}
    .section-header {{ display:grid; grid-template-columns:150px 1fr; gap:2rem; border-top:1px solid var(--line-strong); padding-top:1.25rem; margin-bottom:4rem; }}
    .kicker {{ font-size:.72rem; }}
    .section-header h2 {{ margin:0; font:700 clamp(2.2rem,5vw,5rem)/.98 var(--sans); letter-spacing:-.05em; max-width:15ch; }}
    .manifesto-shell {{ display:grid; grid-template-columns:minmax(0,720px) 1fr; gap:clamp(2rem,7vw,7rem); align-items:start; }}
    .manifesto-intro {{ position:sticky; top:104px; order:2; border-top:1px solid var(--line); padding-top:1rem; }}
    .manifesto-intro code {{ display:block; font:.72rem/1.7 var(--mono); color:var(--muted); overflow-wrap:anywhere; }}
    .manifesto-body {{ max-width:72ch; }}
    .manifesto-body > p {{ margin:0 0 1.15rem; }}
    .manifesto-body h3 {{ scroll-margin-top:100px; margin:4.6rem 0 .15rem; font:700 clamp(1.4rem,2.8vw,2.25rem)/1.12 var(--sans); letter-spacing:-.025em; }}
    .manifesto-body h3:first-child {{ margin-top:0; }}
    .section-slug {{ font-size:.63rem; text-transform:none; margin:0 0 1.5rem; overflow-wrap:anywhere; }}
    blockquote {{ margin:1.7rem 0; padding:.2rem 0 .2rem 1.15rem; border-left:3px solid var(--accent); font-style:italic; font-size:1.04rem; }}
    pre {{ margin:1.6rem 0; padding:1rem 1.2rem; background:var(--panel); border-left:3px solid var(--line-strong); overflow:auto; white-space:pre-wrap; }}
    pre code {{ font:.74rem/1.55 var(--mono); }}
    .manifesto-emphasis {{ font-weight:700; font-size:1.05rem; }}
    .archive {{ border-top:1px solid var(--line); }}
    .archive-tools {{ display:grid; grid-template-columns:minmax(220px,1fr) auto; gap:1rem; align-items:end; margin-bottom:2.5rem; }}
    .search-label {{ display:block; font:600 .67rem/1 var(--mono); color:var(--muted); text-transform:uppercase; letter-spacing:.07em; margin-bottom:.65rem; }}
    .search {{ width:100%; border:0; border-bottom:2px solid var(--ink); background:transparent; color:var(--ink); padding:.75rem .1rem; outline:none; font:700 clamp(1.1rem,2vw,1.5rem)/1 var(--sans); }}
    .search:focus {{ border-color:var(--accent); }}
    .count {{ font:.72rem/1 var(--mono); color:var(--muted); padding-bottom:.9rem; }}
    .archive-grid {{ display:grid; grid-template-columns:250px minmax(0,1fr); gap:clamp(2rem,6vw,6rem); align-items:start; }}
    .track-nav {{ position:sticky; top:96px; max-height:calc(100vh - 120px); overflow:auto; border-top:1px solid var(--line); }}
    .track-link {{ display:grid; grid-template-columns:2rem 1fr; gap:.5rem; padding:.75rem 0; border-bottom:1px solid var(--line); text-decoration:none; font-family:var(--mono); }}
    .track-link span {{ color:var(--muted); font-size:.68rem; }}
    .track-link strong {{ font-size:.7rem; line-height:1.3; }}
    .track-link em {{ color:var(--accent); font-style:normal; }}
    .track-link:hover strong,.track-link.active strong {{ color:var(--accent); }}
    .track {{ scroll-margin-top:92px; padding:0 0 clamp(6rem,10vw,9rem); }}
    .track[hidden],.track-link[hidden] {{ display:none; }}
    .track-head {{ border-top:1px solid var(--line-strong); padding-top:1.1rem; margin-bottom:2.2rem; }}
    .track-index {{ font-size:.66rem; }}
    .track h3 {{ margin:.65rem 0 .4rem; font:800 clamp(2rem,5vw,4.6rem)/.96 var(--mono); letter-spacing:-.07em; max-width:15ch; }}
    .command {{ font-size:.62rem; text-transform:none; overflow-wrap:anywhere; }}
    .listen {{ display:inline-flex; align-items:center; gap:.5rem; margin-top:1.15rem; padding:.68rem .82rem;
      border:1px solid var(--line-strong); text-decoration:none; font:700 .67rem/1 var(--mono);
      text-transform:uppercase; letter-spacing:.055em; transition:.2s var(--ease); }}
    .listen span {{ color:var(--accent); font-size:.6rem; }}
    .listen b {{ font-weight:400; color:var(--muted); }}
    .listen:hover,.listen:focus-visible {{ color:var(--paper); background:var(--ink); border-color:var(--ink); transform:translateY(-2px); }}
    .lyrics {{ padding-left:clamp(0rem,4vw,3.5rem); max-width:70ch; }}
    .verse-line {{ min-height:1.55em; font-size:clamp(1rem,1.4vw,1.12rem); }}
    .verse-line.gap,.stage.gap {{ margin-top:1.05rem; }}
    .stage {{ color:var(--muted); font:.68rem/1.5 var(--mono); margin:.38rem 0; max-width:82ch; }}
    .footer {{ border-top:1px solid var(--line-strong); background:var(--ink); color:var(--paper); }}
    .footer-inner {{ max-width:var(--content); margin:auto; padding:4rem 24px; display:grid; grid-template-columns:1fr auto; gap:2rem; align-items:end; }}
    .footer-mark {{ font:800 clamp(3rem,8vw,7rem)/.8 var(--mono); letter-spacing:-.08em; }}
    .footer p {{ margin:0; max-width:38ch; color:color-mix(in srgb,var(--paper) 68%,transparent); }}
    :focus-visible {{ outline:2px solid var(--accent); outline-offset:4px; }}
    @media (max-width:840px) {{
      .hero-inner,.manifesto-shell,.archive-grid {{ grid-template-columns:1fr; }}
      .hero-inner {{ align-items:center; }} .hero-copy {{ margin-top:3rem; }}
      .manifesto-intro {{ position:static; order:0; }}
      .archive-grid {{ gap:3rem; }} .track-nav {{ position:static; max-height:240px; }}
      .section-header {{ grid-template-columns:1fr; gap:.8rem; }}
    }}
    @media (max-width:620px) {{
      .nav a {{ display:none; }} .topbar-inner {{ min-height:56px; padding:0 16px; }}
      .hero {{ min-height:calc(100svh - 56px); }} .hero-inner,.section {{ padding-left:16px; padding-right:16px; }}
      .hero-mark {{ font-size:clamp(5rem,28vw,8rem); }} .hero h1 {{ font-size:2.2rem; }}
      .archive-tools,.footer-inner {{ grid-template-columns:1fr; }} .count {{ padding:0; }}
      .track h3 {{ font-size:clamp(2rem,11vw,3.5rem); }}
    }}
    @media (prefers-reduced-motion:reduce) {{ html{{scroll-behavior:auto}} *,*::before,*::after{{animation:none!important;transition:none!important}} }}
    @media print {{
      .topbar,.hero-actions,.archive-tools,.track-nav,.footer {{ display:none!important; }}
      body,html {{ background:#fff; color:#000; }} body::before {{ display:none; }}
      .hero {{ min-height:auto; padding:3cm 0; page-break-after:always; }}
      .manifesto-intro {{ position:static; }} .manifesto-shell,.archive-grid {{ display:block; }}
      .track {{ break-before:page; }} .section {{ max-width:none; padding:1.5cm; }}
    }}
  </style>
</head>
<body>
  <a class="skip" href="#conteudo">Pular para o conteúdo</a>
  <header class="topbar">
    <div class="topbar-inner">
      <a class="brand" href="#inicio" aria-label="FEZ início">FEZ<i aria-hidden="true"></i></a>
      <nav class="nav" aria-label="Navegação principal">
        <a href="#manifesto">Manifesto</a><a href="#letras">Letras</a>
      </nav>
      <button class="theme" type="button" aria-label="Alternar tema" aria-pressed="false">CLARO/ESCURO</button>
    </div>
  </header>
  <main id="conteudo">
    <section class="hero" id="inicio" aria-labelledby="titulo-site">
      <div class="hero-inner">
        <div>
          <div class="eyebrow">arquivo vivo / palavra em movimento</div>
          <p class="hero-mark" aria-hidden="true">FEZ<i></i></p>
          <h1 id="titulo-site">Rap, poesia, ancestralidade e tecnologia.</h1>
        </div>
        <div class="hero-copy">
          <p>Um território de letras, ritmo e processo. A semente entra no caldo. A palavra encontra outras palavras. A obra emerge.</p>
          <div class="hero-actions">
            <a class="button primary" href="#manifesto">Ler o manifesto</a>
            <a class="button" href="#letras">Abrir as letras</a>
          </div>
        </div>
      </div>
    </section>

    <section class="section" id="manifesto" aria-labelledby="manifesto-title">
      <header class="section-header">
        <div class="kicker">01 / fundamento</div>
        <h2 id="manifesto-title">Criar no Caldo do Mundo</h2>
      </header>
      <div class="manifesto-shell">
        <article class="manifesto-body">{manifesto}</article>
        <aside class="manifesto-intro" aria-label="Metadados do manifesto">
          <code>def ensaio_filosófico():</code>
          <code>&nbsp;&nbsp;return "arte + tecnologia + dissolução_do_eu"</code>
          <br>
          <code>autor = "Felipe Brito (FEZ)"</code>
          <code>ecossistema = "AlquimiXGriot"</code>
          <code>processo = "RAPP"</code>
          <code>ano = 2025</code>
        </aside>
      </div>
    </section>

    <section class="section archive" id="letras" aria-labelledby="letras-title">
      <header class="section-header">
        <div class="kicker">02 / arquivo</div>
        <h2 id="letras-title">Caderno de Letras</h2>
      </header>
      <div class="archive-tools">
        <label><span class="search-label">Buscar no catálogo</span><input class="search" id="track-search" type="search" placeholder="Digite o nome de uma faixa" autocomplete="off"></label>
        <div class="count" aria-live="polite"><span id="track-count">13</span> faixas</div>
      </div>
      <div class="archive-grid">
        <nav class="track-nav" aria-label="Índice de letras">{track_nav}</nav>
        <div id="track-list">{track_cards}</div>
      </div>
    </section>
  </main>
  <footer class="footer">
    <div class="footer-inner"><div class="footer-mark">FEZ_</div><p>Entre laboratório e rua. Entre código e corpo. Entre palavra e ritmo. Entre memória e invenção.</p></div>
  </footer>
  <script>
    (() => {{
      const root = document.documentElement;
      const themeButton = document.querySelector('.theme');
      const saved = localStorage.getItem('fez-theme');
      const preferred = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      const setTheme = value => {{ root.dataset.theme = value; themeButton.setAttribute('aria-pressed', String(value === 'dark')); }};
      setTheme(saved || preferred);
      themeButton.addEventListener('click', () => {{ const next = root.dataset.theme === 'dark' ? 'light' : 'dark'; setTheme(next); localStorage.setItem('fez-theme', next); }});

      const input = document.querySelector('#track-search');
      const tracks = [...document.querySelectorAll('.track')];
      const links = [...document.querySelectorAll('.track-link')];
      const count = document.querySelector('#track-count');
      const normalize = value => value.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();
      input.addEventListener('input', () => {{
        const query = normalize(input.value.trim()); let shown = 0;
        tracks.forEach((track, index) => {{
          const match = !query || normalize(track.dataset.track).includes(query) || normalize(track.textContent).includes(query);
          track.hidden = !match; links[index].hidden = !match; if (match) shown++;
        }});
        count.textContent = shown;
      }});

      const observer = new IntersectionObserver(entries => {{
        entries.filter(entry => entry.isIntersecting).forEach(entry => {{
          links.forEach(link => link.classList.toggle('active', link.getAttribute('href') === '#' + entry.target.id));
        }});
      }}, {{ rootMargin:'-15% 0px -70% 0px' }});
      tracks.forEach(track => observer.observe(track));
    }})();
  </script>
</body>
</html>'''

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(document, encoding="utf-8", newline="\n")
print(OUT)
