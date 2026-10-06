"""Analitika zaposlenih kao pravi PDF (A4, reportlab): zaglavlje i podnožje na svakoj strani, vektorski grafikoni.

Sadržaj je isti kao na ekranu (`analitika.analitika`). Slova č, ć, đ zahtevaju TrueType font sa latinicom
proširenom — koristi se Arial iz Windowsa (server je Windows), a na drugim sistemima DejaVu Sans.
"""
import logging
import os
from io import BytesIO
from xml.sax.saxutils import escape

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.utils import timezone
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, KeepTogether, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle)

from .spisak_zaposlenih import ADRESA, INSTITUT

logger = logging.getLogger(__name__)

PLAVA = colors.HexColor("#14395B")
SIVA = colors.HexColor("#64748B")
TAMNA = colors.HexColor("#0F2A44")
LINIJA = colors.HexColor("#D7DCE5")
SVETLA = colors.HexColor("#F4F7FA")
ZBIR = colors.HexColor("#E8F0FB")
MUSKI = colors.HexColor("#2563A6")
ZENE = colors.HexColor("#C2417B")
ZELENA = colors.HexColor("#2F8F6F")

SIRINA, VISINA = A4
LEVO = DESNO = 14 * mm
GORE, DOLE = 32 * mm, 16 * mm
KORISNO = SIRINA - LEVO - DESNO

