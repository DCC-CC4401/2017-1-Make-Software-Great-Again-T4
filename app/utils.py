# coding=utf-8

import datetime

from app.models import *


def add_django_user(data):
    user = User.objects.create_user(username=data['username'], email=data['email'], password=data['password'])
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.save()


def add_user(data):
    add_django_user(data)
    user = User.objects.get(username=data['username'])
    p = BaseUser(user=user, avatar=data['avatar'], type=data['type'])
    p.save()
    print("User saved")


def add_settled_vendor(data):
    add_user(data)
    user = BaseUser.objects.get(user=User.objects.get(username=data['username']))
    p = SettledVendor(user=user, start_hour=data['start_hour'], end_hour=data['end_hour'],
                      lat=data['lat'], lng=data['lng'])
    p.save()
    for i in data['payment_methods']:
        p.payment_methods.add(PaymentMethod.objects.get(method=i))
    p.save()
    print("Settled vendor saved")


def add_ambulant_vendor(data):
    add_user(data)
    user = BaseUser.objects.get(user=User.objects.get(username=data['username']))

    p = AmbulantVendor(user=user)
    p.save()
    for i in data['payment_methods']:
        p.payment_methods.add(PaymentMethod.objects.get(method=i))
    p.save()
    print("Ambulant vendor saved")


def create_product(vendor, data):
    icon = ProductIcon.objects.get(name=data['icon'])
    p = Product(vendor=vendor, name=data['name'], image=data['image'], icon=icon,
                description=data['description'], stock=data['stock'], price=data['price'])
    p.save()
    for i in data['categories']:
        p.categories.add(Category.objects.get(name=i))
    p.save()
    print("Product saved")


def add_category(cat):
    p = Category(name=cat)
    p.save()


def add_product_icon(data):
    p_icon = ProductIcon(name=data['name'], icon=data['icon'])
    p_icon.save()


def add_payment(pay):
    p = PaymentMethod(method=pay)
    p.save()


def add_buyer(data):
    add_user(data)
    user = BaseUser.objects.get(user=User.objects.get(username=data['username']))
    p = Student.objects.create(user=user)
    p.save()


def add_stat(data):
    user = BaseUser.objects.get(user=User.objects.get(username=data['username']))
    vendor = Vendor.objects.get(user=user)
    products = Product.objects.filter(vendor=vendor).filter(name=data['product_name'])
    if products.count() != 0:
        product = Product.objects.filter(vendor=vendor).filter(name=data['product_name']).first()
        p = Transactions.objects.create(vendor=vendor, date=data['date'],  amount=data['amount'], product=product)
        p.save()



def password_confirmed(data):
    return data['password'] != data['repassword']


def create_user(type, form):
    """
    Envia a los datos a la funcion de crear usuario correspondiente.
    :param type: String (Numero entre 1 - 3)
    :param form: instancia de clase SignUpForm
    :return:
    """
    if type == "1":
        add_user(form.cleaned_data)
    if type == "2":
        print(form.cleaned_data)
        if form.cleaned_data['start_hour'] is None:
            raise KeyError('Ingresa hora de inicio')
        if form.cleaned_data['end_hour'] is None:
            raise KeyError('Ingresa hora de termino')
        if form.cleaned_data['lat'] is None or form.cleaned_data['lng'] is None:
            raise KeyError('Ingresa posición en el mapa')
        add_settled_vendor(form.cleaned_data)
    if type == "3":
        add_ambulant_vendor(form.cleaned_data)


def dist(lat1, lng1, lat2, lng2):
    from geopy.distance import vincenty
    init = (lat1, lng1)
    out = (lat2, lng2)
    print(init)
    print(out)
    return vincenty(init, out).meters


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
        'type': 2,
        'payment_methods': ['efectivo', 'tarjeta'],
        'state': True,
        'fav': 42,
        'lat': -33.457885,
        'lng': -70.663808,
        'hora_ini': datetime.time(hour=12, minute=0),
        'hora_fin': datetime.time(hour=13, minute=0)
    }
    add_settled_vendor(data1)

    data2 = {
        'username': 'buyer',
        'email': 'test@prueba.cl',
        'password': '1234',
        'first_name': 'Robinson',
        'last_name': 'Castro',
        'avatar': None,
        'type': 1,
    }
    add_buyer(data2)
    buyer = Student.objects.get(user=BaseUser.objects.get(user=User.objects.get(username=data2['username'])))
    buyer.favorites.add(
        Vendor.objects.get(user=BaseUser.objects.get(user=User.objects.get(username=data1['username']))))
    buyer.save()
    p = Vendor.objects.get(user=BaseUser.objects.get(user=User.objects.get(username='vendor1')))
    p.numero_favoritos = +1
    p.save()

    data3 = {
        'username': 'vendor2',
        'email': 'test@prueba.cl',
        'password': '1234',
        'first_name': 'Andres',
        'last_name': 'Olivares',
        'avatar': None,
        'type': 3,
        'payment_methods': ['efectivo'],
        'stack': True,
        'state': False,
        'fav': 42,
        'lat': -33.458085,
        'lng': -70.663808,
    }
    add_ambulant_vendor(data3)

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

    create_product(Vendor.objects.get(user=BaseUser.objects.get(user=User.objects.get(username='vendor1'))),
                   product_1)
    create_product(Vendor.objects.get(user=BaseUser.objects.get(user=User.objects.get(username='vendor2'))),
                   product_2)
    create_product(Vendor.objects.get(user=BaseUser.objects.get(user=User.objects.get(username='vendor1'))),
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
