"""Disciplinski postupci - ista pravila prikaza kao ostatak pravne sluzbe."""
from datetime import datetime

from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from core.mixins import role_permission_required, user_has_role_permission

from .forms import DISCIPLINSKI_COLUMNS, DisciplinskaMeraForm, DisciplinskiPostupakForm, TokPostupkaForm
from .models import DisciplinskiPostupak, TokPostupka


def _filtered_context(request):
    """Isti oblik filtera kao kod ostalih postupaka: arhiva plus dve liste izbora."""
    show_archived = request.GET.get('arhivirano') == '1'
    base_qs = DisciplinskiPostupak.objects.select_related('zaposleni', 'podnosilac')
    if not show_archived:
        base_qs = base_qs.filter(arhivirano=False)

    selected_zaposleni = (request.GET.get('zaposleni') or '').strip()
    selected_centar = (request.GET.get('centar') or '').strip()
    selected_status = (request.GET.get('status') or '').strip()

    zaposleni_options = [
        {'pk': row.pk, 'naziv': str(row)}
        for row in sorted(
            {p.zaposleni for p in base_qs},
            key=lambda e: (e.display_last_name, e.display_first_name),
        )
    ]
    centar_options = sorted({(p.centar or '').strip() for p in base_qs if (p.centar or '').strip()})

    qs = base_qs
    if selected_zaposleni:
        try:
            qs = qs.filter(zaposleni_id=int(selected_zaposleni))
        except ValueError:
            selected_zaposleni = ''
    if selected_centar:
        qs = qs.filter(centar=selected_centar)
    if selected_status == 'zatvoreni':
        qs = qs.filter(mera_datum__isnull=False)
    elif selected_status == 'aktivni':
        qs = qs.filter(mera_datum__isnull=True)

    return {
        'qs': qs,
        'show_archived': show_archived,
        'selected_zaposleni': selected_zaposleni,
        'selected_centar': selected_centar,
        'selected_status': selected_status,
        'zaposleni_options': zaposleni_options,
        'centar_options': centar_options,
    }


@never_cache
@role_permission_required()
def disciplinski_lista(request):
    request.session['current_app'] = 'pravna'
    ctx = _filtered_context(request)

    return render(request, 'pravna/disciplinski_lista.html', {
        'title': 'Pravna služba - Disciplinski postupci',
        'postupci': ctx['qs'].annotate(tok_count=Count('tok')),
        'columns': DISCIPLINSKI_COLUMNS,
        'show_archived': ctx['show_archived'],
        'selected_zaposleni': ctx['selected_zaposleni'],
        'selected_centar': ctx['selected_centar'],
        'selected_status': ctx['selected_status'],
        'zaposleni_options': ctx['zaposleni_options'],
        'centar_options': ctx['centar_options'],
        'can_add': user_has_role_permission(request.user, 'pravna:disciplinski_dodaj'),
        'can_delete': user_has_role_permission(request.user, 'pravna:disciplinski_obrisi'),
    })


@never_cache
@role_permission_required()
def disciplinski_izvestaj(request):
    request.session['current_app'] = 'pravna'
    ctx = _filtered_context(request)
    postupci = list(
        ctx['qs'].prefetch_related('tok').order_by('centar', 'zaposleni__last_name', 'zaposleni__first_name', 'id')
    )

    groups = {}
    for postupak in postupci:
        key = postupak.centar or 'Bez centra'
        groups.setdefault(key, {'centar': key, 'postupci': []})
        groups[key]['postupci'].append({'postupak': postupak, 'tok': list(postupak.tok.all())})

    filter_badges = []
    if ctx['selected_zaposleni']:
        match = next((o for o in ctx['zaposleni_options'] if str(o['pk']) == ctx['selected_zaposleni']), None)
        filter_badges.append(f"Zaposleni: {match['naziv'] if match else ctx['selected_zaposleni']}")
    if ctx['selected_centar']:
        filter_badges.append(f"Centar: {ctx['selected_centar']}")
    if ctx['selected_status']:
        filter_badges.append(f"Status: {'Zatvoreni' if ctx['selected_status'] == 'zatvoreni' else 'Aktivni'}")
    filter_badges.append('Arhivirano: ukljuceno' if ctx['show_archived'] else 'Arhivirano: iskljuceno')

    return render(request, 'pravna/disciplinski_izvestaj.html', {
        'title': 'Izvestaj - Pravna sluzba - Disciplinski postupci',
        'report_date': datetime.now(),
        'groups': list(groups.values()),
        'filter_badges': filter_badges,
        'total_postupci': len(postupci),
    })


