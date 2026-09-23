from django.urls import path

from . import views, views_disciplinski

app_name = "pravna"

urlpatterns = [
    path('disciplinski/', views_disciplinski.disciplinski_lista, name='disciplinski_lista'),
    path('disciplinski/izvestaj/', views_disciplinski.disciplinski_izvestaj, name='disciplinski_izvestaj'),
    path('disciplinski/dodaj/', views_disciplinski.disciplinski_dodaj, name='disciplinski_dodaj'),
    path('disciplinski/<int:pk>/', views_disciplinski.disciplinski_detalj, name='disciplinski_detalj'),
    path('disciplinski/<int:pk>/izmeni/', views_disciplinski.disciplinski_izmeni, name='disciplinski_izmeni'),
    path('disciplinski/<int:pk>/obrisi/', views_disciplinski.disciplinski_obrisi, name='disciplinski_obrisi'),
    path('disciplinski/<int:pk>/arhiviraj/', views_disciplinski.disciplinski_arhiviraj, name='disciplinski_arhiviraj'),
    path('disciplinski/<int:pk>/mera/', views_disciplinski.disciplinski_mera, name='disciplinski_mera'),
    path('disciplinski/<int:pk>/dodaj-tok/', views_disciplinski.disciplinski_dodaj_tok, name='disciplinski_dodaj_tok'),
    path('disciplinski/tok/<int:pk>/obrisi/', views_disciplinski.disciplinski_obrisi_tok, name='disciplinski_obrisi_tok'),

    path('postupak/<int:pk>/', views.detalj, name='detalj'),
    path('postupak/<int:pk>/izmeni/', views.izmeni, name='izmeni'),
    path('postupak/<int:pk>/obrisi/', views.obrisi, name='obrisi'),
    path('postupak/<int:pk>/arhiviraj/', views.arhiviraj, name='arhiviraj'),
    path('postupak/<int:pk>/dodaj-promenu/', views.dodaj_promenu, name='dodaj_promenu'),
    path('promena/<int:pk>/obrisi/', views.obrisi_promenu, name='obrisi_promenu'),

    path('<str:case_type>/', views.cases_list, name='cases_list'),
    path('<str:case_type>/izvestaj/', views.izvestaj, name='izvestaj'),
    path('<str:case_type>/izvestaj/excel/', views.izvestaj_excel, name='izvestaj_excel'),
    path('<str:case_type>/dodaj/', views.dodaj, name='dodaj'),
]
