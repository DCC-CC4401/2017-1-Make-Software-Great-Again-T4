# coding=utf-8

import datetime

from app.models import *


def agregar_usuario_interno(data):
    user = User.objects.create_user(username=data['username'], email=data['email'], password=data['password'])
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.save()


def agregar_usuario(data):
    agregar_usuario_interno(data)
    user = User.objects.get(username=data['username'])
    p = Usuario(user=user, avatar=data['avatar'], tipo=data['tipo'])
    p.save()
    print("Usuario guardado")


def agregar_vendedor_fijo(data):
    print(data)
    agregar_usuario(data)
    user = Usuario.objects.get(user=User.objects.get(username=data['username']))
    p = VendedorFijo(usuario=user, hora_ini=data['hora_ini'], hora_fin=data['hora_fin'],
                     lat=data['lat'], lng=data['lng'])
    p.save()
    for i in data['formas_pago']:
        p.formas_pago.add(FormasDePago.objects.get(metodo=i))
    p.save()
    print("Vendedor fijo guardado")


def agregar_vendedor_ambulante(data):
    agregar_usuario(data)
    user = Usuario.objects.get(user=User.objects.get(username=data['username']))

    p = VendedorAmbulante(usuario=user)
    p.save()
    for i in data['formas_pago']:
        p.formas_pago.add(FormasDePago.objects.get(metodo=i))
    p.save()
    print("Vendedor ambulante guardado")


def crear_producto(vendedor, data):
    icono = ProductIcon.objects.get(name=data['icono'])
    p = Producto(vendedor=vendedor, nombre=data['nombre'], imagen=data['imagen'], icono=icono,
                 descripcion=data['descripcion'], stock=data['stock'], precio=data['precio'])
    p.save()
    for i in data['categorias']:
        p.categorias.add(Categoria.objects.get(nombre=i))
    p.save()
    print("Producto guardado")


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
    agregar_usuario(data)
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


def add_icons():
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


def test():
    User.objects.create_superuser(username='admin', email='bal@123.ck', password='1234')
    add_icons()

    add_category('Almuerzos')
    add_category('Snack')
    add_category('Postres')

    add_payment('tarjeta')
    add_payment('efectivo')
    add_payment('junaeb')

    data1 = {
        'username': 'vendor1',
        'email': 'test@prueba.cl',
        'password': '1234',
        'first_name': 'Daniel',
        'last_name': 'Aguirre',
        'avatar': None,
        'tipo': 2,
        'formas_pago': ['efectivo', 'tarjeta'],
        'state': True,
        'fav': 42,
        'lan': 0.0,
        'lng': 0.0,
        'hora_ini': datetime.time(hour=12, minute=0),
        'hora_fin': datetime.time(hour=13, minute=0)
    }
    agregar_vendedor_fijo(data1)

    data2 = {
        'username': 'buyer',
        'email': 'test@prueba.cl',
        'password': '1234',
        'first_name': 'Robinson',
        'last_name': 'Castro',
        'avatar': None,
        'tipo': 1,
    }
    add_buyer(data2)
    buyer = Alumno.objects.get(usuario=Usuario.objects.get(user=User.objects.get(username=data2['username'])))
    buyer.favorites.add(
        Vendedor.objects.get(usuario=Usuario.objects.get(user=User.objects.get(username=data1['username']))))
    buyer.save()
    p = Vendedor.objects.get(usuario=Usuario.objects.get(user=User.objects.get(username='vendor1')))
    p.numero_favoritos = +1
    p.save()

    data3 = {
        'username': 'vendor2',
        'email': 'test@prueba.cl',
        'password': '1234',
        'first_name': 'Andres',
        'last_name': 'Olivares',
        'avatar': None,
        'tipo': 3,
        'formas_pago': ['efectivo'],
        'stack': True,
        'state': False,
        'fav': 42,
        'lan': 0.0,
        'lng': 0.0,
    }
    agregar_vendedor_ambulante(data3)

    product_1 = {
        'nombre': 'Pizza',
        'imagen': None,
        'icono': 'pizza',
        'categorias': ['Almuerzos'],
        'descripcion': 'Deliciosa pizza hecha con masa casera, viene disponible en 3 tipos:',
        'stock': 20,
        'precio': 1300
    }
    product_2 = {
        'nombre': 'Menú de arroz',
        'imagen': None,
        'icono': 'rice',
        'categorias': ['Almuerzos'],
        'descripcion': 'Almuerzo de arroz con pollo arvejado.',
        'stock': 40,
        'precio': 2500
    }
    product_3 = {
        'nombre': 'Jugo',
        'imagen': None,
        'icono': 'juice',
        'categorias': ['Snack'],
        'descripcion': 'Jugo en caja sabor durazno.',
        'stock': 40,
        'precio': 300
    }

    crear_producto(Vendedor.objects.get(usuario=Usuario.objects.get(user=User.objects.get(username='vendor1'))),
                   product_1)
    crear_producto(Vendedor.objects.get(usuario=Usuario.objects.get(user=User.objects.get(username='vendor2'))),
                   product_2)
    crear_producto(Vendedor.objects.get(usuario=Usuario.objects.get(user=User.objects.get(username='vendor1'))),
                   product_3)

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


def clave_confirmada(data):
    return data['password'] != data['repassword']


def crear_usuario(tipo, form):
    """
    Envia a los datos a la funcion de crear usuario correspondiente.
    :param tipo: String (Numero entre 1 - 3)
    :param form: instancia de clase SignUpForm
    :return:
    """
    if tipo == "1":
        agregar_usuario(form.cleaned_data)
    if tipo == "2":
        if form.cleaned_data['hora_ini'] is None:
            raise KeyError('Ingresa hora de inicio')
        if form.cleaned_data['hora_fin'] is None:
            raise KeyError('Ingresa hora de termino')
        agregar_vendedor_fijo(form.cleaned_data)
    if tipo == "3":
        agregar_vendedor_ambulante(form.cleaned_data)
