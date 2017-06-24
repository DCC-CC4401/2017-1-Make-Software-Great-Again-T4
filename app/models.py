# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

from polymorphic.models import PolymorphicModel

DIAS = [
    (1, 'Lunes'),
    (2, 'Martes'),
    (3, 'Miércoles'),
    (4, 'Jueves'),
    (5, 'Viernes'),
    (6, 'Sábado'),
    (7, 'Domingo')
]


class FormasDePago(models.Model):
    metodo = models.CharField(max_length=50)

    '''
    Inicializar con
        (0, 'Efectivo'),
        (1, 'Tarjeta de Crédito'),
        (2, 'Tarjeta de Débito'),
        (3, 'Tarjeta Junaeb'),
    '''


'''
 Campos de User de Django:
    - username
    - password
    - email
    - first_name
    - last_name
'''


# "Extiende" el usuario de Django para agregar tipo y avatar.
class Usuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipos = ((0, 'Admin'), (1, 'Alumno'), (2, 'Vendedor Fijo'), (3, 'Vendedor Ambulante'))
    tipo = models.IntegerField(choices=tipos)
    avatar = models.ImageField(upload_to='avatars')

    def __str__(self):
        return self.user.username

    def imagen(self):
        try:
            return '/'+str(self.avatar.url)
        except:
            return '/static/img/' + 'AvatarVendedor3.png'

    class Meta:
        db_table = 'usuario'


class Vendedor(PolymorphicModel):
    usuario = models.OneToOneField(Usuario)
    activo = models.BooleanField(default=False, blank=True)
    formas_pago = models.ManyToManyField(FormasDePago)

    lat = models.DecimalField(default=0, max_digits=10, decimal_places=7)
    lng = models.DecimalField(default=0, max_digits=10, decimal_places=7)
    numero_favoritos = models.PositiveIntegerField(default=0, editable=False)

    def payment_str(self):
        temp = []
        for i in self.formas_pago.values():
            temp.append(i['metodo'])
        return ' '.join(temp)

    def estado(self):
        return 'Activo' if self.activo else 'Inactivo'

    def tipo(self):
        return 'Vendedor Ambulante' if self.usuario.tipo == 3 else 'Vendedor Fijo'

    def serialize(self):
        products = Producto.objects.filter(vendedor=self)
        return {
            'position': {'lat': float(self.lat), 'lng': float(self.lng)},
            'state': 'A' if self.activo else 'I',
            'payment': ', '.join(map(lambda pay: pay.metodo, self.formas_pago.all())),
            'id': self.id,
            'name': self.name(),
            'avatar': self.avatar(),
            'products': [product.serialize() for product in products]
        }

    def name(self):
        user = self.usuario.user
        return "{} {}".format(user.first_name, user.last_name)

    def avatar(self):
        try:
            return '/' + self.usuario.avatar.url
        except ValueError:
            return None


# Hereda de Vendedor, se añaden horarios.
class VendedorFijo(Vendedor):
    hora_ini = models.TimeField(blank=True)
    hora_fin = models.TimeField(blank=True)

    def schedule(self):
        return self.hora_ini.strftime('%H:%M') + '-' + self.hora_fin.strftime('%H:%M')

    def serialize(self):
        return {**super().serialize(), **{
            'horaIni': self.hora_ini,
            'horaFin': self.hora_fin
        }}


# Mismos atributos de Vendedor
class VendedorAmbulante(Vendedor):
    pass


class Alumno(models.Model):
    usuario = models.OneToOneField(Usuario)
    favorites = models.ManyToManyField(Vendedor)


class Categoria(models.Model):
    nombre = models.CharField(max_length=50)


# Icons are saved to avoid saving the same image many times.
class ProductIcon(models.Model):
    name = models.CharField(max_length=30)
    icon = models.ImageField()

    def url(self):
        return self.icon.url[13:]


class Producto(models.Model):
    vendedor = models.ForeignKey(Vendedor)
    nombre = models.CharField(max_length=200)
    icono = models.ForeignKey(ProductIcon)
    categorias = models.ManyToManyField(Categoria)
    descripcion = models.TextField(blank=True, max_length=500)
    stock = models.PositiveSmallIntegerField(default=0)
    precio = models.PositiveSmallIntegerField(default=0)
    imagen = models.ImageField(upload_to="productos")

    def __str__(self):
        return self.nombre

    def category2str(self):
        temp = []
        for i in self.categorias.values():
            temp.append(i['nombre'])
        return ' '.join(temp)

    def serialize(self):
        return {
            'categories': [category.nombre
                           for category in self.categorias.all()],
            'stock': self.stock
        }

    class Meta:
        db_table = 'producto'


'''
Inicializar con:
        (
        (0, 'Cerdo'),
        (1, 'Chino'),
        (2, 'Completos'),
        (3, 'Egipcio'),
        (4, 'Empanadas'),
        (5, 'Ensalada'),
        (6, 'Japones'),
        (7, 'Pan'),
        (8, 'Papas fritas'),
        (9, 'Pasta'),
        (10, 'Pescado'),
        (11, 'Pollo'),
        (12, 'Postres'),
        (13, 'Sushi'),
        (14, 'Vacuno'),
        (15, 'Vegano'),
        (16, 'Vegetariano'),
    )
'''


class Favoritos(models.Model):
    alumno = models.ForeignKey(Alumno)
    vendedor = models.ForeignKey(Vendedor)
    fecha = models.DateField()

    class Meta:
        db_table = 'favoritos'


class Transacciones(models.Model):
    vendedor = models.ForeignKey(Vendedor)
    producto = models.ForeignKey(Producto)
    cantidad = models.IntegerField()
    fecha = models.DateField()

    class Meta:
        db_table = 'transacciones'


class Alerta(models.Model):
    usuario = models.ForeignKey(Usuario)
    posX = models.FloatField()
    posY = models.FloatField()


class Token(models.Model):
    vendedor = models.ForeignKey(Vendedor)
    token = models.CharField(max_length=1024)
