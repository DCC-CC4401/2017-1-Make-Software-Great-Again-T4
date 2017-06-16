# -*- coding: utf-8 -*-
import datetime
import time
from django.contrib import auth
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View

from app.forms import LoginForm, EditarCuenta, EditarProductoForm
from app.models import Usuario, Vendedor, Producto, VendedorFijo, FormasDePago, Alumno


def index(request):
    return render(request, 'app/index.html')


def login(request):
    form = LoginForm(request.POST)
    if form.is_valid() and request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(reverse('home'))
            else:
                return render(request, 'app/login.html', {
                    'login_message': 'Su cuenta ha sido banneada', 'form': form, })
        else:
            return render(request, 'app/login.html', {
                'login_message': 'Nombre de Usuario o Contraseña erroneos', 'form': form, })
    else:
        form = LoginForm()
    return render(request, 'app/login.html', {'form': form, })


def home(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login'))
    user = Usuario.objects.get(user=request.user)
    if user.tipo == 1:
        return render(request, 'app/home.html', {'user': user})
    vendor = Vendedor.objects.get(usuario=user)
    update(vendor)
    products = []
    raw_products = Producto.objects.filter(vendedor=vendor)
    schedule = VendedorFijo.objects.get(usuario=user).schedule() if user.tipo == 2 else None
    for p in raw_products:
        products.append(p)
    return render(request, 'app/vendedor-main.html', {'user': user, 'vendor': vendor,
                                                      'products': products, 'schedule': schedule})


def stock(request):
    return None


def stats(request):
    return None


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('index'))


def test(request):
    return render(request, 'app/test.html')


def signup(request):
    return None


class EditAccount(View):
    @staticmethod
    def get(request):
        choices = []
        for i in FormasDePago.objects.all().values():
            choices.append((i['metodo'], i['metodo']))

        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('index'))
        user = Usuario.objects.get(user=request.user)
        initial = {'first_name': request.user.first_name, 'last_name': request.user.last_name}
        data = {'user': user}
        if user.tipo == 2:
            ven = VendedorFijo.objects.get(usuario=user)
            initial['hora_ini'] = ven.hora_ini
            initial['hora_fin'] = ven.hora_fin

        if user.tipo >= 2:
            vendor = Vendedor.objects.get(usuario=user)
            data['vendor'] = vendor
            pay = vendor.formas_pago.values()
            payment = [i['metodo'] for i in pay]
            initial['formas_pago'] = payment

        form = EditarCuenta(initial=initial)
        form.fields['formas_pago'].choices = choices
        data['form'] = form
        return render(request, 'app/edit_account.html', data)

    @staticmethod
    def post(request):
        choices = []
        for i in FormasDePago.objects.all().values():
            choices.append((i['metodo'], i['metodo']))
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('index'))
        form = EditarCuenta(request.POST, request.FILES)
        form.fields['formas_pago'].choices = choices
        user = Usuario.objects.get(user=request.user)
        if not form.is_valid():
            return HttpResponseRedirect(reverse('edit_account'))

        user.user.first_name = form.cleaned_data['first_name']
        user.user.last_name = form.cleaned_data['last_name']
        if form.cleaned_data['avatar'] is not None:
            user.avatar = form.cleaned_data['avatar']
            user.save()
        if user.tipo == 1:
            user.save()
            return HttpResponseRedirect(reverse('home'))
        vendor = Vendedor.objects.get(usuario=user)
        if user.tipo == 2:
            svendor = VendedorFijo.objects.get(usuario=user)
            svendor.hora_ini = form.cleaned_data['hora_ini']
            svendor.hora_fin = form.cleaned_data['hora_fin']
            svendor.save()
        pay = form.cleaned_data['formas_pago']
        vendor.formas_pago.clear()
        for i in pay:
            vendor.formas_pago.add(FormasDePago.objects.get(metodo=i))
        vendor.save()
        user.save()
        return HttpResponseRedirect('home')


