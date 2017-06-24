# -*- coding: utf-8 -*-
import datetime
import time

from django.contrib import auth
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.db.models import Case, IntegerField, F, Sum, When
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from pyfcm import FCMNotification

from app.forms import LoginForm, EditarCuenta, AgregarProductoForm, EditarProductoForm, SignUpForm
from app.models import Usuario, Vendedor, Producto, VendedorFijo, FormasDePago, Alumno, Transacciones, Categoria, \
    Alerta, \
    Token
from app.utils import crear_usuario, \
    clave_confirmada, dist

push_service = FCMNotification(api_key="AIzaSyCKN7gqnUnHEFSPcKpe7YdiXuDJJliObFM")


def index(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('home'))
    return render(request, 'app/index.html', {
        'categories': Categoria.objects.all()
    })


class Login(View):
    @staticmethod
    def get(request):
        form = LoginForm()
        return render(request, 'app/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if not form.is_valid():
            self.get(request)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'app/login.html', {
                'login_message': 'Nombre de Usuario o Contraseña erroneos', 'form': form, })
        if not user.is_active:
            return render(request, 'app/login.html', {
                'login_message': 'Su cuenta ha sido banneada', 'form': form, })
        auth.login(request, user)
        return HttpResponseRedirect(reverse('home'))


def home(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login'))
    user = Usuario.objects.get(user=request.user)
    if user.tipo == 1:
        return render(request, 'app/home.html', {
            'user': user,
            'categories': Categoria.objects.all()
        })
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
    try:
        user = Usuario.objects.get(user=request.user)
        vendor = Vendedor.objects.get(usuario=user)
        update(vendor)
        products = [i for i in Producto.objects.filter(vendedor=vendor)]
        return render(request, 'app/stock.html', {'user': user, 'vendor': vendor,
                                                  'products': products})
    except:
        return HttpResponseRedirect(reverse('home'))


def stats(request):
    try:
        user = Usuario.objects.get(user=request.user)
        vendor = Vendedor.objects.get(usuario=user)
        current_date = datetime.datetime.now().replace(microsecond=0).date()
        transactions = Transacciones.objects.filter(vendedor=vendor)
        transactions_today = transactions.filter(fecha=current_date)
        earnigs_per_product_today_raw = transactions_today.values('producto__nombre').annotate(cant=Sum(
            Case(
                When(cantidad__gte=0, then=1),
                When(cantidad__lt=0, then=-1),
                default=0,
                output_field=IntegerField())
        ),
            precio=Case(
                When(cantidad__gte=0, then=F('cantidad')),
                When(cantidad__lt=0, then=-1 * F('cantidad')),
                default=0,
                output_field=IntegerField()
            ),
            total=F('precio') * F('cant'))
        earnigs_per_product_today_detail = [i for i in earnigs_per_product_today_raw]
        earnigs_per_product_today = [i for i in earnigs_per_product_today_raw.values('producto__nombre', 'total')]
        total_today = transactions_today.values('cantidad').aggregate(tot=Sum('cantidad'))['tot']
        total_today = total_today if total_today is not None else 0

        charts = {
            'today': {
                'products': [i['producto__nombre'] for i in earnigs_per_product_today],
                'amounts': ['monto'] + [i['total'] for i in earnigs_per_product_today]
            },
        }
        return render(request, 'app/stats.html', {'user': user, 'vendor': vendor, 'charts': charts,
                                                  'total': total_today, 'table': earnigs_per_product_today_detail
                                                  })
    except:
        return HttpResponseRedirect(reverse('home'))


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('index'))


def test(request):
    return render(request, 'app/test.html')


