from django.contrib import admin
from django.urls import path
from clientes.views import nuevo_repuesto
from clientes.views import detectar_api
from clientes.views import crear_admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('nuevo/', nuevo_repuesto, name='nuevo_repuesto'),
    path('detectar/', detectar_api),
    path('crear-admin/', crear_admin),
]
