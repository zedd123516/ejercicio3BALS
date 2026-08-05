import json
from datetime import datetime, timedelta
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import (
    Agencia,
    AmaDeLlaves,
    Bloque,
    Factura,
    Habitacion,
    Huesped,
    Proyecto,
    Reserva,
    ReservaServicio,
    ServicioExtra,
    UsuarioCliente,
)

# ==================== DECORADORES PARA PROTEGER VISTAS ====================

def requiere_autenticacion(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def requiere_admin(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión")
            return redirect('login')
        if not request.user.is_staff:
            messages.error(request, "No tienes permiso para acceder aquí")
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper


def requiere_cliente(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión")
            return redirect('login')
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        try:
            UsuarioCliente.objects.get(usuario=request.user)
            return view_func(request, *args, **kwargs)
        except UsuarioCliente.DoesNotExist:
            messages.error(request, "Debes ser cliente para acceder")
            return redirect('/')
    return wrapper


# ==================== VISTAS DE AUTENTICACIÓN ====================

def registro_cliente(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        nombres = request.POST.get('nombres', '')
        apellidos = request.POST.get('apellidos', '')
        email = request.POST.get('email', '')
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        documento = request.POST.get('documento', '')
        telefono = request.POST.get('telefono', '')
        nacionalidad = request.POST.get('nacionalidad', 'Ecuador')
        
        # Validaciones
        if password != password_confirm:
            messages.error(request, "Las contraseñas no coinciden")
            return render(request, 'auth/registro.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, f"El usuario '{username}' ya está ingresado en el sistema.")
            return render(request, 'auth/registro.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, f"El correo '{email}' ya está ingresado en el sistema.")
            return render(request, 'auth/registro.html')

        if documento and (UsuarioCliente.objects.filter(documento=documento).exists() or Huesped.objects.filter(documento=documento).exists()):
            messages.error(request, f"El número de documento '{documento}' ya está ingresado en el sistema.")
            return render(request, 'auth/registro.html')
        
        try:
            # Crear usuario
            usuario = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombres,
                last_name=apellidos
            )
            
            # Crear perfil de cliente
            UsuarioCliente.objects.create(
                usuario=usuario,
                documento=documento,
                telefono=telefono,
                nacionalidad=nacionalidad
            )

            # Crear o actualizar registro en Huesped para conectar con el sistema de reservas
            Huesped.objects.get_or_create(
                documento=documento,
                defaults={
                    'nombres': nombres,
                    'apellidos': apellidos,
                    'email': email,
                    'telefono': telefono,
                    'nacionalidad': nacionalidad
                }
            )
        except IntegrityError:
            messages.error(request, "Error al registrar: Ya existe un registro con ese usuario, correo o documento.")
            return render(request, 'auth/registro.html')

        # Enviar correo electrónico de confirmación de registro
        try:
            try:
                host = request.get_host()
            except Exception:
                host = request.META.get('HTTP_HOST', 'localhost:8000')
            domain = f"{request.scheme}://{host}"
            subject = f"¡Bienvenido a HotelZ, {nombres}!"
            html_message = render_to_string('auth/email_bienvenida.html', {
                'nombre': nombres,
                'apellido': apellidos,
                'username': username,
                'email': email,
                'domain': domain
            })
            plain_message = strip_tags(html_message)
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'HotelZ <noreply@hotelz.com>')

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )
        except Exception as e:
            print(f"Error al enviar correo de bienvenida: {e}")

        messages.success(request, "Registro exitoso. Se ha enviado un correo de bienvenida. Inicia sesión para continuar")
        return redirect('login')
    
    return render(request, 'auth/registro.html')


def login_usuario(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('/reservas-hoteles/')
        return redirect('/mis-reservas/')
    
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        usuario = authenticate(request, username=username, password=password)
        
        if usuario is not None:
            login(request, usuario)
            messages.success(request, f"Bienvenido {usuario.first_name or usuario.username}")
            
            if usuario.is_staff:
                return redirect('/reservas-hoteles/')
            return redirect('/mis-reservas/')
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
    
    return render(request, 'auth/login.html')


def logout_usuario(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente")
    return redirect('/')


# Ruta Inicio de todo
def inicio(request):
    return render(request, 'inicio.html')

# AGENCIA
def nuevaAgencia(request):
    return render(request, 'nuevaAgencia.html')

# Añadir lo de from .models import Agencia, Proyecto, Bloque
# Tambioen from django.shortcuts import render, redirect
def guardarAgencia(request):
    nombreNuevaAgencia = request.POST.get("nombre", "").strip()
    rucNuevaAgencia = request.POST.get("ruc", "").strip()
    telefonoNuevaAgencia = request.POST.get("telefono", "").strip()
    
    if Agencia.objects.filter(ruc=rucNuevaAgencia).exists():
        messages.error(request, f"El RUC '{rucNuevaAgencia}' ya está ingresado en el sistema.")
        return redirect('/agencias/')

    if Agencia.objects.filter(nombre=nombreNuevaAgencia).exists():
        messages.error(request, f"La agencia '{nombreNuevaAgencia}' ya está ingresada en el sistema.")
        return redirect('/agencias/')

    try:
        Agencia.objects.create(
            nombre=nombreNuevaAgencia,
            ruc=rucNuevaAgencia,
            telefono=telefonoNuevaAgencia
        )
        messages.success(request, "Agencia guardada exitosamente")
    except IntegrityError:
        messages.error(request, "Error al guardar la agencia: El RUC o nombre ya está ingresado.")
        return redirect('/agencias/')

    return redirect('/agencias/')

#Renderizar la inferfaz de listado de Agencias
#Ahora Consultar los registros que estan en la BDD
def agencias(request):
    agenciasObtenidas = Agencia.objects.all()
    return render(request, 'agencias.html', {
        'misAgencias': agenciasObtenidas
    })

def eliminarAgencia(request, id):
    agenciaEliminar = Agencia.objects.get(id=id)
    agenciaEliminar.delete()
    messages.success(request, "Agencia Eliminada exitosamente")
    return redirect('/agencias/')

def editarAgencia(request, id):
    agenciaEdit = Agencia.objects.get(id=id)
    return render(request, 'editarAgencia.html', {
        'misAgencias': agenciaEdit
    })

def procesarActualizacionAgencia(request):
    id = request.POST['id']
    nom = request.POST.get('nombre', '').strip()
    ruc = request.POST.get('ruc', '').strip()
    tel = request.POST.get('telefono', '').strip()

    if Agencia.objects.filter(ruc=ruc).exclude(id=id).exists():
        messages.error(request, f"El RUC '{ruc}' ya está ingresado en otra agencia.")
        return redirect(f'/editarAgencia/{id}/')

    if Agencia.objects.filter(nombre=nom).exclude(id=id).exists():
        messages.error(request, f"El nombre '{nom}' ya está ingresado en otra agencia.")
        return redirect(f'/editarAgencia/{id}/')

    try:
        agenciaEditar = Agencia.objects.get(id=id)
        agenciaEditar.nombre = nom
        agenciaEditar.ruc = ruc
        agenciaEditar.telefono = tel
        agenciaEditar.save()
        messages.success(request, "Agencia Editada Exitosamente")
    except IntegrityError:
        messages.error(request, "Error al actualizar la agencia: Datos duplicados.")
        return redirect(f'/editarAgencia/{id}/')

    return redirect('/agencias/')


# PROYECTOS
def nuevoProyecto(request):
    agenciasExistentes = Agencia.objects.all() 
    return render(request, 'nuevoProyecto.html', {'agencias': agenciasExistentes})

def guardarProyecto(request):
    nombreNuevoProyecto = request.POST.get("nombre_proyecto", "").strip()
    ubicacionNuevoProyecto = request.POST.get("ubicacion", "").strip()
    agenciaId = request.POST.get("agencia")

    if Proyecto.objects.filter(nombre_proyecto=nombreNuevoProyecto).exists():
        messages.error(request, f"El proyecto '{nombreNuevoProyecto}' ya está ingresado en el sistema.")
        return redirect('/nuevoProyecto/')

    try:
        agenciaAsignada = Agencia.objects.get(id=agenciaId)
        Proyecto.objects.create(
            nombre_proyecto=nombreNuevoProyecto,
            ubicacion=ubicacionNuevoProyecto,
            agencia=agenciaAsignada
        )
        messages.success(request, "Proyecto guardado exitosamente")
    except IntegrityError:
        messages.error(request, "Error al guardar el proyecto: Nombre duplicado.")
        return redirect('/nuevoProyecto/')

    return redirect('/proyectos/')

def proyectos(request):
    proyectosObtenidos = Proyecto.objects.all()
    return render(request, 'proyectos.html', {
        'misProyectos': proyectosObtenidos
    })

def eliminarProyecto(request, id):
    proyectoEliminar = Proyecto.objects.get(id=id)
    proyectoEliminar.delete()
    messages.success(request, "Proyecto Eliminado exitosamente")
    return redirect('/proyectos/')

def editarProyecto(request, id):
    proyectoEdit = Proyecto.objects.get(id=id)
    agenciasTodas = Agencia.objects.all() 
    return render(request, 'editarProyecto.html', {
        'misProyectos': proyectoEdit,
        'agencias': agenciasTodas
    })

def procesarActualizacionProyecto(request):
    id = request.POST['id']
    nom_pro = request.POST.get('nombre_proyecto', '').strip()
    ubi = request.POST.get('ubicacion', '').strip()
    agencia_id = request.POST.get('agencia')

    if Proyecto.objects.filter(nombre_proyecto=nom_pro).exclude(id=id).exists():
        messages.error(request, f"El proyecto '{nom_pro}' ya está ingresado en el sistema.")
        return redirect(f'/editarProyecto/{id}/')

    try:
        proyectoEditar = Proyecto.objects.get(id=id)
        agenciaAsignada = Agencia.objects.get(id=agencia_id)
        proyectoEditar.nombre_proyecto = nom_pro
        proyectoEditar.ubicacion = ubi
        proyectoEditar.agencia = agenciaAsignada
        proyectoEditar.save()
        messages.success(request, "Proyecto Editado Exitosamente")
    except IntegrityError:
        messages.error(request, "Error al actualizar el proyecto: Nombre duplicado.")
        return redirect(f'/editarProyecto/{id}/')

    return redirect('/proyectos/')

# BLOQUES
def nuevoBloque(request):
    proyectosExistentes = Proyecto.objects.all()
    return render(request, 'nuevoBloque.html', {'proyectos': proyectosExistentes})

def guardarBloque(request):
    nombreNuevoBloque = request.POST.get("nombre_bloque", "").strip()
    pisosNuevoBloque = request.POST.get("pisos")
    proyectoId = request.POST.get("proyecto")

    if Bloque.objects.filter(nombre_bloque=nombreNuevoBloque, proyecto_id=proyectoId).exists():
        messages.error(request, f"El bloque '{nombreNuevoBloque}' ya está ingresado para el proyecto seleccionado.")
        return redirect('/nuevoBloque/')

    try:
        proyectoAsignado = Proyecto.objects.get(id=proyectoId)
        Bloque.objects.create(
            nombre_bloque=nombreNuevoBloque,
            pisos=pisosNuevoBloque,
            proyecto=proyectoAsignado
        )
        messages.success(request, "Bloque guardado exitosamente")
    except IntegrityError:
        messages.error(request, "Error al guardar el bloque: Datos duplicados.")
        return redirect('/nuevoBloque/')

    return redirect('/bloques/')

def bloques(request):
    bloquesObtenidos = Bloque.objects.all()
    return render(request, 'bloques.html', {
        'misBloques': bloquesObtenidos
    })

def eliminarBloque(request, id):
    bloqueEliminar = Bloque.objects.get(id=id)
    bloqueEliminar.delete()
    messages.success(request, "Bloque Eliminado exitosamente")
    return redirect('/bloques/')

def editarBloque(request, id):
    bloqueEdit = Bloque.objects.get(id=id)
    proyectosTodos = Proyecto.objects.all() 
    return render(request, 'editarBloque.html', {
        'misBloques': bloqueEdit,
        'proyectos': proyectosTodos
    })

def procesarActualizacionBloque(request):
    id = request.POST['id']
    nom_blo = request.POST.get('nombre_bloque', '').strip()
    pisos = request.POST.get('pisos')
    proyecto_id = request.POST.get('proyecto')

    if Bloque.objects.filter(nombre_bloque=nom_blo, proyecto_id=proyecto_id).exclude(id=id).exists():
        messages.error(request, f"El bloque '{nom_blo}' ya está ingresado para el proyecto seleccionado.")
        return redirect(f'/editarBloque/{id}/')

    try:
        bloqueEditar = Bloque.objects.get(id=id)
        proyectoAsignado = Proyecto.objects.get(id=proyecto_id)
        bloqueEditar.nombre_bloque = nom_blo
        bloqueEditar.pisos = pisos
        bloqueEditar.proyecto = proyectoAsignado
        bloqueEditar.save()
        messages.success(request, "Bloque Editado Exitosamente")
    except IntegrityError:
        messages.error(request, "Error al actualizar el bloque: Datos duplicados.")
        return redirect(f'/editarBloque/{id}/')

    return redirect('/bloques/')


# HELPER PARA MÉTRICAS DE REVPAR, ADR Y CANALES
def obtener_metricas_hotel():
    habitaciones = Habitacion.objects.all()
    reservas = Reserva.objects.all()
    facturas = Factura.objects.all()

    total_habitaciones = max(habitaciones.count(), 1)
    reservas_activas = reservas.filter(estado__in=['confirmada', 'checked_in'])
    
    total_ingresos_facturas = facturas.filter(estado='pagada').aggregate(total=Sum('total'))['total'] or 0
    total_ingresos_reservas = reservas.filter(estado__in=['confirmada', 'checked_in', 'checked_out']).aggregate(total=Sum('tarifa_base'))['total'] or 0
    total_ingresos = float(total_ingresos_facturas if total_ingresos_facturas > 0 else total_ingresos_reservas)

    cant_activas = reservas_activas.count()
    cant_total_reservas = max(reservas.count(), 1)
    cant_ocupadas = max(cant_activas, 1)

    ocupacion = round((cant_activas / total_habitaciones) * 100, 1) if habitaciones.exists() else 0
    revpar = round(total_ingresos / total_habitaciones, 2) if habitaciones.exists() else 0
    adr = round(total_ingresos / cant_ocupadas, 2) if cant_activas > 0 else (round(total_ingresos / cant_total_reservas, 2) if reservas.exists() else 0)

    CANAL_MAP = {
        'directo': 'Directo (Web/Recepción)',
        'booking': 'Booking / OTAs',
        'agencia': 'Agencia de Viajes',
        'corporativo': 'Convenio Corporativo',
    }

    raw_canales = list(reservas.values('canal_origen').annotate(cantidad=Count('id'), ingreso=Sum('tarifa_base')).order_by('-cantidad'))
    raw_dict = {item['canal_origen']: item for item in raw_canales}

    canales_list = []
    labels = []
    cantidades = []
    ingresos = []
    adrs = []
    porcentajes = []

    for code, label in CANAL_MAP.items():
        data = raw_dict.get(code, {'cantidad': 0, 'ingreso': 0})
        cant = data['cantidad']
        ing = float(data['ingreso'] or 0)
        pct = round((cant / cant_total_reservas) * 100, 1) if cant > 0 else 0
        c_adr = round(ing / cant, 2) if cant > 0 else 0
        c_revpar = round(ing / total_habitaciones, 2)

        item = {
            'canal_origen': code,
            'nombre': label,
            'cantidad': cant,
            'ingreso': ing,
            'porcentaje': pct,
            'adr': c_adr,
            'revpar_aporte': c_revpar,
        }
        canales_list.append(item)

    canales_list_sorted = sorted(canales_list, key=lambda x: (x['cantidad'], x['ingreso']), reverse=True)

    for c in canales_list_sorted:
        labels.append(c['nombre'])
        cantidades.append(c['cantidad'])
        ingresos.append(c['ingreso'])
        adrs.append(c['adr'])
        porcentajes.append(c['porcentaje'])

    return {
        'total_habitaciones_cnt': habitaciones.count(),
        'total_reservas_cnt': reservas.count(),
        'reservas_activas_cnt': cant_activas,
        'total_ingresos': total_ingresos,
        'ocupacion': ocupacion,
        'revpar': revpar,
        'adr': adr,
        'canales': canales_list_sorted,
        'canales_labels_json': json.dumps(labels),
        'canales_cantidades_json': json.dumps(cantidades),
        'canales_ingresos_json': json.dumps(ingresos),
        'canales_adrs_json': json.dumps(adrs),
        'canales_porcentajes_json': json.dumps(porcentajes),
    }


# SISTEMA DE RESERVAS PARA HOTELES (DASHBOARD ADMIN)
def reservas_hotel(request):
    habitaciones = Habitacion.objects.all().order_by('numero')
    huespedes = Huesped.objects.all()
    reservas = Reserva.objects.select_related('huesped', 'habitacion').prefetch_related('servicios').order_by('-id')
    servicios = ServicioExtra.objects.filter(activo=True)
    amas = AmaDeLlaves.objects.all().order_by('piso_asignado')
    facturas = Factura.objects.select_related('reserva').order_by('-id')
    clientes = UsuarioCliente.objects.select_related('usuario').all().order_by('-fecha_registro')

    metrics = obtener_metricas_hotel()

    eventos = []
    for reserva in reservas:
        eventos.append({
            'title': f"{reserva.habitacion.numero} · {reserva.huesped.nombres}",
            'start': reserva.fecha_entrada.isoformat(),
            'end': (reserva.fecha_salida + timedelta(days=1)).isoformat(),
            'backgroundColor': '#0d6efd' if reserva.estado == 'checked_in' else '#198754',
            'textColor': 'white',
            'extendedProps': {'habitacion': reserva.habitacion.numero, 'estado': reserva.estado}
        })

    return render(request, 'reservasHotel.html', {
        'habitaciones': habitaciones,
        'reservas': reservas,
        'servicios': servicios,
        'amas': amas,
        'facturas': facturas,
        'huespedes': huespedes,
        'clientes': clientes,
        'ocupacion': metrics['ocupacion'],
        'revpar': metrics['revpar'],
        'adr': metrics['adr'],
        'total_ingresos': metrics['total_ingresos'],
        'total_habitaciones': metrics['total_habitaciones_cnt'],
        'total_reservas_cnt': metrics['total_reservas_cnt'],
        'canales': metrics['canales'],
        'canales_labels_json': metrics['canales_labels_json'],
        'canales_cantidades_json': metrics['canales_cantidades_json'],
        'canales_ingresos_json': metrics['canales_ingresos_json'],
        'canales_adrs_json': metrics['canales_adrs_json'],
        'canales_porcentajes_json': metrics['canales_porcentajes_json'],
        'eventos_json': json.dumps(eventos),
    })


# HABITACIONES
@requiere_admin
def nuevaHabitacion(request):
    return render(request, 'nuevoHotel/nuevaHabitacion.html')


@requiere_admin
def guardarHabitacion(request):
    numero = request.POST.get("numero", "").strip()
    tipo = request.POST.get("tipo", "").strip()
    capacidad = request.POST.get("capacidad")
    precio_noche = request.POST.get("precio_noche")
    piso = request.POST.get("piso")
    estado = request.POST.get("estado", "disponible")

    if Habitacion.objects.filter(numero=numero).exists():
        messages.error(request, f"La habitación N° {numero} ya está ingresada en el sistema.")
        return redirect('/nueva-habitacion/')

    try:
        Habitacion.objects.create(
            numero=numero,
            tipo=tipo,
            capacidad=capacidad,
            precio_noche=precio_noche,
            piso=piso,
            estado=estado
        )
        messages.success(request, "Habitación guardada exitosamente")
    except IntegrityError:
        messages.error(request, f"La habitación N° {numero} ya está ingresada en el sistema.")
        return redirect('/nueva-habitacion/')

    return redirect('/habitaciones/')


@requiere_admin
def editarHabitacion(request, id):
    habitacion = Habitacion.objects.get(id=id)
    return render(request, 'nuevoHotel/editarHabitacion.html', {'habitacion': habitacion})


@requiere_admin
def procesarActualizacionHabitacion(request):
    id = request.POST['id']
    numero = request.POST.get('numero', '').strip()
    tipo = request.POST.get('tipo', '').strip()
    capacidad = request.POST.get('capacidad')
    precio_noche = request.POST.get('precio_noche')
    piso = request.POST.get('piso')
    estado = request.POST.get('estado', 'disponible')

    if Habitacion.objects.filter(numero=numero).exclude(id=id).exists():
        messages.error(request, f"La habitación N° {numero} ya está ingresada por otra habitación.")
        return redirect(f'/editar-habitacion/{id}/')

    try:
        habitacion = Habitacion.objects.get(id=id)
        habitacion.numero = numero
        habitacion.tipo = tipo
        habitacion.capacidad = capacidad
        habitacion.precio_noche = precio_noche
        habitacion.piso = piso
        habitacion.estado = estado
        habitacion.save()
        messages.success(request, "Habitación actualizada exitosamente")
    except IntegrityError:
        messages.error(request, f"La habitación N° {numero} ya está ingresada por otra habitación.")
        return redirect(f'/editar-habitacion/{id}/')

    return redirect('/habitaciones/')


@requiere_admin
def eliminarHabitacion(request, id):
    habitacion = Habitacion.objects.get(id=id)
    habitacion.delete()
    messages.success(request, "Habitación eliminada exitosamente")
    return redirect('/habitaciones/')


# HUÉSPEDES
@requiere_admin
def nuevoHuesped(request):
    return render(request, 'nuevoHotel/nuevoHuesped.html')


@requiere_admin
def guardarHuesped(request):
    nombres = request.POST.get("nombres", "").strip()
    apellidos = request.POST.get("apellidos", "").strip()
    documento = request.POST.get("documento", "").strip()
    email = request.POST.get("email", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    nacionalidad = request.POST.get("nacionalidad", "Ecuador").strip()

    if Huesped.objects.filter(documento=documento).exists():
        messages.error(request, f"El número de documento '{documento}' ya está ingresado para otro huésped.")
        return redirect('/nuevo-huesped/')

    try:
        Huesped.objects.create(
            nombres=nombres,
            apellidos=apellidos,
            documento=documento,
            email=email,
            telefono=telefono,
            nacionalidad=nacionalidad
        )
        messages.success(request, "Huésped guardado exitosamente")
    except IntegrityError:
        messages.error(request, f"El número de documento '{documento}' ya está ingresado para otro huésped.")
        return redirect('/nuevo-huesped/')

    return redirect('/huespedes/')


@requiere_admin
def editarHuesped(request, id):
    huesped = Huesped.objects.get(id=id)
    return render(request, 'nuevoHotel/editarHuesped.html', {'huesped': huesped})


@requiere_admin
def procesarActualizacionHuesped(request):
    id = request.POST['id']
    nombres = request.POST.get('nombres', '').strip()
    apellidos = request.POST.get('apellidos', '').strip()
    documento = request.POST.get('documento', '').strip()
    email = request.POST.get('email', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    nacionalidad = request.POST.get('nacionalidad', 'Ecuador').strip()

    if Huesped.objects.filter(documento=documento).exclude(id=id).exists():
        messages.error(request, f"El número de documento '{documento}' ya está ingresado para otro huésped.")
        return redirect(f'/editar-huesped/{id}/')

    try:
        huesped = Huesped.objects.get(id=id)
        huesped.nombres = nombres
        huesped.apellidos = apellidos
        huesped.documento = documento
        huesped.email = email
        huesped.telefono = telefono
        huesped.nacionalidad = nacionalidad
        huesped.save()
        messages.success(request, "Huésped actualizado exitosamente")
    except IntegrityError:
        messages.error(request, f"El número de documento '{documento}' ya está ingresado para otro huésped.")
        return redirect(f'/editar-huesped/{id}/')

    return redirect('/huespedes/')


@requiere_admin
def eliminarHuesped(request, id):
    huesped = Huesped.objects.get(id=id)
    huesped.delete()
    messages.success(request, "Huésped eliminado exitosamente")
    return redirect('/huespedes/')


# RESERVAS
@requiere_admin
def nuevaReserva(request):
    habitaciones = Habitacion.objects.filter(estado='disponible')
    huespedes = Huesped.objects.all()
    return render(request, 'nuevoHotel/nuevaReserva.html', {
        'habitaciones': habitaciones,
        'huespedes': huespedes
    })


@requiere_admin
def guardarReserva(request):
    huesped_id = request.POST["huesped"]
    habitacion_id = request.POST["habitacion"]
    fecha_entrada = request.POST["fecha_entrada"]
    fecha_salida = request.POST["fecha_salida"]
    numero_huespedes = request.POST["numero_huespedes"]
    canal_origen = request.POST.get("canal_origen", "directo")
    tarifa_base = request.POST.get("tarifa_base", 0)
    notas = request.POST.get("notas", "")

    if fecha_salida <= fecha_entrada:
        messages.error(request, "La fecha de salida debe ser posterior a la fecha de entrada.")
        return redirect('/nueva-reserva/')

    reserva_existente = Reserva.objects.filter(
        habitacion_id=habitacion_id,
        estado__in=['confirmada', 'checked_in'],
        fecha_entrada__lt=fecha_salida,
        fecha_salida__gt=fecha_entrada
    ).exists()

    if reserva_existente:
        messages.error(request, "La habitación seleccionada ya tiene una reserva activa para esas fechas.")
        return redirect('/nueva-reserva/')

    try:
        huesped = Huesped.objects.get(id=huesped_id)
        habitacion = Habitacion.objects.get(id=habitacion_id)

        reserva = Reserva.objects.create(
            huesped=huesped,
            habitacion=habitacion,
            fecha_entrada=fecha_entrada,
            fecha_salida=fecha_salida,
            numero_huespedes=numero_huespedes,
            canal_origen=canal_origen,
            tarifa_base=tarifa_base,
            notas=notas
        )

        habitacion.estado = 'ocupada'
        habitacion.save()

        Factura.objects.create(
            reserva=reserva,
            numero_factura=f'F-{reserva.id:03d}',
            total=float(tarifa_base),
            estado='pendiente',
            metodo_pago='Efectivo'
        )

        messages.success(request, "Reserva guardada exitosamente")
    except IntegrityError:
        messages.error(request, "Error al guardar la reserva: Datos duplicados o inválidos.")
        return redirect('/nueva-reserva/')

    return redirect('/reservas/')


@requiere_admin
def editarReserva(request, id):
    reserva = Reserva.objects.get(id=id)
    habitaciones = Habitacion.objects.all()
    huespedes = Huesped.objects.all()
    return render(request, 'nuevoHotel/editarReserva.html', {
        'reserva': reserva,
        'habitaciones': habitaciones,
        'huespedes': huespedes
    })


@requiere_admin
def procesarActualizacionReserva(request):
    id = request.POST['id']
    huesped_id = request.POST['huesped']
    habitacion_id = request.POST['habitacion']
    fecha_entrada = request.POST['fecha_entrada']
    fecha_salida = request.POST['fecha_salida']
    estado = request.POST.get('estado', 'confirmada')
    numero_huespedes = request.POST['numero_huespedes']
    canal_origen = request.POST.get('canal_origen', 'directo')
    tarifa_base = request.POST.get('tarifa_base', 0)
    notas = request.POST.get('notas', '')

    if fecha_salida <= fecha_entrada:
        messages.error(request, "La fecha de salida debe ser posterior a la fecha de entrada.")
        return redirect(f'/editar-reserva/{id}/')

    reserva_existente = Reserva.objects.filter(
        habitacion_id=habitacion_id,
        estado__in=['confirmada', 'checked_in'],
        fecha_entrada__lt=fecha_salida,
        fecha_salida__gt=fecha_entrada
    ).exclude(id=id).exists()

    if reserva_existente:
        messages.error(request, "La habitación seleccionada ya tiene una reserva activa para esas fechas.")
        return redirect(f'/editar-reserva/{id}/')

    try:
        reserva = Reserva.objects.get(id=id)
        huesped = Huesped.objects.get(id=huesped_id)
        habitacion = Habitacion.objects.get(id=habitacion_id)

        reserva.huesped = huesped
        reserva.habitacion = habitacion
        reserva.fecha_entrada = fecha_entrada
        reserva.fecha_salida = fecha_salida
        reserva.estado = estado
        reserva.numero_huespedes = numero_huespedes
        reserva.canal_origen = canal_origen
        reserva.tarifa_base = tarifa_base
        reserva.notas = notas
        reserva.save()

        messages.success(request, "Reserva actualizada exitosamente")
    except IntegrityError:
        messages.error(request, "Error al actualizar la reserva: Datos duplicados o inválidos.")
        return redirect(f'/editar-reserva/{id}/')

    return redirect('/reservas/')


@requiere_admin
def eliminarReserva(request, id):
    reserva = Reserva.objects.get(id=id)
    habitacion = reserva.habitacion
    habitacion.estado = 'disponible'
    habitacion.save()
    reserva.delete()
    messages.success(request, "Reserva eliminada exitosamente")
    return redirect('/reservas/')


# SERVICIOS EXTRAS
@requiere_admin
def nuevoServicio(request):
    return render(request, 'nuevoHotel/nuevoServicio.html')


@requiere_admin
def guardarServicio(request):
    nombre = request.POST.get("nombre", "").strip()
    descripcion = request.POST.get("descripcion", "").strip()
    precio = request.POST.get("precio", 0)

    if ServicioExtra.objects.filter(nombre=nombre).exists():
        messages.error(request, f"El servicio '{nombre}' ya está ingresado en el sistema.")
        return redirect('/nuevo-servicio/')

    try:
        ServicioExtra.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            activo=True
        )
        messages.success(request, "Servicio guardado exitosamente")
    except IntegrityError:
        messages.error(request, f"El servicio '{nombre}' ya está ingresado en el sistema.")
        return redirect('/nuevo-servicio/')

    return redirect('/servicios/')


@requiere_admin
def editarServicio(request, id):
    servicio = ServicioExtra.objects.get(id=id)
    return render(request, 'nuevoHotel/editarServicio.html', {'servicio': servicio})


@requiere_admin
def procesarActualizacionServicio(request):
    id = request.POST['id']
    nombre = request.POST.get('nombre', '').strip()
    descripcion = request.POST.get('descripcion', '').strip()
    precio = request.POST.get('precio', 0)

    if ServicioExtra.objects.filter(nombre=nombre).exclude(id=id).exists():
        messages.error(request, f"El servicio '{nombre}' ya está ingresado por otro servicio.")
        return redirect(f'/editar-servicio/{id}/')

    try:
        servicio = ServicioExtra.objects.get(id=id)
        servicio.nombre = nombre
        servicio.descripcion = descripcion
        servicio.precio = precio
        servicio.save()
        messages.success(request, "Servicio actualizado exitosamente")
    except IntegrityError:
        messages.error(request, f"El servicio '{nombre}' ya está ingresado por otro servicio.")
        return redirect(f'/editar-servicio/{id}/')

    return redirect('/servicios/')


@requiere_admin
def eliminarServicio(request, id):
    servicio = ServicioExtra.objects.get(id=id)
    servicio.delete()
    messages.success(request, "Servicio eliminado exitosamente")
    return redirect('/servicios/')


# AMAS DE LLAVES
@requiere_admin
def nuevoAma(request):
    return render(request, 'nuevoHotel/nuevoAma.html')


@requiere_admin
def guardarAma(request):
    nombre = request.POST.get("nombre", "").strip()
    turno = request.POST.get("turno", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    piso_asignado = request.POST.get("piso_asignado", 1)

    if AmaDeLlaves.objects.filter(nombre=nombre).exists():
        messages.error(request, f"El ama de llaves '{nombre}' ya está ingresada en el sistema.")
        return redirect('/nuevo-ama/')

    try:
        AmaDeLlaves.objects.create(
            nombre=nombre,
            turno=turno,
            telefono=telefono,
            piso_asignado=piso_asignado
        )
        messages.success(request, "Ama de llaves guardada exitosamente")
    except IntegrityError:
        messages.error(request, f"El ama de llaves '{nombre}' ya está ingresada en el sistema.")
        return redirect('/nuevo-ama/')

    return redirect('/amas/')


@requiere_admin
def editarAma(request, id):
    ama = AmaDeLlaves.objects.get(id=id)
    return render(request, 'nuevoHotel/editarAma.html', {'ama': ama})


@requiere_admin
def procesarActualizacionAma(request):
    id = request.POST['id']
    nombre = request.POST.get('nombre', '').strip()
    turno = request.POST.get('turno', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    piso_asignado = request.POST.get('piso_asignado', 1)

    if AmaDeLlaves.objects.filter(nombre=nombre).exclude(id=id).exists():
        messages.error(request, f"El ama de llaves '{nombre}' ya está ingresada por otra persona.")
        return redirect(f'/editar-ama/{id}/')

    try:
        ama = AmaDeLlaves.objects.get(id=id)
        ama.nombre = nombre
        ama.turno = turno
        ama.telefono = telefono
        ama.piso_asignado = piso_asignado
        ama.save()
        messages.success(request, "Ama de llaves actualizada exitosamente")
    except IntegrityError:
        messages.error(request, f"El ama de llaves '{nombre}' ya está ingresada por otra persona.")
        return redirect(f'/editar-ama/{id}/')

    return redirect('/amas/')


@requiere_admin
def eliminarAma(request, id):
    ama = AmaDeLlaves.objects.get(id=id)
    ama.delete()
    messages.success(request, "Ama de llaves eliminada exitosamente")
    return redirect('/amas/')


# FACTURAS
def editarFactura(request, id):
    factura = Factura.objects.get(id=id)
    return render(request, 'nuevoHotel/editarFactura.html', {'factura': factura})


def procesarActualizacionFactura(request):
    id = request.POST['id']
    total = request.POST['total']
    estado = request.POST.get('estado', 'pendiente')
    metodo_pago = request.POST.get('metodo_pago', 'Efectivo')

    factura = Factura.objects.get(id=id)
    factura.total = total
    factura.estado = estado
    factura.metodo_pago = metodo_pago
    factura.save()
    messages.success(request, "Factura actualizada exitosamente")
    return redirect('/facturas/')


def eliminarFactura(request, id):
    factura = Factura.objects.get(id=id)
    factura.delete()
    messages.success(request, "Factura eliminada exitosamente")
    return redirect('/facturas/')

# VISTAS LISTA PARA CADA TABLA
def habitaciones_lista(request):
    habitaciones = Habitacion.objects.all().order_by('numero')
    return render(request, 'hotel/habitaciones.html', {'habitaciones': habitaciones})


def huespedes_lista(request):
    huespedes = Huesped.objects.all()
    return render(request, 'hotel/huespedes.html', {'huespedes': huespedes})


def reservas_lista(request):
    reservas = Reserva.objects.select_related('huesped', 'habitacion').order_by('-id')
    huespedes = Huesped.objects.all()
    habitaciones = Habitacion.objects.all()
    return render(request, 'hotel/reservas.html', {
        'reservas': reservas,
        'huespedes': huespedes,
        'habitaciones': habitaciones
    })


def servicios_lista(request):
    servicios = ServicioExtra.objects.all()
    return render(request, 'hotel/servicios.html', {'servicios': servicios})


def amas_lista(request):
    amas = AmaDeLlaves.objects.all().order_by('piso_asignado')
    return render(request, 'hotel/amas.html', {'amas': amas})


def facturas_lista(request):
    facturas = Factura.objects.select_related('reserva').order_by('-id')
    return render(request, 'hotel/facturas.html', {'facturas': facturas})


def reportes_vista(request):
    metrics = obtener_metricas_hotel()
    return render(request, 'hotel/reportes.html', {
        'ocupacion': metrics['ocupacion'],
        'revpar': metrics['revpar'],
        'adr': metrics['adr'],
        'total_ingresos': metrics['total_ingresos'],
        'total_habitaciones': metrics['total_habitaciones_cnt'],
        'total_reservas': metrics['total_reservas_cnt'],
        'canales': metrics['canales'],
        'canales_labels_json': metrics['canales_labels_json'],
        'canales_cantidades_json': metrics['canales_cantidades_json'],
        'canales_ingresos_json': metrics['canales_ingresos_json'],
        'canales_adrs_json': metrics['canales_adrs_json'],
        'canales_porcentajes_json': metrics['canales_porcentajes_json'],
    })


def clientes_lista(request):
    """Vista para listar todos los usuarios clientes registrados."""
    clientes = UsuarioCliente.objects.select_related('usuario').all().order_by('-fecha_registro')
    return render(request, 'hotel/clientes.html', {'clientes': clientes})


@requiere_admin
def editarCliente(request, id):
    cliente = UsuarioCliente.objects.select_related('usuario').get(id=id)
    return render(request, 'nuevoHotel/editarCliente.html', {'cliente': cliente})


@requiere_admin
def procesarActualizacionCliente(request):
    id = request.POST.get('id')
    nombres = request.POST.get('nombres', '').strip()
    apellidos = request.POST.get('apellidos', '').strip()
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    documento = request.POST.get('documento', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    nacionalidad = request.POST.get('nacionalidad', 'Ecuador').strip()

    cliente = UsuarioCliente.objects.select_related('usuario').get(id=id)
    usuario = cliente.usuario

    if User.objects.filter(username=username).exclude(id=usuario.id).exists():
        messages.error(request, f"El nombre de usuario '{username}' ya está ingresado.")
        return redirect(f'/editar-cliente/{id}/')

    if email and User.objects.filter(email=email).exclude(id=usuario.id).exists():
        messages.error(request, f"El correo electrónico '{email}' ya está ingresado.")
        return redirect(f'/editar-cliente/{id}/')

    if documento and UsuarioCliente.objects.filter(documento=documento).exclude(id=cliente.id).exists():
        messages.error(request, f"El número de documento '{documento}' ya está ingresado por otro cliente.")
        return redirect(f'/editar-cliente/{id}/')

    try:
        usuario.first_name = nombres
        usuario.last_name = apellidos
        usuario.username = username
        usuario.email = email
        usuario.save()

        cliente.documento = documento
        cliente.telefono = telefono
        cliente.nacionalidad = nacionalidad
        cliente.save()

        # Sincronizar en Huesped si existe el registro
        if documento:
            Huesped.objects.filter(documento=documento).update(
                nombres=nombres,
                apellidos=apellidos,
                email=email,
                telefono=telefono,
                nacionalidad=nacionalidad
            )

        messages.success(request, "Cliente actualizado exitosamente")
    except IntegrityError:
        messages.error(request, "Error al actualizar el cliente: Datos duplicados.")
        return redirect(f'/editar-cliente/{id}/')

    return redirect('/clientes/')


@requiere_admin
def eliminarCliente(request, id):
    cliente = UsuarioCliente.objects.select_related('usuario').get(id=id)
    usuario = cliente.usuario
    cliente.delete()
    if usuario:
        usuario.delete()
    messages.success(request, "Cliente eliminado exitosamente")
    return redirect('/clientes/')


@requiere_autenticacion
def reservar_cliente(request):
    """Vista para que un cliente autenticado realice su propia reserva de hotel."""
    if request.method == 'POST':
        habitacion_id = request.POST.get('habitacion')
        fecha_entrada = request.POST.get('fecha_entrada')
        fecha_salida = request.POST.get('fecha_salida')
        numero_huespedes = request.POST.get('numero_huespedes', 1)
        servicios_seleccionados = request.POST.getlist('servicios')
        notas = request.POST.get('notas', '')

        if fecha_salida <= fecha_entrada:
            messages.error(request, "La fecha de salida debe ser posterior a la fecha de entrada.")
            return redirect('/reservar-cliente/')

        reserva_existente = Reserva.objects.filter(
            habitacion_id=habitacion_id,
            estado__in=['confirmada', 'checked_in'],
            fecha_entrada__lt=fecha_salida,
            fecha_salida__gt=fecha_entrada
        ).exists()

        if reserva_existente:
            messages.error(request, "La habitación seleccionada ya cuenta con una reserva activa para esas fechas.")
            return redirect('/reservar-cliente/')

        try:
            # Buscar o crear el registro de Huesped para el usuario en sesión
            perfil = getattr(request.user, 'perfil_cliente', None)
            documento = getattr(perfil, 'documento', None) or f"USR-{request.user.id}"
            telefono = getattr(perfil, 'telefono', '') or ''
            nacionalidad = getattr(perfil, 'nacionalidad', 'Ecuador') or 'Ecuador'

            huesped, _ = Huesped.objects.get_or_create(
                documento=documento,
                defaults={
                    'nombres': request.user.first_name or request.user.username,
                    'apellidos': request.user.last_name or 'Cliente',
                    'email': request.user.email,
                    'telefono': telefono,
                    'nacionalidad': nacionalidad
                }
            )

            habitacion = Habitacion.objects.get(id=habitacion_id)
            tarifa_total = habitacion.precio_noche

            reserva = Reserva.objects.create(
                huesped=huesped,
                habitacion=habitacion,
                fecha_entrada=fecha_entrada,
                fecha_salida=fecha_salida,
                numero_huespedes=numero_huespedes,
                canal_origen='directo',
                tarifa_base=tarifa_total,
                notas=notas,
                estado='confirmada'
            )

            habitacion.estado = 'ocupada'
            habitacion.save()

            # Registrar servicios extras
            subtotal_servicios = 0
            for s_id in servicios_seleccionados:
                try:
                    servicio = ServicioExtra.objects.get(id=s_id)
                    ReservaServicio.objects.create(
                        reserva=reserva,
                        servicio=servicio,
                        cantidad=1,
                        subtotal=servicio.precio
                    )
                    subtotal_servicios += float(servicio.precio)
                except ServicioExtra.DoesNotExist:
                    pass

            total_factura = float(tarifa_total) + subtotal_servicios

            Factura.objects.create(
                reserva=reserva,
                numero_factura=f'F-{reserva.id:03d}',
                total=total_factura,
                estado='pendiente',
                metodo_pago='Efectivo'
            )

            messages.success(request, f"¡Reserva #{reserva.id} realizada con éxito para la Habitación {habitacion.numero}!")
            return redirect('/mis-reservas/')
        except IntegrityError:
            messages.error(request, "Error al procesar la reserva: Datos duplicados o inválidos.")
            return redirect('/reservar-cliente/')

    habitaciones = Habitacion.objects.filter(estado='disponible')
    servicios = ServicioExtra.objects.filter(activo=True)
    return render(request, 'hotel/reservar_cliente.html', {
        'habitaciones': habitaciones,
        'servicios': servicios
    })


@requiere_autenticacion
def mis_reservas(request):
    """Vista para que un cliente consulte sus reservas realizadas."""
    perfil = getattr(request.user, 'perfil_cliente', None)
    documento = getattr(perfil, 'documento', None) or f"USR-{request.user.id}"
    
    huespedes = Huesped.objects.filter(documento=documento)
    if request.user.email:
        huespedes = huespedes | Huesped.objects.filter(email=request.user.email)
    
    reservas = Reserva.objects.filter(huesped__in=huespedes).select_related('habitacion', 'huesped').prefetch_related('servicios__servicio').order_by('-id')
    return render(request, 'hotel/mis_reservas.html', {'reservas': reservas})


# ==================== VISTAS DE REPORTES IMPRIMIBLES ====================

def reporteHabitaciones(request): 
    habitaciones = Habitacion.objects.all().order_by('numero')
    return render(request, 'hotel/reporteHabitaciones.html', {'habitaciones': habitaciones})

def reporteHuespedes(request):
    huespedes = Huesped.objects.all().order_by('nombres')
    return render(request, 'hotel/reporteHuespedes.html', {'huespedes': huespedes})

def reporteReservas(request):
    reservas = Reserva.objects.select_related('huesped', 'habitacion').order_by('-id')
    return render(request, 'hotel/reporteReservas.html', {'reservas': reservas})

def reporteServicios(request):
    servicios = ServicioExtra.objects.all()
    return render(request, 'hotel/reporteServicios.html', {'servicios': servicios})

def reporteAmas(request):
    amas = AmaDeLlaves.objects.all().order_by('piso_asignado')
    return render(request, 'hotel/reporteAmas.html', {'amas': amas})

def reporteFacturas(request):
    facturas = Factura.objects.select_related('reserva', 'reserva__huesped').order_by('-id')
    return render(request, 'hotel/reporteFacturas.html', {'facturas': facturas})

def reporteClientes(request):
    clientes = UsuarioCliente.objects.select_related('usuario').all().order_by('-fecha_registro')
    return render(request, 'hotel/reporteClientes.html', {'clientes': clientes})

@requiere_autenticacion
def reporteMisReservas(request):
    perfil = getattr(request.user, 'perfil_cliente', None)
    documento = getattr(perfil, 'documento', None) or f"USR-{request.user.id}"
    huespedes = Huesped.objects.filter(documento=documento)
    if request.user.email:
        huespedes = huespedes | Huesped.objects.filter(email=request.user.email)
    reservas = Reserva.objects.filter(huesped__in=huespedes).select_related('habitacion', 'huesped').order_by('-id')
    return render(request, 'hotel/reporteMisReservas.html', {'reservas': reservas})

def reporteCanalesPdf(request):
    metrics = obtener_metricas_hotel()
    return render(request, 'hotel/reporteCanalesPdf.html', {
        'ocupacion': metrics['ocupacion'],
        'revpar': metrics['revpar'],
        'adr': metrics['adr'],
        'total_ingresos': metrics['total_ingresos'],
        'canales': metrics['canales'],
        'fecha_generacion': datetime.now().strftime('%d/%m/%Y %H:%M'),
    })