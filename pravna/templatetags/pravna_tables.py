from django import template

register = template.Library()


# Sirina i ponasanje kolone u tabelama pravne sluzbe. Sto nije navedeno dobija
# podrazumevanu sirinu i prelama se, da tabela ne bi izasla iz kartice.
COLUMN_CLASSES = {
    'sifra_partnera': 'legal-col-xs legal-nowrap',
    'valuta': 'legal-col-xs legal-nowrap',
    'pib': 'legal-col-sm legal-nowrap',
    'broj_predmeta': 'legal-col-sm legal-nowrap',
    'izvrsiteljski_broj': 'legal-col-sm legal-nowrap',
    'novi_broj': 'legal-col-sm legal-nowrap',
    'vece': 'legal-col-sm',
    'datum_pokretanja': 'legal-col-date legal-nowrap',
    'datum_podnosenja_tuzbe': 'legal-col-date legal-nowrap',
    'datum_otvaranja_stecaja': 'legal-col-date legal-nowrap',
    'osnovni_dug': 'legal-col-num legal-nowrap',
    'vrednost_spora': 'legal-col-num legal-nowrap',
    'kamata': 'legal-col-num legal-nowrap',
    'troskovi': 'legal-col-num legal-nowrap',
    'ukupan_dug': 'legal-col-num legal-nowrap',
    'predmet_spora': 'legal-col-text',
    'prijava_potrazivanja': 'legal-col-text',
    'sud': 'legal-col-wide',
    'naziv_partnera': 'legal-col-wide',
    'tuzilac': 'legal-col-wide',
    'zaposleni': 'legal-col-wide',
    'podnosilac': 'legal-col-wide',
    'centar': 'legal-col-xs legal-nowrap',
    'datum_podnosenja': 'legal-col-date legal-nowrap',
    'mera_datum': 'legal-col-date legal-nowrap',
    'mera_opis': 'legal-col-text',
}


@register.simple_tag
def legal_columns(columns):
    """Kolonama iz COLUMNS_BY_TIP dodaje razred za sirinu i prelamanje."""
    return [
        {'key': key, 'title': title, 'css': COLUMN_CLASSES.get(key, '')}
        for key, title in columns
    ]
