"""Meka veza: EUF faktura u Nabavci ↔ ulazna SEF faktura (Finansije, `finansije.SefFaktura`).

Nema stranog ključa ni kopije podataka: SEF faktura se traži pri prikazu, po istom broju
dokumenta (`kljuc_broja`) i istom PIB-u dobavljača kada su oba poznata. Provereno 02.10.2026.
na stvarnim podacima: 126 od 145 EUF faktura iz perioda SEF-a ima par, bez ijednog sukoba PIB-a
i bez više kandidata.
"""


def sef_faktura(invoice):
    """(SEF faktura ili None, broj kandidata). Kod više kandidata uzima se poslednja poslata."""
    from finansije.sef_models import SefFaktura, kljuc_broja

    kljuc = kljuc_broja(invoice.invoice_number)
    if not kljuc:
        return None, 0
    kandidati = list(SefFaktura.objects.filter(smer=SefFaktura.Smer.ULAZNA, broj_kljuc=kljuc)
                     .order_by("-datum_slanja", "-sef_id"))
    pib = (invoice.partner_pib or "").strip()
    if pib:
        kandidati = [f for f in kandidati if not (f.partner_pib or "").strip() or f.partner_pib.strip() == pib]
    return (kandidati[0] if kandidati else None), len(kandidati)