def _detalj_context(request, postupak, forma_mera=None):
    return {
        'title': f'Disciplinski postupak - {postupak.zaposleni}',
        'postupak': postupak,
        'tok': postupak.tok.all(),
        'forma_tok': TokPostupkaForm(),
        'forma_mera': forma_mera or DisciplinskaMeraForm(instance=postupak),
        'can_edit': user_has_role_permission(request.user, 'pravna:disciplinski_izmeni'),
        'can_archive': user_has_role_permission(request.user, 'pravna:disciplinski_arhiviraj'),
        'can_add_tok': user_has_role_permission(request.user, 'pravna:disciplinski_dodaj_tok'),
        'can_delete_tok': user_has_role_permission(request.user, 'pravna:disciplinski_obrisi_tok'),
        'can_mera': user_has_role_permission(request.user, 'pravna:disciplinski_mera'),
    }


@never_cache
@role_permission_required()
def disciplinski_detalj(request, pk):
    request.session['current_app'] = 'pravna'
    postupak = get_object_or_404(
        DisciplinskiPostupak.objects.select_related('zaposleni', 'podnosilac'), pk=pk
    )
    return render(request, 'pravna/disciplinski_detalj.html', _detalj_context(request, postupak))


@role_permission_required()
def disciplinski_dodaj(request):
    request.session['current_app'] = 'pravna'
    if request.method == 'POST':
        form = DisciplinskiPostupakForm(request.POST)
        if form.is_valid():
            postupak = form.save(commit=False)
            postupak.created_by = request.user
            postupak.save()
            return redirect('pravna:disciplinski_detalj', pk=postupak.pk)
    else:
        form = DisciplinskiPostupakForm()

    return render(request, 'pravna/disciplinski_forma.html', {
        'title': 'Novi disciplinski postupak',
        'form': form,
    })


@role_permission_required()
def disciplinski_izmeni(request, pk):
    request.session['current_app'] = 'pravna'
    postupak = get_object_or_404(DisciplinskiPostupak, pk=pk)

    if request.method == 'POST':
        form = DisciplinskiPostupakForm(request.POST, instance=postupak)
        if form.is_valid():
            form.save()
            return redirect('pravna:disciplinski_detalj', pk=pk)
    else:
        form = DisciplinskiPostupakForm(instance=postupak)

    return render(request, 'pravna/disciplinski_forma.html', {
        'title': f'Izmeni - {postupak.zaposleni}',
        'form': form,
        'postupak': postupak,
    })


@role_permission_required()
def disciplinski_obrisi(request, pk):
    postupak = get_object_or_404(DisciplinskiPostupak, pk=pk)
    if request.method == 'POST':
        postupak.delete()
        return redirect('pravna:disciplinski_lista')
    return redirect('pravna:disciplinski_detalj', pk=pk)


@role_permission_required()
def disciplinski_arhiviraj(request, pk):
    postupak = get_object_or_404(DisciplinskiPostupak, pk=pk)
    if request.method == 'POST':
        postupak.arhivirano = not postupak.arhivirano
        postupak.save(update_fields=['arhivirano', 'updated_at'])
    return redirect('pravna:disciplinski_detalj', pk=pk)


@role_permission_required()
def disciplinski_dodaj_tok(request, pk):
    postupak = get_object_or_404(DisciplinskiPostupak, pk=pk)

    if request.method == 'POST':
        form = TokPostupkaForm(request.POST)
        if form.is_valid():
            zapis = form.save(commit=False)
            zapis.postupak = postupak
            zapis.created_by = request.user
            zapis.save()
    return redirect('pravna:disciplinski_detalj', pk=pk)


@role_permission_required()
def disciplinski_obrisi_tok(request, pk):
    zapis = get_object_or_404(TokPostupka, pk=pk)
    postupak_pk = zapis.postupak_id
    if request.method == 'POST':
        zapis.delete()
    return redirect('pravna:disciplinski_detalj', pk=postupak_pk)


@role_permission_required()
def disciplinski_mera(request, pk):
    """Disciplinska mera zatvara postupak. Ponisti mere ga vraca u rad."""
    postupak = get_object_or_404(DisciplinskiPostupak, pk=pk)

    if request.method == 'POST':
        if request.POST.get('ponisti') == '1':
            postupak.mera_datum = None
            postupak.mera_opis = ''
            postupak.save(update_fields=['mera_datum', 'mera_opis', 'updated_at'])
            return redirect('pravna:disciplinski_detalj', pk=pk)

        form = DisciplinskaMeraForm(request.POST, instance=postupak)
        if form.is_valid():
            form.save()
            return redirect('pravna:disciplinski_detalj', pk=pk)

        # Neispravna forma je vec upisala datum u instancu, pa bi postupak izgledao
        # zatvoreno iako nista nije sacuvano. Prikazuje se stanje iz baze.
        request.session['current_app'] = 'pravna'
        sacuvani = get_object_or_404(
            DisciplinskiPostupak.objects.select_related('zaposleni', 'podnosilac'), pk=pk
        )
        return render(request, 'pravna/disciplinski_detalj.html',
                      _detalj_context(request, sacuvani, forma_mera=form))
    return redirect('pravna:disciplinski_detalj', pk=pk)