FONTOVI = (
    (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
)


def _fontovi():
    """(obican, podebljan) — registruje TrueType font sa našim slovima; Helvetica samo kao krajnja rezerva."""
    if "IMS" in pdfmetrics.getRegisteredFontNames():
        return "IMS", "IMS-Bold"
    kandidati = [getattr(settings, "PDF_FONTOVI", None)] + list(FONTOVI)
    for par in filter(None, kandidati):
        if all(os.path.exists(p) for p in par):
            pdfmetrics.registerFont(TTFont("IMS", par[0]))
            pdfmetrics.registerFont(TTFont("IMS-Bold", par[1]))
            return "IMS", "IMS-Bold"
    logger.warning("Nije pronađen TrueType font za PDF; slova č, ć, đ neće biti ispravno prikazana.")
    return "Helvetica", "Helvetica-Bold"


def broj(v, decimale=1):
    if v is None:
        return "—"
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    return f"{v:,.{decimale}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def procenat(v):
    return "—" if v is None else broj(v) + "%"


class _Brojac(rl_canvas.Canvas):
    """Canvas koji posle poslednje strane zna ukupan broj strana („Strana 2 od 5”)."""

    def __init__(self, *args, crtaj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._strane, self._crtaj = [], crtaj

    def showPage(self):
        self._strane.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        ukupno = len(self._strane)
        for stanje in self._strane:
            self.__dict__.update(stanje)
            self._crtaj(self, self._pageNumber, ukupno)
            super().showPage()
        super().save()


def _okvir_strane(fontovi, filteri, izradjeno):
    obican, podebljan = fontovi
    logo = finders.find("fleet/assets/images/logoims.png")

    def crtaj(c, strana, ukupno):
        c.saveState()
        vrh = VISINA - 12 * mm
        if logo:
            c.drawImage(logo, LEVO, vrh - 13 * mm, width=22 * mm, height=13 * mm, preserveAspectRatio=True, mask="auto")
        x = LEVO + 26 * mm
        c.setFillColor(PLAVA)
        c.setFont(podebljan, 12)
        c.drawString(x, vrh - 4.5 * mm, INSTITUT)
        c.setFillColor(SIVA)
        c.setFont(obican, 8)
        c.drawString(x, vrh - 9 * mm, ADRESA)
        c.drawString(x, vrh - 12.5 * mm, "Kadrovska evidencija · Analitika zaposlenih")
        c.setFont(obican, 7.5)
        c.drawRightString(SIRINA - DESNO, vrh - 4.5 * mm, f"Izrađeno: {izradjeno:%d.%m.%Y. %H:%M}")
        c.drawRightString(SIRINA - DESNO, vrh - 9 * mm, filteri[:90])
        c.setStrokeColor(PLAVA)
        c.setLineWidth(1.6)
        c.line(LEVO, vrh - 16 * mm, SIRINA - DESNO, vrh - 16 * mm)
        c.setStrokeColor(LINIJA)
        c.setLineWidth(0.5)
        c.line(LEVO, 11 * mm, SIRINA - DESNO, 11 * mm)
        c.setFillColor(SIVA)
        c.setFont(obican, 7)
        c.drawString(LEVO, 7 * mm, f"{INSTITUT} · Analitika zaposlenih · interni dokument")
        c.drawRightString(SIRINA - DESNO, 7 * mm, f"Strana {strana} od {ukupno}")
        c.restoreState()

    return crtaj


# --- grafikoni (vektorski) --------------------------------------------------------------------------

def _piramida(a, sirina, visina, fontovi):
    obican, podebljan = fontovi
    d = Drawing(sirina, visina)
    sredina, sirina_raspona = sirina / 2, 15 * mm
    duzina = (sirina - sirina_raspona) / 2 - 8 * mm
    redovi = list(reversed(a["starosni"]))
    korak = (visina - 7 * mm) / len(redovi)
    d.add(String(sredina - sirina_raspona / 2 - 2, visina - 4 * mm, "Muškarci", fontName=podebljan, fontSize=7.5,
                 fillColor=MUSKI, textAnchor="end"))
    d.add(String(sredina + sirina_raspona / 2 + 2, visina - 4 * mm, "Žene", fontName=podebljan, fontSize=7.5, fillColor=ZENE))
    for i, r in enumerate(redovi):
        y = visina - 7 * mm - (i + 1) * korak + korak * 0.18
        h = korak * 0.64
        d.add(String(sredina, y + h / 2 - 2.5, r["naziv"], fontName=podebljan, fontSize=7, fillColor=TAMNA, textAnchor="middle"))
        m = duzina * r["sirina_muski"] / 100
        z = duzina * r["sirina_zene"] / 100
        if m:
            d.add(Rect(sredina - sirina_raspona / 2 - m, y, m, h, fillColor=MUSKI, strokeColor=None))
        if z:
            d.add(Rect(sredina + sirina_raspona / 2, y, z, h, fillColor=ZENE, strokeColor=None))
        d.add(String(sredina - sirina_raspona / 2 - m - 2, y + h / 2 - 2.5, str(r["muski"]), fontName=obican, fontSize=7,
                     fillColor=TAMNA, textAnchor="end"))
        d.add(String(sredina + sirina_raspona / 2 + z + 2, y + h / 2 - 2.5, str(r["zene"]), fontName=obican, fontSize=7,
                     fillColor=TAMNA))
    return d


def _stubici(redovi, sirina, visina, fontovi, *, boja=ZELENA, vrednost="ukupno", naziv="naziv"):
    obican, podebljan = fontovi
    d = Drawing(sirina, visina)
    osnova, vrh = 9 * mm, visina - 6 * mm
    najvise = max((r[vrednost] for r in redovi), default=0) or 1
    korak = sirina / max(len(redovi), 1)
    d.add(Line(0, osnova, sirina, osnova, strokeColor=SIVA, strokeWidth=0.6))
    for i, r in enumerate(redovi):
        x = i * korak + korak * 0.16
        s = korak * 0.68
        h = (vrh - osnova) * r[vrednost] / najvise
        if h:
            d.add(Rect(x, osnova, s, h, fillColor=boja, strokeColor=None))
        d.add(String(x + s / 2, osnova + h + 2, str(r[vrednost]), fontName=podebljan, fontSize=7, fillColor=TAMNA,
                     textAnchor="middle"))
        d.add(String(x + s / 2, osnova - 9, r[naziv], fontName=obican, fontSize=6.5, fillColor=SIVA, textAnchor="middle"))
    return d


def _trake_spreme(stepeni, sirina, fontovi):
    obican, podebljan = fontovi
    red_visina = 6.2 * mm
    d = Drawing(sirina, red_visina * len(stepeni) + 8 * mm)
    oznaka_sirina, broj_sirina = 62 * mm, 26 * mm
    duzina = sirina - oznaka_sirina - broj_sirina
    najvise = max((r["ukupno"] for r in stepeni), default=0) or 1
    vrh = d.height - 6 * mm
    d.add(Rect(oznaka_sirina, vrh + 1.5 * mm, 3 * mm, 2.4 * mm, fillColor=MUSKI, strokeColor=None))
    d.add(String(oznaka_sirina + 4 * mm, vrh + 1.8 * mm, "Muškarci", fontName=obican, fontSize=6.8, fillColor=SIVA))
    d.add(Rect(oznaka_sirina + 22 * mm, vrh + 1.5 * mm, 3 * mm, 2.4 * mm, fillColor=ZENE, strokeColor=None))
    d.add(String(oznaka_sirina + 26 * mm, vrh + 1.8 * mm, "Žene", fontName=obican, fontSize=6.8, fillColor=SIVA))
    for i, r in enumerate(stepeni):
        y = vrh - (i + 1) * red_visina + 1.2 * mm
        h = red_visina - 2.4 * mm
        d.add(String(0, y + 1.2, r["prikaz"], fontName=obican, fontSize=7.2, fillColor=TAMNA))
        m = duzina * r["muski"] / najvise
        z = duzina * r["zene"] / najvise
        if m:
            d.add(Rect(oznaka_sirina, y, m, h, fillColor=MUSKI, strokeColor=None))
        if z:
            d.add(Rect(oznaka_sirina + m, y, z, h, fillColor=ZENE, strokeColor=None))
        d.add(String(sirina, y + 1.2, f'{r["ukupno"]} · {procenat(r["udeo"])}', fontName=podebljan, fontSize=7.2,
                     fillColor=TAMNA, textAnchor="end"))
    return d


# --- tabele -----------------------------------------------------------------------------------------

def _tabela(zaglavlje, redovi, sirine, fontovi, *, zbir=None, levo=1, boje=None):
    obican, podebljan = fontovi
    podaci = [zaglavlje] + redovi + ([zbir] if zbir else [])
    t = Table(podaci, colWidths=sirine, repeatRows=1)
    stil = [
        ("FONT", (0, 0), (-1, -1), obican, 7.6),
        ("FONT", (0, 0), (-1, 0), podebljan, 7.2),
        ("BACKGROUND", (0, 0), (-1, 0), PLAVA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (levo, 0), (-1, -1), "RIGHT"),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINIJA),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(redovi) + 1):
        if i % 2 == 0:
            stil.append(("BACKGROUND", (0, i), (-1, i), SVETLA))
    if zbir:
        stil += [("BACKGROUND", (0, -1), (-1, -1), ZBIR), ("FONT", (0, -1), (-1, -1), podebljan, 7.6),
                 ("LINEABOVE", (0, -1), (-1, -1), 1, PLAVA)]
    stil += boje or []
    t.setStyle(TableStyle(stil))
    return t


def _kartice(a, fontovi, stilovi):
    s = a["sazetak"]
    kartice = [
        ("Zaposlenih", broj(a["ukupno"]), f"aktivnih na dan {a['na_dan']:%d.%m.%Y.}", PLAVA),
        ("Žene", broj(s["zene"]), f"{procenat(s['udeo_zena'])} · prosečno {broj(s['prosek_zene'])} god.", ZENE),
        ("Muškarci", broj(s["muski"]), f"{procenat(s['udeo_muski'])} · prosečno {broj(s['prosek_muski'])} god.", MUSKI),
        ("Prosečna starost", broj(s["prosek"]),
         f"medijana {broj(s['medijana'], 1) if s['medijana'] is not None else '—'} · {s['najmladji'] or '—'}–{s['najstariji'] or '—'} god.", PLAVA),
        ("Prosečan staž u Institutu", broj(s["prosek_staz"]), "godina, od datuma zaposlenja", ZELENA),
        ("Visoka i viša sprema", procenat(s["udeo_visoka"]), f"{s['visoka']} zaposlenih, stepen VI–VIII", ZELENA),
        ("60 i više godina", broj(s["pred_penzijom"]), "bliže uslovima za penziju", colors.HexColor("#B45309")),
        ("Bez datuma rođenja", broj(s["bez_starosti"]), "nisu u starosnim pokazateljima", SIVA),
    ]
    celije = [[Paragraph(escape(l), stilovi["kl"]), Paragraph(escape(v), stilovi["kv"]), Paragraph(escape(p), stilovi["kp"])]
              for l, v, p, _ in kartice]
    sirina = KORISNO / 4
    redovi = [[celije[i], celije[i + 1], celije[i + 2], celije[i + 3]] for i in (0, 4)]
    t = Table(redovi, colWidths=[sirina] * 4, rowHeights=[19 * mm] * 2)
    stil = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.4, LINIJA),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, LINIJA), ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6)]
    for i, (_, _, _, boja) in enumerate(kartice):
        red, kol = divmod(i, 4)
        stil.append(("LINEBEFORE", (kol, red), (kol, red), 3, boja))
    t.setStyle(TableStyle(stil))
    return t


