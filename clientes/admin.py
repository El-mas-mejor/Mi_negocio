from django.contrib import admin
from django import forms
from .models import (
    TipoRepuesto,
    Marca,
    Modelo,
    ModeloNotebook,
    Repuesto,
    Compatibilidad,
    Equivalencia
)


# 🔹 FORM personalizado
class RepuestoForm(forms.ModelForm):
    texto_compatibilidad = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
        label="Pegar compatibilidad"
    )

    class Meta:
        model = Repuesto
        fields = '__all__'


# 🔹 Inline
class CompatibilidadInline(admin.TabularInline):
    model = Compatibilidad
    extra = 0


# 🔹 ADMIN
class RepuestoAdmin(admin.ModelAdmin):
    form = RepuestoForm
    inlines = [CompatibilidadInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        texto = form.cleaned_data.get("texto_compatibilidad")

        if texto:
            modelos = detectar_modelos(texto)

            for marca, modelo in modelos:
                mn, _ = ModeloNotebook.objects.get_or_create(
                    marca=marca,
                    modelo=modelo
                )

                Compatibilidad.objects.get_or_create(
                    repuesto=obj,
                    modelo_notebook=mn
                )


# 🔥 TU LÓGICA ADAPTADA
def detectar_modelos(texto):
    texto = texto.replace("\n", " ").replace(",", " ").replace(":", " ")

    marca = "Desconocida"

    if "HP" in texto.upper():
        marca = "HP"
    elif "DELL" in texto.upper():
        marca = "Dell"
    elif "LENOVO" in texto.upper():
        marca = "Lenovo"
    elif "ASUS" in texto.upper():
        marca = "Asus"
    elif "ACER" in texto.upper():
        marca = "Acer"

    palabras = texto.split()
    modelos = []

    for i, palabra in enumerate(palabras):

        palabra = palabra.strip()

        # tipo 14-CE0020TX
        if any(c.isdigit() for c in palabra) and "-" in palabra:
            modelos.append((marca, palabra))

        # tipo 240 G7
        if palabra.isdigit():
            if i < len(palabras) - 1:
                if palabras[i + 1].upper().startswith("G"):
                    modelo = palabra + " " + palabras[i + 1]
                    modelos.append((marca, modelo))

    return modelos

from .models import Equivalencia

admin.site.register(TipoRepuesto)
admin.site.register(Marca)
admin.site.register(Modelo)
admin.site.register(ModeloNotebook)
admin.site.register(Repuesto, RepuestoAdmin)
admin.site.register(Compatibilidad)
admin.site.register(Equivalencia)