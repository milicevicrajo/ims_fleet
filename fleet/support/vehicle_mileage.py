"""Observed odometer readings and non-overlapping intervals near 30 days."""
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django import forms
from django.urls import reverse
from django.utils import timezone

from fleet.models import FuelConsumption, TransactionNIS, TransactionOMV, VehicleTravelOrder


class MileagePeriodForm(forms.Form):
    mileage_from = forms.DateField(label='Očitavanja od', required=False, widget=forms.DateInput(format='%Y-%m-%d', attrs={'type':'date','data-native-date':'true'}))
    mileage_to = forms.DateField(label='Očitavanja do', required=False, widget=forms.DateInput(format='%Y-%m-%d', attrs={'type':'date','data-native-date':'true'}))

    def clean(self):
        data=super().clean()
        start,end=data.get('mileage_from'),data.get('mileage_to')
        if start and end and start > end:
            raise forms.ValidationError('Početak perioda ne može biti posle završetka.')
        return data


def observed_timeline(readings):
    """Use one daily maximum; a decrease anywhere inside an interval blocks its distance."""
    grouped=defaultdict(list)
    for reading in readings:
        grouped[reading['date']].append(reading)
    days=[]
    for day,items in sorted(grouped.items()):
        minimum,maximum=min(r['value'] for r in items),max(r['value'] for r in items)
        days.append(dict(date=day,minimum=minimum,value=maximum,
            source='; '.join(sorted({r['source'] for r in items if r['value']==maximum})),
            count=len(items), readings=items))
    intervals=[]
    anchor=0
    while anchor < len(days)-1:
        target=days[anchor]['date']+timedelta(days=30)
        end=min(range(anchor+1,len(days)),key=lambda i:(abs((days[i]['date']-target).days),days[i]['date']))
        first,last=days[anchor],days[end]
        decreases=[days[i]['date'] for i in range(anchor+1,end+1) if days[i]['minimum'] < days[i-1]['value']]
        intervals.append(dict(start=first['date'],end=last['date'],days=(last['date']-first['date']).days,
            start_value=first['value'],end_value=last['value'],start_source=first['source'],end_source=last['source'],
            km=None if decreases else last['value']-first['value'],issues=decreases,count=sum(d['count'] for d in days[anchor:end+1])))
        anchor=end
    current=days[-1].copy() if days else None
    if current:
        current['needs_check']=len(days)>1 and current['minimum'] < days[-2]['value']
    return dict(days=days,intervals=list(reversed(intervals)),current=current,
        issue_count=sum(bool(i['issues']) for i in intervals),
        total_km=sum((i['km'] for i in intervals),Decimal('0')) if intervals and not any(i['issues'] for i in intervals) else None)


def vehicle_mileage(vehicle, params=None, today=None):
    today=today or timezone.localdate()
    readings=[]
    excluded=0

    def add(day,value,source,reference='',url=None,allow_zero=False,original_value=None):
        nonlocal excluded
        if isinstance(day,datetime):
            day=timezone.localtime(day).date() if timezone.is_aware(day) else day.date()
        try:
            number=Decimal(str(value)) if value is not None else None
        except (InvalidOperation,ValueError):
            number=None
        if not day or day>today or number is None or not number.is_finite() or number<0 or (number==0 and not allow_zero):
            if value is not None: excluded+=1
            return
        readings.append(dict(date=day,value=number,source=source,reference=reference,url=url,original_value=original_value))

    for row in TransactionNIS.objects.filter(vehicle=vehicle).values('datum_transakcije','kilometraza','broj_racuna'):
        add(row['datum_transakcije'],row['kilometraza'],'NIS — točenje',row['broj_racuna'])
    for row in TransactionOMV.objects.filter(vehicle=vehicle).values('transaction_date','mileage','corrected_mileage','voucher','invoice_no'):
        corrected=row['corrected_mileage']
        use_corrected=corrected is not None and corrected>0
        add(row['transaction_date'],corrected if use_corrected else row['mileage'],
            'OMV — korigovano u izvoru' if use_corrected else 'OMV — točenje',row['voucher'] or row['invoice_no'] or '',
            original_value=row['mileage'] if use_corrected and row['mileage'] != corrected else None)
    direct_days={r['date'] for r in readings}
    for row in FuelConsumption.objects.filter(vehicle=vehicle).values('date','mileage','supplier'):
        day=timezone.localtime(row['date']).date() if timezone.is_aware(row['date']) else row['date'].date()
        if day not in direct_days:
            add(day,row['mileage'],'Ranija evidencija goriva',row['supplier'])
    for order in VehicleTravelOrder.objects.filter(vehicle=vehicle).values('pk','pn_number','rbz','created_at','closed_at','start_mileage','end_mileage'):
        url=reverse('vehicle_travel_order_detail',args=[order['pk']])
        ref=f'PN {order["pn_number"] or "—"} · {order["rbz"] or ""}'
        add(order['created_at'],order['start_mileage'],'Nalog vozila — početak',ref,url,allow_zero=True)
        add(order['closed_at'],order['end_mileage'],'Nalog vozila — završetak',ref,url,allow_zero=True)
    readings.sort(key=lambda r:(r['date'],r['value'],r['source']),reverse=True)
    complete=observed_timeline(readings)
    bound=params is not None and ('mileage_from' in params or 'mileage_to' in params)
    form=MileagePeriodForm(params if bound else None,initial={'mileage_from':min((r['date'] for r in readings),default=None),'mileage_to':today})
    valid=not bound or form.is_valid()
    selected=readings
    if bound and valid:
        start,end=form.cleaned_data.get('mileage_from'),form.cleaned_data.get('mileage_to')
        selected=[r for r in readings if (not start or r['date']>=start) and (not end or r['date']<=end)]
    if not valid:selected=[]
    result=observed_timeline(selected)
    result.update(current=complete['current'],readings=selected,form=form,valid=valid,excluded=excluded,
        coverage_start=min((r['date'] for r in selected),default=None),coverage_end=max((r['date'] for r in selected),default=None))
    return result
