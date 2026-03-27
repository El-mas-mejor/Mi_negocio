from django.db import models

class EquivalenciaNuevo(models.Model):
    repuesto = models.ForeignKey("Repuesto", on_delete=models.CASCADE)
    codigo_equivalente = models.CharField(max_length=120)

    class Meta:
        unique_together = ('repuesto', 'codigo_equivalente')
        
    def __str__(self):
        return f"{self.repuesto.descripcion} -> {self.codigo_equivalente}"
class TipoRepuesto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.ForeignKey(TipoRepuesto, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('nombre', 'tipo')

    def __str__(self):
        return f"{self.nombre} - {self.tipo.nombre}"


class Modelo(models.Model):
    nombre = models.CharField(max_length=100)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('nombre', 'marca')

    def __str__(self):
        return f"{self.nombre} - {self.marca.nombre}"


class ModeloNotebook(models.Model):
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)

    class Meta:
        unique_together = ('marca', 'modelo')

    def __str__(self):
        return f"{self.marca} {self.modelo}"


class Repuesto(models.Model):
    tipo = models.ForeignKey(TipoRepuesto, on_delete=models.CASCADE)
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=200, blank=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)

    modelos_notebook = models.ManyToManyField(
        ModeloNotebook,
        through='Compatibilidad'
    )

    def __str__(self):
        return f"{self.modelo} - {self.descripcion}"


class Compatibilidad(models.Model):
    repuesto = models.ForeignKey("Repuesto", on_delete=models.CASCADE)
    modelo_notebook = models.ForeignKey(ModeloNotebook, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('repuesto', 'modelo_notebook')
        verbose_name = "Compatibilidad"
        verbose_name_plural = "Compatibilidades"

    def __str__(self):
        return f"{self.repuesto} -> {self.modelo_notebook}"
    
  