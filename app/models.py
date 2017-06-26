# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
from django.contrib.auth.models import User
from django.db import models
from polymorphic.models import PolymorphicModel


'''

 Django User class fields:
    - username
    - password
    - email
    - first_name
    - last_name
'''


# "Extends" the Django user to agregate avatar and type.
class BaseUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    types = ((0, 'Admin'), (1, 'Alumno'), (2, 'Vendedor Fijo'), (3, 'Vendedor Ambulante'))
    type = models.IntegerField(choices=types)
    avatar = models.ImageField(upload_to='avatars')

    def __str__(self):
        return self.user.username

    def image(self):
        try:
            return '/' + str(self.avatar.url)
        except:
            return '/static/img/' + 'AvatarVendedor3.png'

    class Meta:
        db_table = 'base_user'


class PaymentMethod(models.Model):
    method = models.CharField(max_length=50)

    '''
    Initialize with
        (0, 'Efectivo'),
        (1, 'Tarjeta de Crédito'),
        (2, 'Tarjeta de Débito'),
        (3, 'Tarjeta Junaeb'),
    '''


class Vendor(PolymorphicModel):
    user = models.OneToOneField(BaseUser)
    active = models.BooleanField(default=False, blank=True)
    payment_methods = models.ManyToManyField(PaymentMethod)

    lat = models.DecimalField(default=0, max_digits=10, decimal_places=7)
    lng = models.DecimalField(default=0, max_digits=10, decimal_places=7)
    favorites_counter = models.PositiveIntegerField(default=0, editable=False)

    def payment_str(self):
        temp = []
        for i in self.payment_methods.values():
            temp.append(i['method'])
        return ' '.join(temp)

    def state(self):
        if self.user.type == 2:
            t = datetime.datetime.now().time()
            now = datetime.time(hour=t.hour, minute=t.minute)
            if self.start_hour <= now <= self.end_hour:
                self.active = True
            else:
                self.active = False

        return 'Activo' if self.active else 'Inactivo'

    def type(self):
        return 'Vendedor Ambulante' if self.user.type == 3 else 'Vendedor Fijo'

    def serialize(self):
        products = Product.objects.filter(vendedor=self)
        return {
            'position': {'lat': float(self.lat), 'lng': float(self.lng)},
            'state': 'A' if self.active else 'I',
            'payment': ', '.join(map(lambda pay: pay.method, self.payment_methods.all())),
            'id': self.id,
            'name': self.name(),
            'avatar': self.avatar(),
            'products': [product.serialize() for product in products]
        }

    def name(self):
        user = self.user.user
        return "{} {}".format(user.first_name, user.last_name)

    def avatar(self):
        try:
            return '/' + self.user.avatar.url
        except ValueError:
            return None


# Inherites from vendor
class SettledVendor(Vendor):
    start_hour = models.TimeField(blank=True)
    end_hour = models.TimeField(blank=True)

    def schedule(self):
        return self.start_hour.strftime('%H:%M') + '-' + self.end_hour.strftime('%H:%M')

    def serialize(self):
        return {**super().serialize(), **{
            'startHour': self.start_hour,
            'endHour': self.end_hour
        }}


# Same attributes as Vendor
class AmbulantVendor(Vendor):
    pass


class Student(models.Model):
    user = models.OneToOneField(BaseUser)
    favorites = models.ManyToManyField(Vendor)


class Category(models.Model):
    name = models.CharField(max_length=50)


# Icons are saved to avoid saving the same image many times.
class ProductIcon(models.Model):
    name = models.CharField(max_length=30)
    icon = models.ImageField()

    def url(self):
        return self.icon.url[13:]


class Product(models.Model):
    vendor = models.ForeignKey(Vendor)
    name = models.CharField(max_length=200)
    icon = models.ForeignKey(ProductIcon)
    categories = models.ManyToManyField(Category)
    description = models.TextField(blank=True, max_length=500)
    stock = models.PositiveSmallIntegerField(default=0)
    price = models.PositiveSmallIntegerField(default=0)
    image = models.ImageField(upload_to="products")

    def __str__(self):
        return self.name

    def category2str(self):
        temp = []
        for i in self.categories.values():
            temp.append(i['name'])
        return ' '.join(temp)

    def serialize(self):
        return {
            'categories': [category.name
                           for category in self.categories.all()],
            'stock': self.stock
        }

    class Meta:
        db_table = 'product'


'''
Initialize with:
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


class Transactions(models.Model):
    vendor = models.ForeignKey(Vendor)
    product = models.ForeignKey(Product)
    amount = models.IntegerField()
    date = models.DateField()

    class Meta:
        db_table = 'transactions'


class Alert(models.Model):
    user = models.ForeignKey(BaseUser)
    posX = models.FloatField()
    posY = models.FloatField()


class Token(models.Model):
    vendor = models.ForeignKey(Vendor)
    code = models.CharField(max_length=150)
    token = models.CharField(max_length=1024)
