"""Render UML locally using Java and the installed VS Code PlantUML extension.

Usage: python dokumentacija/dijagrami/render.py [--java PATH] [--jar PATH]
No Django initialization, database connection, or external rendering service.
"""
import argparse
import html
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
DIAGRAMS = [
    ('01-pregled-sistema', 'Pregled sistema', 'Korisnici, IMS ERP i spoljni izvori podataka.'),
    ('02-organizacija-modula', 'Organizacija modula', 'Poslovne oblasti, Django moduli i zajedničke funkcije.'),
    ('03-serveri-i-podaci', 'Servisi i izvori podataka', 'Windows, NSSM, Django, Celery, Redis i SQL Server.'),
    ('04-kadrovi-model-podataka', 'Kadrovi: model podataka', 'Zaposleni, zahtevi, rešenja, vrste, dani i potpisnici.'),
    ('05-kadrovi-tok-resenja', 'Kadrovi: tok rešenja', 'Provere, kreiranje nacrta i izdavanje dokumenta.'),
    ('06-korisnici-i-dozvole', 'Korisnici i dozvole', 'Uloge, dozvole ruta i organizacioni obuhvat.'),
]


def find_java():
    if path := shutil.which('java'):
        return path
    candidates = []
    if os.environ.get('JAVA_HOME'):
        candidates.append(Path(os.environ['JAVA_HOME']) / 'bin' / 'java.exe')
    for vendor in ('Eclipse Adoptium', 'Java', 'Microsoft'):
        folder = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / vendor
        candidates.extend(sorted(folder.glob('*/bin/java.exe'), reverse=True))
    return next((str(path) for path in candidates if path.is_file()), None)


def find_jar():
    jars = list((Path.home() / '.vscode/extensions').glob('jebbs.plantuml-*/plantuml.jar'))
    return str(max(jars, key=lambda path: path.stat().st_mtime)) if jars else None


def build_gallery():
    cards = []
    for stem, title, description in DIAGRAMS:
        cards.append(f'''<article>
<a class="preview" href="svg/{stem}.svg"><img src="svg/{stem}.svg" alt="{html.escape(title)}"></a>
<div class="card-body"><h2>{html.escape(title)}</h2><p>{html.escape(description)}</p>
<nav aria-label="Formati: {html.escape(title)}"><a href="svg/{stem}.svg">Otvori SVG</a>
<a href="png/{stem}.png">PNG</a><a href="{stem}.puml" download>PlantUML izvor</a></nav></div></article>''')
    page = '''<!doctype html><html lang="sr-Latn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>IMS ERP | UML arhitektura</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f2f5f8;color:#213b50;font:16px/1.6 "Segoe UI",sans-serif}
header{background:linear-gradient(120deg,#163b55,#237f79);color:white;padding:42px max(24px,calc((100vw - 1280px)/2))}
header small{letter-spacing:.12em}h1{font-size:34px;line-height:1.2;margin:10px 0}header p{margin:0;max-width:850px;color:#dcecf2}
main{max-width:1328px;padding:28px 24px 48px;margin:auto}.intro{margin-bottom:24px;color:#536b7d}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,360px),1fr));gap:24px}
article{background:white;border:1px solid #dce5ed;border-radius:12px;overflow:hidden;box-shadow:0 4px 14px #163b5508}
.preview{display:block;background:#fff;padding:16px;border-bottom:1px solid #e6edf2}.preview img{display:block;width:100%;height:240px;object-fit:contain}
.card-body{padding:20px}h2{font-size:20px;margin:0 0 8px}p{margin:0 0 18px}nav{display:flex;flex-wrap:wrap;gap:16px}
a{color:#176087;text-decoration:none}a:hover{text-decoration:underline}a:focus-visible{outline:3px solid #298c94;outline-offset:4px}
footer{margin-top:30px;font-size:13px;color:#607586}@media(max-width:500px){h1{font-size:28px}.preview img{height:200px}}
</style></head><body><header><small>IMS ERP · TEHNIČKA DOKUMENTACIJA</small>
<h1>Kako je sistem organizovan</h1><p>Od pregleda aplikacije i njenih modula do servisa, modela podataka i toka izdavanja rešenja.</p></header>
<main><p class="intro">Počnite od pregleda sistema. Za uvećanje otvorite SVG; za izmene koristite PlantUML izvor i Alt+D u VS Code-u.</p>
<div class="grid">''' + '\n'.join(cards) + '''</div>
<footer>Stanje repozitorijuma: 28.09.2026. · Dijagrami se generišu lokalno.
Raspored servera zasnovan je na konfiguraciji i dokumentaciji, bez provere živih servisa.</footer></main></body></html>'''
    (ROOT / 'index.html').write_text(page, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java', default=find_java())
    parser.add_argument('--jar', default=find_jar())
    args = parser.parse_args()
    if not args.java or not args.jar:
        parser.error('Install Java and jebbs.plantuml, or supply --java and --jar paths.')
    sources = [f'{stem}.puml' for stem, _, _ in DIAGRAMS]
    command = [args.java, '-Djava.awt.headless=true', '-jar', args.jar, '-charset', 'UTF-8']
    subprocess.run(command + ['-checkonly', *sources], cwd=ROOT, check=True)
    for output in ('svg', 'png'):
        (ROOT / output).mkdir(exist_ok=True)
        subprocess.run(command + ['-failfast2', f'-t{output}', '-o', output, *sources], cwd=ROOT, check=True)
    for stem, _, _ in DIAGRAMS:
        svg = ROOT / 'svg' / f'{stem}.svg'
        root = ET.parse(svg).getroot()
        if root.tag != '{http://www.w3.org/2000/svg}svg' or 'Syntax Error' in svg.read_text(encoding='utf-8'):
            raise RuntimeError(f'Invalid diagram: {stem}')
        if not (ROOT / 'png' / f'{stem}.png').is_file():
            raise RuntimeError(f'Missing PNG: {stem}')
    build_gallery()
    print(f'OK: {len(DIAGRAMS)} diagrams, SVG + PNG. Gallery: {ROOT / "index.html"}')


if __name__ == '__main__':
    main()
