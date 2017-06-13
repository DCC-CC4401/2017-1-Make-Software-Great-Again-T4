# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

DIAS = [
    (1, 'Lunes'),
    (2, 'Martes'),
    (3, 'Miércoles'),
    (4, 'Jueves'),
    (5, 'Viernes'),
    (6, 'Sábado'),
    (7, 'Domingo')
]

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
        return self.nombre

    class Meta:
        db_table = 'usuario'


class FormasDePago(models.Model):
    metodo = models.CharField(max_length=50)

    '''
    Inicializar con
        (0, 'Efectivo'),
        (1, 'Tarjeta de Crédito'),
        (2, 'Tarjeta de Débito'),
        (3, 'Tarjeta Junaeb'),
    '''


class Alumno(models.Model):
    usuario = models.OneToOneField(Usuario)


class Vendedor(models.Model):
    usuario = models.OneToOneField(Usuario)
    activo = models.BooleanField(default=False, blank=True)
    formas_pago = models.ManyToManyField(FormasDePago)


# Hereda de Vendedor, se añaden horarios.
# Horario: De dia_ini a dia_fin entre hora_ini y hora_fin.
class VendedorFijo(Vendedor):
    dias_ini = models.CharField(choices=DIAS,max_length=9)
    dia_fin = models.CharField(choices=DIAS,max_length=9)
    hora_ini = models.TimeField()
    hora_fin = models.TimeField()


# Mismos atributos de Vendedor
class VendedorAmbulante(models.Model):
    pass


class Categoria(models.Model):
    nombre = models.CharField(max_length=50)


class Comida(models.Model):
    vendedor = models.ForeignKey(Vendedor)
    nombre = models.CharField(max_length=200)
    categorias = models.ManyToManyField(Categoria)
    descripcion = models.TextField(blank=True)
    stock = models.PositiveSmallIntegerField(default=0)
    precio = models.PositiveSmallIntegerField(default=0)
    imagen = models.ImageField(upload_to="productos")

    def __str__(self):
        return self.nombre

    def category2str(self):
        temp = []
        for i in self.categorias.values():
            temp.append(i['name'])
        return ' '.join(temp)

    class Meta:
        db_table = 'comida'

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
    comida = models.ForeignKey(Comida)
    cantidad = models.IntegerField()
    fecha = models.DateField()

    class Meta:
        db_table = 'transacciones'

###### Borrar al modificar Views, lamentablemente muchas ######
###### funciones dependen de esta linea al migrar.       ######
class Imagen(models.Model):
    id = models.AutoField(primary_key=True)
    imagen = models.ImageField(upload_to='avatars')

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'imagen'