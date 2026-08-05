from django.contrib import admin

from .models import Agencia, Proyecto, Bloque
from .models import Habitacion, Huesped, Reserva, ServicioExtra, ReservaServicio, AmaDeLlaves, Factura


class AgenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'ruc', 'telefono')


class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_proyecto', 'ubicacion', 'agencia')


class BloqueAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_bloque', 'pisos', 'proyecto')


class HabitacionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'tipo', 'capacidad', 'precio_noche', 'piso', 'estado')


class HuespedAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombres', 'apellidos', 'documento', 'email', 'telefono')


class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'huesped', 'habitacion', 'fecha_entrada', 'fecha_salida', 'estado', 'canal_origen', 'tarifa_base')


class ServicioExtraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'activo')


class ReservaServicioAdmin(admin.ModelAdmin):
    list_display = ('reserva', 'servicio', 'cantidad', 'subtotal')


class AmaDeLlavesAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'turno', 'telefono', 'piso_asignado')


class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero_factura', 'reserva', 'fecha_emision', 'total', 'estado', 'metodo_pago')


admin.site.register(Agencia, AgenciaAdmin)
admin.site.register(Proyecto, ProyectoAdmin)
admin.site.register(Bloque, BloqueAdmin)
admin.site.register(Habitacion, HabitacionAdmin)
admin.site.register(Huesped, HuespedAdmin)
admin.site.register(Reserva, ReservaAdmin)
admin.site.register(ServicioExtra, ServicioExtraAdmin)
admin.site.register(ReservaServicio, ReservaServicioAdmin)
admin.site.register(AmaDeLlaves, AmaDeLlavesAdmin)
admin.site.register(Factura, FacturaAdmin)