
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User

import json
import re

from .models import (
    TipoRepuesto,
    Marca,
    Modelo,
    Repuesto,
    ModeloNotebook,
    Compatibilidad,
    EquivalenciaNuevo
)


# =========================================
# LIMPIAR MODELO
# =========================================
def limpiar_modelo(m):
    m = (m or "").strip().upper()

    # 🔴 BLOQUEO DIRECTO DE REPUESTOS
    palabras_prohibidas = ["BATERIA", "BATTERY", "PILA", "CELL"]
    for palabra in palabras_prohibidas:
        if palabra in m:
            return None

    marcas = ["HP", "DELL", "LENOVO", "ASUS", "ACER", "TOSHIBA", "SONY"]
    palabras_ruido = ["NOTEBOOK", "LAPTOP", "PARA", "COMPATIBLE", "SATELLITE", "ASPIRE", "TECRA", "PORTEGE", "DYNABOOK", "VAIO", "PRO", "SERIES"]

    partes = m.split()
    # eliminar palabras de repuesto dentro del texto
    partes = [p for p in partes if p not in ["BATERIA", "BATTERY", "CARGADOR", "TECLADO"]]

    if partes and partes[0] in marcas:
        partes = partes[1:]

    partes = [p for p in partes if p not in palabras_ruido]

    if not partes:
        return None

    m = " ".join(partes)
    m = m.replace(" ", "")

    if m.startswith("T") and any(c.isdigit() for c in m):
        m = "THINKPAD " + m

    # 🔴 EVITAR COSAS SOLO NUMÉRICAS (tipo 5251)
    if m.isdigit():
        return None

    if not any(c.isdigit() for c in m):
        return None

    return m

# =========================================
# LIMPIAR REPUESTOS
# =========================================
def limpiar_repuesto(texto):

    texto = (texto or "").upper()

    texto = texto.replace(",", " ").replace("\n", " ").replace(":", " ")

    palabras = texto.split()

    resultado = set()

    for p in palabras:

        p = p.strip()

        if p in [
            "BATERIA", "BATTERY", "PARA", "NOTEBOOK",
            "LAPTOP", "COMPATIBLE", "ORIGINAL"
        ]:
            continue

        if len(p) < 4:
            continue
        
        
        if not any(c.isdigit() for c in p):
            continue

        if not any(c.isalpha() for c in p):
            continue

        if re.match(r"^[A-Z0-9\-]+$", p):

            if re.match(r"^\d{2}-[A-Z]{2}", p):
                continue

            resultado.add(p)

    return list(resultado)

# =========================================
# DETECTOR DE MODELOS
# =========================================
def detectar_modelos(texto):

    texto = (texto or "").upper()

    marca = "DESCONOCIDA"

    if "HP" in texto:
        marca = "HP"
    elif "DELL" in texto:
        marca = "DELL"
    elif "LENOVO" in texto:
        marca = "LENOVO"
    elif "ASUS" in texto:
        marca = "ASUS"
    elif "ACER" in texto:
        marca = "ACER"
    elif "TOSHIBA" in texto:
        marca = "TOSHIBA"
    elif "SONY" in texto or "VAIO" in texto:
        marca = "SONY"

    modelos = set()

    patron = re.findall(
        r"\b[A-Z0-9]+(?:-[A-Z0-9]+)+\b|\b[A-Z]{1,2}\d{2,4}\b",
        texto
    )

    for m in patron:

        if m.isdigit():
            continue

        if len(m) <= 2:
            continue

        m = limpiar_modelo(m)

        if not m:
            continue

        if len(m) > 25:
            continue

        if m.count("-") > 3:
            continue

        if not any(c.isdigit() for c in m):
            continue

        modelos.add(m)

    return [(marca, m) for m in modelos]


