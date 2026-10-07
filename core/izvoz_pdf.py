"""PDF izvoz tabele izveštaja (od 07.10.2026.): A4 položeno, zaglavlje Instituta, filteri, „Strana x od y”.

Za izveštaje koji se prave na serveru (Excel ide kroz `core.exporting.rows_to_xlsx_response`). Ekrani sa
tabelom `ReportsDT` imaju PDF u pregledaču (`report_datatable.js`, pdfmake).
"""
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PLAVA = colors.HexColor("#14395B")
SIVA = colors.HexColor("#64748B")
LINIJA = colors.HexColor("#D7DCE5")
SVETLA = colors.HexColor("#F4F7FA")
ZBIR = colors.HexColor("#E8F0FB")
INSTITUT = "Institut IMS a.d. Beograd"


def _broj(v):
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
        tekst = f"{v:,.2f}" if not isinstance(v, int) else f"{v:,}"
        return tekst.replace(",", "X").replace(".", ",").replace("X", "."), True
    return ("" if v is None else str(v)), False


def tabela_pdf_response(filename, naslov, zaglavlje, redovi, *, podnaslov="", ukupno=None, sekcija="Izveštaj"):
    """`redovi` i `ukupno` su liste vrednosti istim redom kao `zaglavlje`; brojevi se poravnavaju desno."""
    from hr.services.analitika_pdf import _fontovi

    obican, podebljan = _fontovi()
    stranica = landscape(A4)
    izradjeno = timezone.localtime()
    sirina = stranica[0] - 24 * mm

    stil = ParagraphStyle("c", fontName=obican, fontSize=7.2, leading=8.6)
    stil_z = ParagraphStyle("z", parent=stil, fontName=podebljan, textColor=colors.white)
    stil_u = ParagraphStyle("u", parent=stil, fontName=podebljan)

    def celija(v, s):
        tekst, broj = _broj(v)
        return Paragraph(escape(tekst), ParagraphStyle("d", parent=s, alignment=2) if broj else s)

    podaci = [[Paragraph(escape(str(h)), stil_z) for h in zaglavlje]]
    podaci += [[celija(v, stil) for v in red] for red in redovi]
    if ukupno is not None:
        podaci.append([celija(v, stil_u) for v in ukupno])

    # Širine kolona: brojevi i reči zaglavlja se ne lome; ako tabela ne staje, sužavaju se samo tekstualne kolone.
    svi = list(redovi[:400]) + ([ukupno] if ukupno is not None else [])
    brojcane = [any(_broj(r[i])[1] for r in svi) for i in range(len(zaglavlje))]
    potrebno, najmanje = [], []
    for i, h in enumerate(zaglavlje):
        # +3: unutrašnja margina ćelije i podebljan tekst zaglavlja i reda UKUPNO
        reci = [str(h)] + ([str(ukupno[i])] if ukupno is not None and not _broj(ukupno[i])[1] else [])
        rec = max((len(w) for tekst in reci for w in tekst.split()), default=4) + 3
        najmanje.append(rec)
        sadrzaj = max([len(_broj(r[i])[0]) for r in svi] or [4]) + 3
        potrebno.append(max(rec, sadrzaj) if brojcane[i] else max(rec, min(sadrzaj, 60)))
    staje = sirina / 4.1  # približan broj znakova fonta 7,2 pt u širini strane
    visak = sum(potrebno) - staje
    if visak > 0:
        tekstualne = sum(p for p, b in zip(potrebno, brojcane) if not b) or 1
        potrebno = [p if b else max(m, p - visak * p / tekstualne) for p, b, m in zip(potrebno, brojcane, najmanje)]
    sirine = [sirina * d / sum(potrebno) for d in potrebno]

    tabela = Table(podaci, colWidths=sirine, repeatRows=1)
    stilovi = [("BACKGROUND", (0, 0), (-1, 0), PLAVA), ("VALIGN", (0, 0), (-1, -1), "TOP"),
               ("GRID", (0, 0), (-1, -1), 0.3, LINIJA), ("TOPPADDING", (0, 0), (-1, -1), 2),
               ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    for i in range(1, len(podaci)):
        if i % 2 == 0:
            stilovi.append(("BACKGROUND", (0, i), (-1, i), SVETLA))
    if ukupno is not None:
        stilovi.append(("BACKGROUND", (0, len(podaci) - 1), (-1, len(podaci) - 1), ZBIR))
    tabela.setStyle(TableStyle(stilovi))

    naslov_stil = ParagraphStyle("n", fontName=podebljan, fontSize=13, leading=16, textColor=PLAVA)
    pod_stil = ParagraphStyle("p", fontName=obican, fontSize=8, leading=10, textColor=SIVA)
    sadrzaj = [Paragraph(escape(naslov), naslov_stil)]
    if podnaslov:
        sadrzaj.append(Paragraph(escape(podnaslov), pod_stil))
    sadrzaj += [Paragraph(f"Izrađeno: {izradjeno:%d.%m.%Y. %H:%M}", pod_stil), Spacer(1, 4 * mm), tabela]

    class Platno(rl_canvas.Canvas):
        """„Strana x od y”: ukupan broj strana poznat je tek na kraju."""

        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._strane = []

        def showPage(self):
            self._strane.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            ukupno_strana = len(self._strane)
            for stanje in self._strane:
                self.__dict__.update(stanje)
                self.setFont(obican, 7)
                self.setFillColor(SIVA)
                self.drawString(12 * mm, 7 * mm, f"{INSTITUT} · {sekcija} · {naslov}"[:150])
                self.drawRightString(stranica[0] - 12 * mm, 7 * mm, f"Strana {self._pageNumber} od {ukupno_strana}")
                super().showPage()
            super().save()

    izlaz = BytesIO()
    SimpleDocTemplate(izlaz, pagesize=stranica, leftMargin=12 * mm, rightMargin=12 * mm, topMargin=12 * mm,
                      bottomMargin=14 * mm, title=naslov, author=INSTITUT).build(sadrzaj, canvasmaker=Platno)
    odgovor = HttpResponse(izlaz.getvalue(), content_type="application/pdf")
    odgovor["Content-Disposition"] = f'attachment; filename="{filename}"'
    return odgovor