class SignUp(View):
    choices_pay = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.choices_pay = []
        for i in FormasDePago.objects.all().values():
            self.choices_pay.append((i['metodo'], i['metodo']))

    def get(self, request):
        form = SignUpForm()
        form.fields['formas_pago'].choices = self.choices_pay
        return render(request, 'app/signup.html', {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST, request.FILES)
        form.fields['formas_pago'].choices = self.choices_pay
        if form.is_valid():
            if clave_confirmada(form.cleaned_data):
                return render(request, 'app/signup.html', {'message': 'Las contraseñas no coinciden', 'form': form})
            try:
                tipo = form.cleaned_data['tipo']
                crear_usuario(tipo, form)
                return render(request, 'app/login.html', {
                    'message': 'Cuenta creada satisfactoriamente', 'form': form, })
            except IntegrityError:
                return render(request, 'app/signup.html', {'message': 'El usuario ya esta en uso', 'form': form})
            except KeyError as e:
                return render(request, 'app/signup.html', {'message': e.args[0], 'form': form})
        else:
            form = LoginForm()
        return render(request, 'app/login.html', {'form': form, })


class EditAccount(View):
    choices_pay = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.choices_pay = []
        for i in FormasDePago.objects.all().values():
            self.choices_pay.append((i['metodo'], i['metodo']))

    def get(self, request):
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
            initial['lat'] = vendor.lat
            initial['lng'] = vendor.lng

        form = EditarCuenta(initial=initial)
        form.fields['formas_pago'].choices = self.choices_pay
        data['form'] = form
        return render(request, 'app/edit_account.html', data)

    def post(self, request):
        form = EditarCuenta(request.POST, request.FILES)
        form.fields['formas_pago'].choices = self.choices_pay
        if not request.user.is_authenticated() or not form.is_valid():
            return self.get(request)
        user = Usuario.objects.get(user=request.user)
        user.user.first_name = form.cleaned_data['first_name']
        user.user.last_name = form.cleaned_data['last_name']
        if form.cleaned_data['avatar'] is not None:
            user.avatar = form.cleaned_data['avatar']
        user.save()
        try:
            vendor = Vendedor.objects.get(usuario=user)
            pay = form.cleaned_data['formas_pago']
            vendor.formas_pago.clear()
            for i in pay:
                vendor.formas_pago.add(FormasDePago.objects.get(metodo=i))
            if user.tipo == 2:
                vendor.lat = form.cleaned_data['lat']
                vendor.lng = form.cleaned_data['lng']
            vendor.save()
            svendor = VendedorFijo.objects.get(usuario=user)
            svendor.hora_ini = form.cleaned_data['hora_ini']
            svendor.hora_fin = form.cleaned_data['hora_fin']
            svendor.save()
        finally:
            return HttpResponseRedirect('home')


class EditProduct(View):
    categories = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.categories = []
        for i in Categoria.objects.all().values():
            self.categories.append((i['nombre'], i['nombre']))

    def get(self, request, pid):
        try:
            user = Usuario.objects.get(user=request.user)
            vendor = Vendedor.objects.get(usuario=user)
            products = Producto.objects.filter(vendedor=vendor)
            product = products.get(id=pid)
            categories = [i['nombre'] for i in product.categorias.values()]
            initial = {'nombre': product.nombre, 'precio': product.precio,
                       'stock': product.stock, 'descripcion': product.descripcion,
                       'categorias': categories}
            form = EditarProductoForm(initial=initial)
            form.fields['categorias'].choices = self.categories
            return render(request, 'app/edit_product.html', {'form': form, 'user': user,
                                                             'vendor': vendor, 'product': product})
        except:
            return HttpResponseRedirect(reverse('home'))

    def post(self, request, pid):
        try:
            user = Usuario.objects.get(user=request.user)
            vendor = Vendedor.objects.get(usuario=user)
            products = Producto.objects.filter(vendedor=vendor)
            product = products.get(id=pid)
            form = EditarProductoForm(request.POST, request.FILES)
            form.fields['categorias'].choices = self.categories
            if not form.is_valid():
                return self.get(request, pid)
            product.nombre = form.cleaned_data['nombre']
            product.precio = form.cleaned_data['precio']
            product.stock = form.cleaned_data['stock']
            product.descripcion = form.cleaned_data['descripcion']
            if form.cleaned_data['imagen'] is not None:
                product.imagen = form.cleaned_data['imagen']

            product.categorias.clear()
            for i in form.cleaned_data['categorias']:
                product.categorias.add(Categoria.objects.get(nombre=i))
            product.save()
        finally:
            return HttpResponseRedirect(reverse('home'))


class AgregarProducto(View):
    choices = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.choices = []
        for i in Categoria.objects.all().values():
            self.choices.append((i['nombre'], i['nombre']))

    def get(self, request):
        user = Usuario.objects.get(user=request.user)
        form = AgregarProductoForm()
        form.fields['categorias'].choices = self.choices
        return render(request, 'app/agregar_producto.html', {'form': form, 'user': user})

    def post(self, request):
        from app.utils import crear_producto
        user = Usuario.objects.get(user=request.user)
        vendedor = Vendedor.objects.get(usuario=user)
        form = AgregarProductoForm(request.POST, request.FILES)
        form.fields['categorias'].choices = self.choices
        if form.is_valid():
            icono = request.POST.get('icon-button')
            if icono is None:
                # Set default
                icono = 'bread'
            form.cleaned_data['icono'] = icono
            crear_producto(vendedor, form.cleaned_data)

            return HttpResponseRedirect(reverse('home'))
        else:
            form = AgregarProductoForm()
            form.fields['categorias'].choices = self.choices
            return render(request, 'app/agregar_producto.html',
                          {'error_message': 'Hubo un error con el formulario', 'form': form, 'user': request.user})


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
        try:
            user = Usuario.objects.get(user=request.user)
            buyer = Alumno.objects.get(usuario=user)
            if buyer.favorites.filter(usuario=vendor.usuario).values().count() != 0:
                is_fav = True
        finally:
            return render(request, 'app/vendor_info.html', {'user': user, 'vendor': vendor,
                                                            'products': products, 'schedule': schedule,
                                                            'is_fav': is_fav})
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

    if not vendor.activo:
        vendor.activo = True
        vendor.lat = request.POST.get('lat', 0.0)
        vendor.lng = request.POST.get('lng', 0.0)
    else:
        vendor.activo = False
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


class ActiveVendors(View):
    @staticmethod
    def post(request):
        def get_favorites():
            try:
                user = Usuario.objects.get(user=request.user)
                return Alumno.objects.get(usuario=user).favorites.all()
            except:
                return []

        def has_stock(vendor):
            return Producto.objects.filter(vendedor=vendor, stock__gt=0).exists()
        for i in VendedorFijo.objects.all():
            update(i)
        active = Vendedor.objects.filter(activo=True)
        favorites = set(get_favorites())

        return JsonResponse([{**vendor.serialize(), **{
            'fav': vendor in favorites
        }} for vendor in active if has_stock(vendor)], safe=False)


def adm_stock(request):
    user = Usuario.objects.get(user=request.user)
    pid = request.POST.get('id')
    vendor = Vendedor.objects.get(usuario=user)
    product = Producto.objects.get(id=pid)
    action = request.POST.get('action')
    if action == 'true':  # suma
        product.stock += 1
        p = Transacciones.objects.create(vendedor=vendor, fecha=datetime.datetime.now().date(),
                                         cantidad=-product.precio,
                                         producto=product)
        p.save()
    elif product.stock > 0:
        product.stock -= 1
        p = Transacciones.objects.create(vendedor=vendor, fecha=datetime.datetime.now().date(), cantidad=product.precio,
                                         producto=product)
        p.save()

    product.save()
    return JsonResponse({'new_stock': product.stock})


def interval_chart(request):
    try:
        low_raw = request.POST['low']
        high_raw = request.POST['high']
        low = datetime.datetime.strptime(low_raw, '%d-%m-%Y').date()
        high = datetime.datetime.strptime(high_raw, '%d-%m-%Y').date()
        user = Usuario.objects.get(user=request.user)
        vendor = Vendedor.objects.get(usuario=user)
        delta = (high - low).days
        transactions = Transacciones.objects.filter(vendedor=vendor)
        days = {}
        earnings = [None] * (delta + 1)
        for i in range(delta, -1, -1):
            key = high - datetime.timedelta(days=+i)
            days[key] = i
            earnings[i] = ([key.strftime('%d-%m-%Y'), 0])
        earnigs_per_day = [i for i in transactions.filter(
            fecha__gte=low, fecha__lte=high).values('fecha').annotate(monto=Sum('cantidad'))]
        for j in earnigs_per_day:
            earnings[days[j['fecha']]][1] += j['monto']
        data = {
            'dates': ['x'] + [i[0] for i in earnings][::-1],
            'amounts': ['monto'] + [j[1] for j in earnings][::-1]
        }
        return JsonResponse(data)
    except:
        return JsonResponse({})


def alerta(request):
    if request.method == 'POST':
        try:
            alert = Alerta(usuario=Usuario.objects.get(user=request.user), posX=request.POST["lat"],
                           posY=request.POST["lng"])
            alert.save()

            tokens = [i for i in Token.objects.all()]

            filtered_tokens = list(filter(
                lambda x: dist(x.vendedor.lat, x.vendedor.lng, request.POST["lat"], request.POST["lng"]) <= 50,
                tokens))
            registration_ids = [i.token for i in filtered_tokens]
            message_title = "Beau-Chef"
            message_body = "Vienen los Carabineros"
            push_service.notify_multiple_devices(registration_ids=registration_ids,
                                                 message_title=message_title, message_body=message_body)
            return JsonResponse({})
        except:
            return render(request, 'app/index.html')


def token(request):
    user = Usuario.objects.get(user=request.user)
    tok = Token(vendedor=Vendedor.objects.get(usuario=user), token=request.POST['token'])
    tok.save()
    return JsonResponse({})