# =========================================
# VISTA PRINCIPAL
# =========================================
def nuevo_repuesto(request):

    if request.method == "POST":

        # ==============================
        # DATOS
        # ==============================
        tipo_nombre = request.POST.get("tipo", "").strip().upper()
        marca_nombre = request.POST.get("marca", "").strip().upper()
        modelo_nombre = request.POST.get("modelo", "").strip().upper()
        descripcion = request.POST.get("descripcion", "").strip().upper()
        precio_compra = request.POST.get("precio_compra")
        precio_venta = request.POST.get("precio_venta")
        texto = request.POST.get("texto")
        equivalencias_json = request.POST.get("equivalencias")
        print("EQUIVALENCIAS RAW:", equivalencias_json)

        if not descripcion:
            return JsonResponse({"error": "Descripción requerida"})
        if not modelo_nombre:
            return JsonResponse({"error": "Modelo requerido"})

        if not tipo_nombre:
            tipo_nombre = "GENERAL"

        if not marca_nombre:
            marca_nombre = "GENERICO"

        if not modelo_nombre:
            modelo_nombre = "GENERAL"

        # ==============================
        # CREAR BASE
        # ==============================
        tipo, _ = TipoRepuesto.objects.get_or_create(nombre=tipo_nombre)

        marca_obj, _ = Marca.objects.get_or_create(
            nombre=marca_nombre,
            tipo=tipo
        )

        modelo, _ = Modelo.objects.get_or_create(
            nombre=modelo_nombre,
            marca=marca_obj
        )

        # ==============================
        # PRECIOS
        # ==============================
        try:
            precio_compra = float(precio_compra) if precio_compra else None
        except:
            precio_compra = None

        try:
            precio_venta = float(precio_venta) if precio_venta else None
        except:
            precio_venta = None

        # ==============================
        # REPUESTO
        # ==============================
        repuesto_existente = Repuesto.objects.filter(
            tipo=tipo,
            modelo=modelo,
            descripcion=descripcion
        ).first()

        if repuesto_existente:
            return JsonResponse({
                "error": "Este repuesto ya existe"
        })

        repuesto = Repuesto.objects.create(
            tipo=tipo,
            modelo=modelo,
            descripcion=descripcion,
            precio_compra=precio_compra,
            precio_venta=precio_venta
        )

        
        # ==============================
        # DETECTAR MODELOS
        # ==============================
        try:
            datos = json.loads(texto) if texto else []
            modelos_detectados = [(d["marca"], d["modelo"]) for d in datos]
        except:
            modelos_detectados = detectar_modelos(texto or "")

        # ==============================
        # COMPATIBILIDADES
        # ==============================
        for marca_nb, modelo_nb_texto in modelos_detectados:

            if not marca_nb or not modelo_nb_texto:
                continue

            marca_nb_obj, _ = Marca.objects.get_or_create(nombre=marca_nb)

            modelo_nb_obj, _ = ModeloNotebook.objects.get_or_create(
                marca=marca_nb_obj,
                modelo=modelo_nb_texto
            )

            Compatibilidad.objects.get_or_create(
                repuesto=repuesto,
                modelo_notebook=modelo_nb_obj
            )

        # ==============================
        # EQUIVALENCIAS
        # ==============================
        equivalencias = limpiar_repuesto(equivalencias_json)

        for eq in equivalencias:

            EquivalenciaNuevo.objects.get_or_create(
                repuesto=repuesto,
                codigo_equivalente=eq
            )

        return JsonResponse({"ok": True})

    # ==============================
    # GET
    # ==============================
    tipos = TipoRepuesto.objects.all()
    modelos = Modelo.objects.all()
    marcas = Marca.objects.all()

    return render(request, "nuevo_repuesto.html", {
        "tipos": tipos,
        "modelos": modelos,
        "marcas": marcas
    })


# =========================================
# API DETECCION
# =========================================
def detectar_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        texto = data.get("texto", "")

        modelos = detectar_modelos(texto)

        marca_form = data.get("marca", "").strip().upper()

        modelos = [
            (marca_form if m[0] == "DESCONOCIDA" and marca_form else m[0], m[1])
            for m in modelos
        ]

        resultado = [
            {"marca": m[0], "modelo": m[1]}
            for m in modelos
        ]

        return JsonResponse({"modelos": resultado})


# =========================================
# CREAR ADMIN
# =========================================
def crear_admin(request):
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@email.com",
            password="12345678"
        )
        return HttpResponse("Usuario admin creado")
    return HttpResponse("El usuario ya existe")