def pdf(a, filteri):
    fontovi = _fontovi()
    obican, podebljan = fontovi
    stilovi = {
        "naslov": ParagraphStyle("naslov", fontName=podebljan, fontSize=17, leading=21, textColor=PLAVA, spaceAfter=1 * mm),
        "meta": ParagraphStyle("meta", fontName=obican, fontSize=8.5, leading=11, textColor=SIVA, spaceAfter=4 * mm),
        "h2": ParagraphStyle("h2", fontName=podebljan, fontSize=11.5, leading=14, textColor=PLAVA, spaceBefore=5 * mm,
                             spaceAfter=0.6 * mm, keepWithNext=1),
        "opis": ParagraphStyle("opis", fontName=obican, fontSize=7.6, leading=9.6, textColor=SIVA, spaceAfter=2 * mm,
                               keepWithNext=1),
        "napomena": ParagraphStyle("napomena", fontName=obican, fontSize=7.4, leading=9.6, textColor=SIVA, spaceBefore=4 * mm),
        "kl": ParagraphStyle("kl", fontName=obican, fontSize=6.8, leading=8, textColor=SIVA),
        "kv": ParagraphStyle("kv", fontName=podebljan, fontSize=15, leading=18, textColor=TAMNA),
        "kp": ParagraphStyle("kp", fontName=obican, fontSize=6.6, leading=8, textColor=SIVA),
    }
    izradjeno = timezone.localtime()
    bafer = BytesIO()
    dokument = BaseDocTemplate(bafer, pagesize=A4, leftMargin=LEVO, rightMargin=DESNO, topMargin=GORE, bottomMargin=DOLE,
                               title="Analitika zaposlenih", author=INSTITUT, subject=filteri)
    okvir = Frame(LEVO, DOLE, KORISNO, VISINA - GORE - DOLE, id="sadrzaj", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    dokument.addPageTemplates([PageTemplate(id="strana", frames=[okvir])])

    def h2(tekst, opis=""):
        delovi = [Paragraph(escape(tekst), stilovi["h2"])]
        if opis:
            delovi.append(Paragraph(escape(opis), stilovi["opis"]))
        return delovi

    s = a["sazetak"]
    sadrzaj = [Paragraph("Analitika zaposlenih", stilovi["naslov"]),
               Paragraph(escape(f"{filteri} · stanje na dan {a['na_dan']:%d.%m.%Y.}"), stilovi["meta"]),
               _kartice(a, fontovi, stilovi)]

    pola = (KORISNO - 6 * mm) / 2
    grafikoni = Table([[
        [*h2("Starosna piramida", "Broj zaposlenih po rasponima starosti; muškarci levo, žene desno."),
         _piramida(a, pola, 66 * mm, fontovi)],
        [*h2("Histogram starosti", "Ukupan broj zaposlenih po rasponima od deset godina."),
         _stubici(a["starosni"], pola, 66 * mm, fontovi)],
    ]], colWidths=[pola + 3 * mm, pola + 3 * mm])
    grafikoni.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm)]))
    sadrzaj += [grafikoni]

    def udeo_zena(r):
        return procenat(r["udeo_zena"]) if r["udeo_zena"] is not None else "—"

    sirine7 = [34 * mm, 20 * mm, 20 * mm, 20 * mm, 22 * mm, 22 * mm, KORISNO - 138 * mm]
    sadrzaj += [KeepTogether([*h2("Starosna struktura po rasponima"), _tabela(
        ["Godine", "Ukupno", "Udeo", "Žene", "Muškarci", "Udeo žena", "Prosečna starost"],
        [[r["naziv"], broj(r["ukupno"]), procenat(r["udeo"]), broj(r["zene"]), broj(r["muski"]), udeo_zena(r),
          broj(r["prosek"])] for r in a["starosni"]],
        sirine7, fontovi,
        zbir=["Ukupno sa poznatom starošću", broj(a["sa_starosti"]), "100,0%", broj(s["zene"]), broj(s["muski"]),
              procenat(s["udeo_zena"]), broj(s["prosek"])])])]

    sadrzaj += [CondPageBreak(95 * mm), *h2(
        "Stručna sprema", "Stepen je izveden iz naziva zanimanja (a kad ga nema, iz škole) iz kadrovske baze — vidi napomenu."),
        _trake_spreme(a["stepeni"], KORISNO, fontovi), Spacer(1, 2 * mm),
        _tabela(["Stepen", "Stručna sprema", "Ukupno", "Udeo", "Žene", "Muškarci", "Udeo žena", "Prosek", "Prosek Ž",
                 "Prosek M"],
                [["—" if r["oznaka"] == r["naziv"] else r["oznaka"], r["naziv"], broj(r["ukupno"]), procenat(r["udeo"]), broj(r["zene"]), broj(r["muski"]),
                  udeo_zena(r), broj(r["prosek"]), broj(r["prosek_zene"]), broj(r["prosek_muski"])] for r in a["stepeni"]],
                [16 * mm, 50 * mm] + [(KORISNO - 66 * mm) / 8] * 8, fontovi, levo=2)]

    najvise = max((b for r in a["ukrstanje"] for b in r["rasponi"]), default=0) or 1
    boje = []
    for i, r in enumerate(a["ukrstanje"], 1):
        for j, b in enumerate(r["rasponi"], 1):
            if b:
                jacina = 0.12 + 0.75 * b / najvise
                boje.append(("BACKGROUND", (j, i), (j, i), colors.Color(0.078, 0.224, 0.357, alpha=jacina)))
                if jacina > 0.5:
                    boje.append(("TEXTCOLOR", (j, i), (j, i), colors.white))
    n = len(a["rasponi_nazivi"])
    sadrzaj += [KeepTogether([*h2("Starost po stručnoj spremi",
                                  "Broj zaposlenih u svakom rasponu starosti za svaki stepen; tamnije polje je brojnija grupa."),
                              _tabela(["Stručna sprema", *a["rasponi_nazivi"], "Ukupno", "Prosek"],
                                      [[r["prikaz"], *[str(b) if b else "·" for b in r["rasponi"]],
                                        broj(r["ukupno"]), broj(r["prosek"])] for r in a["ukrstanje"]],
                                      [56 * mm] + [(KORISNO - 56 * mm) / (n + 2)] * (n + 2), fontovi, boje=boje)])]

    pola_tabela = (KORISNO - 6 * mm) / 2
    staz = [*h2("Staž u Institutu", "Godine od datuma zaposlenja u Institutu (ne ukupan radni staž)."),
            _stubici(a["staz"], pola_tabela, 42 * mm, fontovi, boja=PLAVA), Spacer(1, 2 * mm),
            _tabela(["Staž", "Broj", "Udeo", "Žene", "Muški", "Prosek"],
                    [[r["naziv"], broj(r["ukupno"]), procenat(r["udeo"]), broj(r["zene"]), broj(r["muski"]),
                      broj(r["prosek"])] for r in a["staz"]],
                    [24 * mm] + [(pola_tabela - 24 * mm) / 5] * 5, fontovi)]
    odnos = [*h2("Vrsta radnog odnosa", "Iz kadrovske baze (status zaposlenog)."),
             _tabela(["Radni odnos", "Broj", "Udeo", "Žene", "Muški", "Prosek"],
                     [[r["naziv"], broj(r["ukupno"]), procenat(r["udeo"]), broj(r["zene"]), broj(r["muski"]),
                       broj(r["prosek"])] for r in a["odnos"]],
                     [34 * mm] + [(pola_tabela - 34 * mm) / 5] * 5, fontovi)]
    dva = Table([[staz, odnos]], colWidths=[pola_tabela + 3 * mm, pola_tabela + 3 * mm])
    dva.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm)]))
    sadrzaj += [CondPageBreak(90 * mm), dva]

    sadrzaj += [CondPageBreak(40 * mm), *h2("Po organizacionim jedinicama"),
                _tabela(["Organizaciona jedinica", "Ukupno", "Udeo", "Žene", "Muškarci", "Udeo žena", "Prosečna starost"],
                        [[Paragraph(escape(r["naziv"]), ParagraphStyle("oj", fontName=obican, fontSize=7.6, leading=9)),
                          broj(r["ukupno"]), procenat(r["udeo"]), broj(r["zene"]), broj(r["muski"]), udeo_zena(r),
                          broj(r["prosek"])] for r in a["oj"]],
                        [KORISNO - 116 * mm, 16 * mm, 18 * mm, 16 * mm, 20 * mm, 20 * mm, 26 * mm], fontovi,
                        zbir=["Ukupno", broj(a["ukupno"]), "100,0%", broj(s["zene"]), broj(s["muski"]),
                              procenat(s["udeo_zena"]), broj(s["prosek"])])]

    napomena = ("<b>Napomena o stručnoj spremi:</b> kadrovska baza nema stepen spreme kao posebno polje, pa se on izvodi "
                "iz naziva zanimanja: „doktor” → VIII; „master”, „dipl.”, fakultet → VII; „strukovni”, „inženjer”, viša "
                "škola → VI; „specijalista” → V; „tehničar”, gimnazija, srednja škola → IV; zanati (bravar, mehaničar, "
                "vozač…) → III. Starost i staž su pune godine na dan izrade; datum rođenja 01.01.1900. u izvoru znači "
                "da datum nije upisan.")
    if a["nerazvrstani"]:
        napomena += f" Nije razvrstano: {sum(n['broj'] for n in a['nerazvrstani'])} zaposlenih (spisak u Excelu)."
    sadrzaj.append(Paragraph(napomena, stilovi["napomena"]))

    crtaj = _okvir_strane(fontovi, filteri, izradjeno)
    dokument.build(sadrzaj, canvasmaker=lambda *args, **kwargs: _Brojac(*args, crtaj=crtaj, **kwargs))
    odgovor = HttpResponse(bafer.getvalue(), content_type="application/pdf")
    odgovor["Content-Disposition"] = f'inline; filename="analitika_zaposlenih_{izradjeno:%Y%m%d}.pdf"'
    return odgovor