class EditProduct(View):
    @staticmethod
    def get(request, pid):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('index'))
        user = Usuario.objects.get(user=request.user)
        if user.tipo == 1:
            return HttpResponseRedirect(reverse('home'))
        vendor = Vendedor.objects.get(usuario=user)
        products = Producto.objects.filter(vendedor=vendor)
        try:
            product = products.get(id=pid)
            initial = {'nombre': product.nombre, 'precio': product.precio,
                       'stock': product.stock, 'descripcion': product.descripcion}
            form = EditarProductoForm(initial=initial)
            return render(request, 'app/edit_product.html', {'form': form, 'user': user,
                                                             'vendor': vendor, 'product': product})
        except:
            return HttpResponseRedirect(reverse('home'))

    def post(self, request, pid):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('index'))
        user = Usuario.objects.get(user=request.user)
        if user.tipo == 1:
            return HttpResponseRedirect(reverse('home'))

        vendor = Vendedor.objects.get(usuario=user)
        products = Producto.objects.filter(vendedor=vendor)
        try:
            product = products.get(id=pid)
            form = EditarProductoForm(request.POST, request.FILES)
            if not form.is_valid():
                self.get(request, pid)
            product.nombre = form.cleaned_data['nombre']
            product.precio = form.cleaned_data['precio']
            product.stock = form.cleaned_data['stock']
            product.descripcion = form.cleaned_data['descripcion']
            if form.cleaned_data['imagen'] is not None:
                product.imagen = form.cleaned_data['imagen']
            product.save()
        finally:
            return HttpResponseRedirect(reverse('home'))


def vendor_info(request, pid):
    try:
        user = None
        is_fav = False

        vendor = Vendedor.objects.get(id=pid)
        update(vendor)
        products = []
        raw_products = Producto.objects.filter(vendedor=vendor)
        schedule = VendedorFijo.objects.get(usuario=vendor.usuario).schedule() if vendor.usuario.tipo == 2 else None
        for p in raw_products:
            products.append(p)

        if request.user.is_authenticated():
            user = Usuario.objects.get(user=request.user)
            if user.tipo == 1:
                buyer = Alumno.objects.get(usuario=user)
                if buyer.favorites.filter(usuario=vendor.usuario).values().count() != 0:
                    is_fav = True

        return render(request, 'app/vendor_info.html', {'user': user, 'vendor': vendor,
                                                        'products': products, 'schedule': schedule, 'is_fav': is_fav})
    except:
        return HttpResponseRedirect(reverse('home'))


def update(ven):
    t = datetime.datetime.now().time()
    if ven.usuario.tipo == 2:
        vendor = VendedorFijo.objects.get(usuario=ven.usuario)
        now = datetime.time(hour=t.hour, minute=t.minute)
        if vendor.hora_ini <= now <= vendor.hora_fin and not vendor.activo:
            vendor.activo = True
        if not vendor.hora_ini <= now <= vendor.hora_fin and vendor.activo:
            vendor.activo = False
        vendor.save()


def like(request):
    try:
        data = {'is_fav_now': False}
        pid = request.POST.get('id', None)
        vendor = Vendedor.objects.get(id=pid)
        buyer = Alumno.objects.get(usuario=Usuario.objects.get(user=request.user))
        if buyer.favorites.filter(usuario=vendor.usuario).values().count() != 0:
            buyer.favorites.remove(vendor)
            vendor.numero_favoritos -= 1
            data['is_fav_now'] = False
        else:
            buyer.favorites.add(vendor)
            vendor.numero_favoritos += 1
            data['is_fav_now'] = True
        buyer.save()
        vendor.save()
        data['favorites'] = vendor.numero_favoritos
        return JsonResponse(data)
    except:
        return HttpResponseRedirect(reverse('home'))


def check_in(request):
    user = Usuario.objects.get(user=request.user)
    vendor = Vendedor.objects.get(usuario=user)

    vendor.activo = True if not vendor.activo else False
    vendor.save()

    return JsonResponse({
        'is_active': vendor.activo
    })


def delete_product(request):
    pid = request.POST.get('id')
    Producto.objects.get(id=pid).delete()
    time.sleep(100)
    return JsonResponse({'success': True})


def delete_account(request):
    user = Usuario.objects.get(user=request.user).user
    auth.logout(request)
    user.delete()
    return JsonResponse({'success': True})


ADMIN = 0
ALUMNO = 1
VENDEDOR_FIJO = 2
VENDEDOR_AMBULANTE = 3


class ActiveVendors(View):
    @staticmethod
    def post(request):
        def get_favorites():
            try:
                user = Usuario.objects.get(user=request.user)
                return Alumno.objects.get(usuario=user).favorites.all()
            except:
                return []

        active = list(Vendedor.objects.filter(activo=True))
        favorites = list(get_favorites())
        vendors = set(active + favorites)
        return JsonResponse([{
            'position': {'lat': float(vendor.lat), 'lng': float(vendor.lng)},
            'fav': vendor in favorites
        } for vendor in vendors], safe=False)
