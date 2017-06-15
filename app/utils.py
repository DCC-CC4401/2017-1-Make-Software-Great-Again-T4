# coding=utf-8

import datetime

from app.models import *


def add_user(data):
    user = User.objects.create_user(username=data['username'], email=data['email'], password=data['password'])
    user.first_name = data['name']
    user.last_name = data['last_name']
    user.save()


def add_app_user(data):
    add_user(data)
    user = User.objects.get(username=data['username'])
    p = Usuario(user=user, avatar=data['photo'], tipo=data['type'])
    p.save()
    print("App user saved")


def add_S_Vendedor(data):
    add_app_user(data)
    user = Usuario.objects.get(user=User.objects.get(username=data['username']))

    t_start = datetime.datetime.strptime(data['schedule'][0], '%H:%M').time()
    t_finish = datetime.datetime.strptime(data['schedule'][1], '%H:%M').time()

    p = VendedorFijo(usuario=user, activo=data['state'],
                     numero_favoritos=data['fav'], lat=data['lan'], lng=data['lng'],
                     hora_ini=t_start, hora_fin=t_finish)
    p.save()
    print(data['payment'])
    for i in data['payment']:
        p.formas_pago.add(FormasDePago.objects.get(metodo=i))
    p.save()
    print("S.Vendedor saved")


def add_A_Vendedor(data):
    add_app_user(data)
    user = Usuario.objects.get(user=User.objects.get(username=data['username']))
    p = VendedorAmbulante(usuario=user, activo=data['state'],
                          numero_favoritos=data['fav'], lat=data['lan'], lng=data['lng'])
    p.save()
    for i in data['payment']:
        p.formas_pago.add(FormasDePago.objects.get(metodo=i))
    p.save()
    print("A.Vendedor saved")


def add_product(data):
    user = Vendedor.objects.get(usuario=Usuario.objects.get(user=User.objects.get(username=data['username'])))
    icon = ProductIcon.objects.get(name=data['icon'])
    p = Producto(vendedor=user, nombre=data['name'], imagen=data['photo'], icono=icon,
                 descripcion=data['des'], stock=data['stock'], precio=data['price'])
    p.save()
    for i in data['category']:
        p.categorias.add(Categoria.objects.get(nombre=i))
    p.save()
    print("Product saved")


def add_category(cat):
    p = Categoria(nombre=cat)
    p.save()


def add_product_icon(data):
    p_icon = ProductIcon(name=data['name'], icon=data['icon'])
    p_icon.save()


def add_payment(pay):
    p = FormasDePago(metodo=pay)
    p.save()


def add_buyer(data):
    add_app_user(data)
    user = Usuario.objects.get(user=User.objects.get(username=data['username']))
    p = Alumno.objects.create(usuario=user)
    p.save()


def add_stat(data):
    user = Usuario.objects.get(user=User.objects.get(username=data['username']))
    vendor = Vendedor.objects.get(usuario=user)
    products = Producto.objects.filter(vendedor=vendor).filter(nombre=data['product_name'])
    if products.count() != 0:
        product = Producto.objects.filter(vendedor=vendor).filter(nombre=data['product_name']).first()
        p = Transacciones.objects.create(vendedor=vendor, fecha=data['date'], cantidad=data['amount'], producto=product)
        p.save()


