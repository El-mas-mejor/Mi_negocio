
from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import re
from .models import TipoRepuesto, Marca, Modelo, Repuesto, ModeloNotebook, Compatibilidad, Equivalencia
def limpiar_modelo(m):
    m = (m or "").strip().upper()
    print("MODELO ORIGINAL:", m)

    marcas = ["HP", "DELL", "LENOVO", "ASUS", "ACER"]
    palabras_ruido = ["NOTEBOOK", "LAPTOP", "BATERIA", "BATTERY", "PARA", "COMPATIBLE"]

    partes = m.split()

    if partes and partes[0] in marcas:
        partes = partes[1:]

    partes = [p for p in partes if p not in palabras_ruido]

    if not partes:
        return None

    m = " ".join(partes)

    m = m.replace(" ", "")

    if m.startswith("T") and any(c.isdigit() for c in m):
        m = "THINKPAD " + m

    if not any(c.isdigit() for c in m):
        return None

    print("MODELO LIMPIO:", m)
    return m




def nuevo_repuesto(request):

    if request.method == "POST":

        
        # ==============================
        # CAPTURA DE DATOS
        # ==============================
        tipo_nombre = request.POST.get("tipo", "").strip().upper()
        marca_nombre = request.POST.get("marca", "").strip().upper()
        modelo_nombre = request.POST.get("modelo", "").strip().upper()
        descripcion = request.POST.get("descripcion", "").strip().upper()
        precio_compra = request.POST.get("precio_compra")
        precio_venta = request.POST.get("precio_venta")
        texto = request.POST.get("texto")
        equivalencias_json = request.POST.get("equivalencias")
        equivalencias_json = request.POST.get("equivalencias")
        print("EQUIVALENCIAS RECIBIDAS:", equivalencias_json)
        if not descripcion:
            return JsonResponse({"error": "Descripción requerida"})
        if not modelo_nombre:
            return JsonResponse({"error": "Modelo requerido"})

        # ==============================
        # VALORES POR DEFECTO
        # ==============================
        if not tipo_nombre:
            tipo_nombre = "GENERAL"

        if not marca_nombre:
            marca_nombre = "GENERICO"

        if not modelo_nombre:
            modelo_nombre = "GENERAL"

        # ==============================
        # CREAR TIPO
        # ==============================
        tipo, _ = TipoRepuesto.objects.get_or_create(
            nombre=tipo_nombre
        )

        # ==============================
        # CREAR MARCA
        # ==============================
        marca_obj, _ = Marca.objects.get_or_create(
            nombre=marca_nombre,
            tipo=tipo
        )

        # ==============================
        # CREAR MODELO
        # ==============================
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
        # REPUESTO (SIN DUPLICAR)
        # ==============================
        repuesto = Repuesto.objects.filter(
            tipo=tipo,
            modelo=modelo,
            descripcion=descripcion
        ).first()

        if not repuesto:
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
        except Exception as e:
            print("ERROR JSON:", e)
            modelos_detectados = detectar_modelos(texto or "")

# ==============================
# GUARDAR EQUIVALENCIAS
# ==============================

    try:
        equivalencias = json.loads(equivalencias_json) if equivalencias_json else []
    except:
        equivalencias = []

    for eq in equivalencias:

        eq = (eq or "").strip().upper()

        if not eq:
          continue

    # evitar duplicados
        if not Equivalencia.objects.filter(repuesto=repuesto, codigo_equivalente=eq).exists():

            Equivalencia.objects.create(
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

    modelos = set()

    patron = re.findall(r"\b[A-Z0-9]{3,}(?:-[A-Z0-9]+)*\b", texto)

    for m in patron:
         #  FILTROS ANTES DE LIMPIAR
        if m.isdigit():
            continue

        if len(m) <= 4 and not any(c.isalpha() for c in m):
            continue

        # limpiar modelos
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
# API DETECCION
# =========================================
def detectar_api(request):
    if request.method == "POST":
        data = json.loads(request.body)
        texto = data.get("texto", "")

        modelos = detectar_modelos(texto)

        # 🔥 reemplazar marca desconocida por la del form
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
    