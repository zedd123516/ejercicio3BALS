from django.urls import path

from . import views

urlpatterns = [
    # Autenticación
    path('login/', views.login_usuario, name='login'),
    path('registro/', views.registro_cliente, name='registro'),
    path('logout/', views.logout_usuario, name='logout'),
    
    path('', views.inicio),
    
    path('reservas-hoteles/', views.reservas_hotel),
    path('reservar-cliente/', views.reservar_cliente, name='reservar_cliente'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    
    # Páginas lista de cada tabla
    path('habitaciones/', views.habitaciones_lista),
    path('huespedes/', views.huespedes_lista),
    path('reservas/', views.reservas_lista),
    path('servicios/', views.servicios_lista),
    path('amas/', views.amas_lista),
    path('facturas/', views.facturas_lista),
    path('clientes/', views.clientes_lista, name='clientes_lista'),
    path('editar-cliente/<id>/', views.editarCliente, name='editarCliente'),
    path('procesar-actualizacion-cliente/', views.procesarActualizacionCliente, name='procesarActualizacionCliente'),
    path('eliminar-cliente/<id>/', views.eliminarCliente, name='eliminarCliente'),
    path('reportes/', views.reportes_vista),
    
    # Agencias
    path('agencias/', views.agencias),
    path('nuevaAgencia/', views.nuevaAgencia),
    path('guardarAgencia/', views.guardarAgencia),
    path('editarAgencia/<id>/', views.editarAgencia),
    path('procesarActualizacionAgencia/', views.procesarActualizacionAgencia),
    path('eliminarAgencia/<id>/', views.eliminarAgencia),

    # Proyectos
    path('proyectos/', views.proyectos),
    path('nuevoProyecto/', views.nuevoProyecto),
    path('guardarProyecto/', views.guardarProyecto),
    path('editarProyecto/<id>/', views.editarProyecto),
    path('procesarActualizacionProyecto/', views.procesarActualizacionProyecto),
    path('eliminarProyecto/<id>/', views.eliminarProyecto),

    # Bloques
    path('bloques/', views.bloques),
    path('nuevoBloque/', views.nuevoBloque),
    path('guardarBloque/', views.guardarBloque),
    path('editarBloque/<id>/', views.editarBloque),
    path('procesarActualizacionBloque/', views.procesarActualizacionBloque),
    path('eliminarBloque/<id>/', views.eliminarBloque),
    
    # Habitaciones
    path('nueva-habitacion/', views.nuevaHabitacion),
    path('guardar-habitacion/', views.guardarHabitacion),
    path('editar-habitacion/<id>/', views.editarHabitacion),
    path('procesar-actualizacion-habitacion/', views.procesarActualizacionHabitacion),
    path('eliminar-habitacion/<id>/', views.eliminarHabitacion),
    path('reporteHabitaciones/', views.reporteHabitaciones, name='reporteHabitaciones'),
    
    # Huéspedes
    path('nuevo-huesped/', views.nuevoHuesped),
    path('guardar-huesped/', views.guardarHuesped),
    path('editar-huesped/<id>/', views.editarHuesped),
    path('procesar-actualizacion-huesped/', views.procesarActualizacionHuesped),
    path('eliminar-huesped/<id>/', views.eliminarHuesped),
    
    # Reservas
    path('nueva-reserva/', views.nuevaReserva),
    path('guardar-reserva/', views.guardarReserva),
    path('editar-reserva/<id>/', views.editarReserva),
    path('procesar-actualizacion-reserva/', views.procesarActualizacionReserva),
    path('eliminar-reserva/<id>/', views.eliminarReserva),
    
    # Servicios Extras
    path('nuevo-servicio/', views.nuevoServicio),
    path('guardar-servicio/', views.guardarServicio),
    path('editar-servicio/<id>/', views.editarServicio),
    path('procesar-actualizacion-servicio/', views.procesarActualizacionServicio),
    path('eliminar-servicio/<id>/', views.eliminarServicio),
    
    # Amas de llaves
    path('nuevo-ama/', views.nuevoAma),
    path('guardar-ama/', views.guardarAma),
    path('editar-ama/<id>/', views.editarAma),
    path('procesar-actualizacion-ama/', views.procesarActualizacionAma),
    path('eliminar-ama/<id>/', views.eliminarAma),
    
    # Reportes Imprimibles
    path('reporteHabitaciones/', views.reporteHabitaciones, name='reporteHabitaciones'),
    path('reporteHuespedes/', views.reporteHuespedes, name='reporteHuespedes'),
    path('reporteReservas/', views.reporteReservas, name='reporteReservas'),
    path('reporteServicios/', views.reporteServicios, name='reporteServicios'),
    path('reporteAmas/', views.reporteAmas, name='reporteAmas'),
    path('reporteFacturas/', views.reporteFacturas, name='reporteFacturas'),
    path('reporteClientes/', views.reporteClientes, name='reporteClientes'),
    path('reporteMisReservas/', views.reporteMisReservas, name='reporteMisReservas'),
    path('reporteCanalesPdf/', views.reporteCanalesPdf, name='reporteCanalesPdf'),
]