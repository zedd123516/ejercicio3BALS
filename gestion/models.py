from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class Agencia(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    ruc = models.CharField(max_length=13, unique=True)
    telefono = models.CharField(max_length=15)

    def __str__(self):
        return self.nombre


class Proyecto(models.Model):
    id = models.AutoField(primary_key=True)
    nombre_proyecto = models.CharField(max_length=150)
    ubicacion = models.CharField(max_length=200)
    agencia = models.ForeignKey(Agencia, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre_proyecto


class Bloque(models.Model):
    id = models.AutoField(primary_key=True)
    nombre_bloque = models.CharField(max_length=50)
    pisos = models.IntegerField()
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre_bloque


class Habitacion(models.Model):
    ESTADOS = (
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('mantenimiento', 'Mantenimiento'),
    )

    id = models.AutoField(primary_key=True)
    numero = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=50)
    capacidad = models.IntegerField(default=2)
    precio_noche = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    piso = models.IntegerField(default=1)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible')
    imagen = models.ImageField(
        upload_to='habitaciones/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )

    def __str__(self):
        return f"Habitación {self.numero}"


class Huesped(models.Model):
    id = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    documento = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    nacionalidad = models.CharField(max_length=50, default='Ecuador')

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class Reserva(models.Model):
    ESTADOS = (
        ('confirmada', 'Confirmada'),
        ('checked_in', 'Check-in'),
        ('checked_out', 'Check-out'),
        ('cancelada', 'Cancelada'),
    )
    CANALES = (
        ('directo', 'Directo'),
        ('booking', 'Booking'),
        ('agencia', 'Agencia'),
        ('corporativo', 'Corporativo'),
    )

    id = models.AutoField(primary_key=True)
    huesped = models.ForeignKey(Huesped, on_delete=models.CASCADE)
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE)
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='confirmada')
    numero_huespedes = models.IntegerField(default=1)
    canal_origen = models.CharField(max_length=20, choices=CANALES, default='directo')
    tarifa_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Reserva {self.id} - {self.huesped}"


class ServicioExtra(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class ReservaServicio(models.Model):
    id = models.AutoField(primary_key=True)
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='servicios')
    servicio = models.ForeignKey(ServicioExtra, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.reserva.id} - {self.servicio.nombre}"


class AmaDeLlaves(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    turno = models.CharField(max_length=50)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    piso_asignado = models.IntegerField(default=1)

    def __str__(self):
        return self.nombre


class Factura(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada'),
    )

    id = models.AutoField(primary_key=True)
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE)
    numero_factura = models.CharField(max_length=20, unique=True)
    fecha_emision = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    metodo_pago = models.CharField(max_length=50, default='Efectivo')

    def __str__(self):
        return self.numero_factura

class UsuarioCliente(models.Model):
    """Modelo extendido de Usuario para clientes"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_cliente')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    nacionalidad = models.CharField(max_length=50, default='Ecuador')
    documento = models.CharField(max_length=20, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cliente: {self.usuario.get_full_name() or self.usuario.username}"