def test():
    User.objects.create_superuser(username='admin', email='bal@123.ck', password='1234')

    add_category('Almuerzos')
    add_category('Snack')
    add_category('Postres')

    # Add all the original icons
    icon_dict_list = [
        {'name': 'bread', 'icon': 'static/img/bread.png'},
        {'name': 'breakfast', 'icon': 'static/img/breakfast.png'},
        {'name': 'burger', 'icon': 'static/img/burger.png'},
        {'name': 'chicken', 'icon': 'static/img/chicken.png'},
        {'name': 'chicken2', 'icon': 'static/img/chicken2.png'},
        {'name': 'chocolate', 'icon': 'static/img/chocolate.png'},
        {'name': 'coke', 'icon': 'static/img/coke.png'},
        {'name': 'cupcake', 'icon': 'static/img/cupcake.png'},
        {'name': 'donut', 'icon': 'static/img/donut.png'},
        {'name': 'jelly', 'icon': 'static/img/jelly.png'},
        {'name': 'fish', 'icon': 'static/img/fish.png'},
        {'name': 'fries', 'icon': 'static/img/fries.png'},
        {'name': 'hot-dog', 'icon': 'static/img/hot-dog.png'},
        {'name': 'icecream', 'icon': 'static/img/icecream.png'},
        {'name': 'juice', 'icon': 'static/img/juice.png'},
        {'name': 'lettuce', 'icon': 'static/img/lettuce.png'},
        {'name': 'pizza', 'icon': 'static/img/pizza.png'},
        {'name': 'spaguetti', 'icon': 'static/img/spaguetti.png'},
        {'name': 'rice', 'icon': 'static/img/rice.png'}
    ]
    for idata in icon_dict_list:
        add_product_icon(idata)

    add_payment('tarjeta')
    add_payment('efectivo')
    add_payment('junaeb')

    data1 = {
        'username': 'vendor1',
        'email': 'test@prueba.cl',
        'password': '1234',
        'name': 'Daniel',
        'last_name': 'Aguirre',
        'photo': None,
        'type': 2,
        'payment': ['efectivo', 'tarjeta'],
        'stack': True,
        'state': True,
        'fav': 42,
        'lan': 0.0,
        'lng': 0.0,
        'schedule': ['12:00', '13:00']
    }
    add_S_Vendedor(data1)

    data2 = {
        'username': 'buyer',
        'email': 'test@prueba.cl',
        'password': '1234',
        'name': 'Robinson',
        'last_name': 'Castro',
        'photo': None,
        'type': 1,
    }
    add_buyer(data2)
    buyer = Alumno.objects.get(usuario=Usuario.objects.get(user=User.objects.get(username=data2['username'])))
    buyer.favorites.add(Vendedor.objects.get(usuario=
                                             Usuario.objects.get(user=User.objects.get(username=data1['username']))))
    buyer.save()

    data3 = {
        'username': 'vendor2',
        'email': 'test@prueba.cl',
        'password': '1234',
        'name': 'Andres',
        'last_name': 'Olivares',
        'photo': None,
        'type': 3,
        'payment': ['efectivo'],
        'stack': True,
        'state': False,
        'fav': 42,
        'lan': 0.0,
        'lng': 0.0,
    }
    add_A_Vendedor(data3)

    product_1 = {
        'username': 'vendor1',
        'name': 'Pizza',
        'photo': None,
        'icon': 'pizza',
        'category': ['Almuerzos'],
        'des': 'Deliciosa pizza hecha con masa casera, viene disponible en 3 tipos:',
        'stock': 20,
        'price': 1300
    }
    product_2 = {
        'username': 'vendor2',
        'name': 'Menú de arroz',
        'photo': None,
        'icon': 'rice',
        'category': ['Almuerzos'],
        'des': 'Almuerzo de arroz con pollo arvejado.',
        'stock': 40,
        'price': 2500
    }
    product_3 = {
        'username': 'vendor1',
        'name': 'Jugo',
        'photo': None,
        'icon': 'juice',
        'category': ['Snack'],
        'des': 'Jugo en caja sabor durazno.',
        'stock': 40,
        'price': 300
    }

    add_product(product_1)
    add_product(product_2)
    add_product(product_3)

    stat1 = {
        'username': 'vendor1',
        'product_name': 'Pizza',
        'date': datetime.datetime(year=2017, month=5, day=26, hour=13, minute=42, second=40),
        'amount': 1300
    }
    stat2 = {
        'username': 'vendor1',
        'product_name': 'Pizza',
        'date': datetime.datetime(year=2017, month=5, day=26, hour=12, minute=42, second=40),
        'amount': 1300
    }
    stat3 = {
        'username': 'vendor1',
        'product_name': 'Pizza',
        'date': datetime.datetime(year=2017, month=5, day=25, hour=13, minute=42, second=40),
        'amount': 1300
    }
    stat4 = {
        'username': 'vendor1',
        'product_name': 'Jugo',
        'date': datetime.datetime(year=2017, month=5, day=25, hour=12, minute=42, second=40),
        'amount': 400
    }

    add_stat(stat1)
    add_stat(stat2)
    add_stat(stat3)
    add_stat(stat4)
