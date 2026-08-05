from django.test import TestCase, Client
from django.contrib.auth.models import User
from gestion.models import Agencia, Habitacion, Huesped, ServicioExtra, AmaDeLlaves, UsuarioCliente

class ValidacionesDuplicadosTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.client.force_login(self.admin)

    def test_habitacion_duplicada(self):
        Habitacion.objects.create(numero='101', tipo='Standard', capacidad=2, precio_noche=50, piso=1)
        response = self.client.post('/guardar-habitacion/', {
            'numero': '101',
            'tipo': 'Suite',
            'capacidad': 2,
            'precio_noche': 100,
            'piso': 1
        }, follow=True)
        self.assertContains(response, "ya está ingresada en el sistema")

    def test_huesped_duplicado(self):
        Huesped.objects.create(nombres='Juan', apellidos='Pérez', documento='1234567890')
        response = self.client.post('/guardar-huesped/', {
            'nombres': 'Pedro',
            'apellidos': 'Gómez',
            'documento': '1234567890',
            'email': 'pedro@example.com',
            'telefono': '0999999999',
            'nacionalidad': 'Ecuador'
        }, follow=True)
        self.assertContains(response, "ya está ingresado para otro huésped")

    def test_agencia_duplicada(self):
        Agencia.objects.create(nombre='Agencia Uno', ruc='1790000000001', telefono='022222222')
        response = self.client.post('/guardarAgencia/', {
            'nombre': 'Agencia Dos',
            'ruc': '1790000000001',
            'telefono': '033333333'
        }, follow=False)
        self.assertEqual(response.status_code, 302)
        messages_list = list(response.wsgi_request._messages)
        self.assertTrue(any("ya está ingresado en el sistema" in str(m) for m in messages_list))

    def test_servicio_duplicado(self):
        ServicioExtra.objects.create(nombre='Spa', precio=25)
        response = self.client.post('/guardar-servicio/', {
            'nombre': 'Spa',
            'descripcion': 'Masaje',
            'precio': 30
        }, follow=True)
        self.assertContains(response, "ya está ingresado en el sistema")

    def test_ama_duplicada(self):
        AmaDeLlaves.objects.create(nombre='Maria Rosa', turno='Mañana', piso_asignado=1)
        response = self.client.post('/guardar-ama/', {
            'nombre': 'Maria Rosa',
            'turno': 'Tarde',
            'telefono': '0987654321',
            'piso_asignado': 2
        }, follow=True)
        self.assertContains(response, "ya está ingresada en el sistema")

