from django.urls import path

from . import views

app_name = "relatorios"

urlpatterns = [
    path("", views.PainelView.as_view(), name="painel"),
    path("exportar/excel/", views.ExportarExcelView.as_view(), name="exportar_excel"),
    path("exportar/pdf/", views.ExportarPDFView.as_view(), name="exportar_pdf"),
]
