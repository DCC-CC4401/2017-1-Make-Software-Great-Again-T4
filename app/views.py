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

from app.forms import LoginForm, EditAccountForm, AddProductForm, EditProductForm, SignUpForm
from app.models import BaseUser, Vendor, Product, SettledVendor, PaymentMethod, Student, Transactions, Category, \
    Alert, \
    Token
from app.utils import create_user, \
    password_confirmed, dist

push_service = FCMNotification(api_key="AIzaSyCKN7gqnUnHEFSPcKpe7YdiXuDJJliObFM")


def index(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('home'))
    return render(request, 'app/index.html', {
        'categories': Category.objects.all()
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
    user = BaseUser.objects.get(user=request.user)
    if user.type == 1:
        return render(request, 'app/home.html', {
            'user': user,
            'categories': Category.objects.all()
        })
    vendor = Vendor.objects.get(user=user)
    update(vendor)
    products = []
    raw_products = Product.objects.filter(vendor=vendor)
    schedule = SettledVendor.objects.get(user=user).schedule() if user.type == 2 else None
    for p in raw_products:
        products.append(p)
    return render(request, 'app/vendedor-main.html', {'user': user, 'vendor': vendor,
                                                      'products': products, 'schedule': schedule})


def stock(request):
    try:
        user = BaseUser.objects.get(user=request.user)
        vendor = Vendor.objects.get(user=user)
        update(vendor)
        products = [i for i in Product.objects.filter(vendor=vendor)]
        return render(request, 'app/stock.html', {'user': user, 'vendor': vendor,
                                                  'products': products})
    except:
        return HttpResponseRedirect(reverse('home'))


def stats(request):
    try:
        user = BaseUser.objects.get(user=request.user)
        vendor = Vendor.objects.get(user=user)
        current_date = datetime.datetime.now().replace(microsecond=0).date()
        transactions = Transactions.objects.filter(vendor=vendor)
        transactions_today = transactions.filter(date=current_date)
        earnings_per_product_today_raw = transactions_today.values('product__name').annotate(quantity=Sum(
            Case(
                When(amount__gte=0, then=1),
                When(amount__lt=0, then=-1),
                default=0,
                output_field=IntegerField())
        ),
            price=Case(
                When(amount__gte=0, then=F('amount')),
                When(amount__lt=0, then=-1 * F('amount')),
                default=0,
                output_field=IntegerField()
            ),
            total=F('price') * F('quantity'))
        earnings_per_product_today_detail = [i for i in earnings_per_product_today_raw]
        earnings_per_product_today = [i for i in earnings_per_product_today_raw.values('product__name', 'total')]
        total_today = transactions_today.values('amount').aggregate(tot=Sum('amount'))['tot']
        total_today = total_today if total_today is not None else 0

        charts = {
            'today': {
                'products': [i['product__name'] for i in earnings_per_product_today],
                'amounts': ['cash_amount'] + [i['total'] for i in earnings_per_product_today]
            },
        }
        return render(request, 'app/stats.html', {'user': user, 'vendor': vendor, 'charts': charts,
                                                  'total': total_today, 'table': earnings_per_product_today_detail
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
        for i in PaymentMethod.objects.all().values():
            self.choices_pay.append((i['method'], i['method']))

    def get(self, request):
        form = SignUpForm()
        form.fields['payment_methods'].choices = self.choices_pay
        return render(request, 'app/signup.html', {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST, request.FILES)
        form.fields['payment_methods'].choices = self.choices_pay
        if form.is_valid():
            if password_confirmed(form.cleaned_data):
                return render(request, 'app/signup.html', {'message': 'Las contraseñas no coinciden', 'form': form})
            try:
                tipo = form.cleaned_data['type']
                create_user(tipo, form)
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
        for i in PaymentMethod.objects.all().values():
            self.choices_pay.append((i['method'], i['method']))

    def get(self, request):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('index'))
        user = BaseUser.objects.get(user=request.user)
        initial = {'first_name': request.user.first_name, 'last_name': request.user.last_name}
        data = {'user': user}
        if user.type == 2:
            ven = SettledVendor.objects.get(user=user)
            initial['start_hour'] = ven.start_hour
            initial['end_hour'] = ven.end_hour

        if user.type >= 2:
            vendor = Vendor.objects.get(user=user)
            data['vendor'] = vendor
            pay = vendor.payment_methods.values()
            payment = [i['method'] for i in pay]
            initial['payment_methods'] = payment
            initial['lat'] = vendor.lat
            initial['lng'] = vendor.lng

        form = EditAccountForm(initial=initial)
        form.fields['payment_methods'].choices = self.choices_pay
        data['form'] = form
        return render(request, 'app/edit_account.html', data)

    def post(self, request):
        form = EditAccountForm(request.POST, request.FILES)
        form.fields['payment_methods'].choices = self.choices_pay
        if not request.user.is_authenticated() or not form.is_valid():
            return self.get(request)
        user = BaseUser.objects.get(user=request.user)
        user.user.first_name = form.cleaned_data['first_name']
        user.user.last_name = form.cleaned_data['last_name']
        if form.cleaned_data['avatar'] is not None:
            user.avatar = form.cleaned_data['avatar']
        user.save()
        try:
            vendor = Vendor.objects.get(user=user)
            pay = form.cleaned_data['payment_methods']
            vendor.formas_pago.clear()
            for i in pay:
                vendor.formas_pago.add(PaymentMethod.objects.get(method=i))
            if user.type == 2:
                vendor.lat = form.cleaned_data['lat']
                vendor.lng = form.cleaned_data['lng']
            vendor.save()
            svendor = SettledVendor.objects.get(user=user)
            svendor.hora_ini = form.cleaned_data['start_hour']
            svendor.end_hour = form.cleaned_data['end_hour']
            svendor.save()
        finally:
            return HttpResponseRedirect('home')


class EditProduct(View):
    categories = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.categories = []
        for i in Category.objects.all().values():
            self.categories.append((i['name'], i['name']))

    def get(self, request, pid):
        try:
            user = BaseUser.objects.get(user=request.user)
            vendor = Vendor.objects.get(user=user)
            products = Product.objects.filter(vendor=vendor)
            product = products.get(id=pid)
            categories = [i['name'] for i in product.categories.values()]
            initial = {'name': product.name, 'price': product.price,
                       'stock': product.stock, 'description': product.description,
                       'categories': categories}
            form = EditProductForm(initial=initial)
            form.fields['categories'].choices = self.categories
            return render(request, 'app/edit_product.html', {'form': form, 'user': user,
                                                             'vendor': vendor, 'product': product})
        except:
            return HttpResponseRedirect(reverse('home'))

    def post(self, request, pid):
        try:
            user = BaseUser.objects.get(user=request.user)
            vendor = Vendor.objects.get(user=user)
            products = Product.objects.filter(vendor=vendor)
            product = products.get(id=pid)
            form = EditProductForm(request.POST, request.FILES)
            form.fields['categories'].choices = self.categories
            if not form.is_valid():
                return self.get(request, pid)
            product.name = form.cleaned_data['name']
            product.price = form.cleaned_data['price']
            product.stock = form.cleaned_data['stock']
            product.description = form.cleaned_data['description']
            if form.cleaned_data['image'] is not None:
                product.image = form.cleaned_data['image']

            product.categories.clear()
            for i in form.cleaned_data['categories']:
                product.categories.add(Category.objects.get(name=i))
            product.save()
        finally:
            return HttpResponseRedirect(reverse('home'))


class AddProduct(View):
    choices = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.choices = []
        for i in Category.objects.all().values():
            self.choices.append((i['name'], i['name']))

    def get(self, request):
        user = BaseUser.objects.get(user=request.user)
        form = AddProductForm()
        form.fields['categories'].choices = self.choices
        return render(request, 'app/add_product.html', {'form': form, 'user': user})

    def post(self, request):
        from app.utils import create_product
        user = BaseUser.objects.get(user=request.user)
        vendor = Vendor.objects.get(user=user)
        form = AddProductForm(request.POST, request.FILES)
        form.fields['categories'].choices = self.choices
        if form.is_valid():
            icon = request.POST.get('icon-button')
            if icon is None:
                # Set default
                icon = 'bread'
            form.cleaned_data['icon'] = icon
            create_product(vendor, form.cleaned_data)

            return HttpResponseRedirect(reverse('home'))
        else:
            form = AddProductForm()
            form.fields['categories'].choices = self.choices
            return render(request, 'app/add_product.html',
                          {'error_message': 'Hubo un error con el formulario', 'form': form, 'user': request.user})


def vendor_info(request, pid):
    try:
        user = None
        is_fav = False
        vendor = Vendor.objects.get(id=pid)
        update(vendor)
        products = []
        raw_products = Product.objects.filter(vendor=vendor)
        schedule = SettledVendor.objects.get(user=vendor.user).schedule() if vendor.user.type == 2 else None
        for p in raw_products:
            products.append(p)
        try:
            user = BaseUser.objects.get(user=request.user)
            buyer = Student.objects.get(user=user)
            if buyer.favorites.filter(user=vendor.user).values().count() != 0:
                is_fav = True
        finally:
            return render(request, 'app/vendor_info.html', {'user': user, 'vendor': vendor,
                                                            'products': products, 'schedule': schedule,
                                                            'is_fav': is_fav})
    except:
        return HttpResponseRedirect(reverse('home'))


def update(ven):
    t = datetime.datetime.now().time()
    if ven.user.type == 2:
        vendor = SettledVendor.objects.get(user=ven.user)
        now = datetime.time(hour=t.hour, minute=t.minute)
        if vendor.start_hour <= now <= vendor.end_hour and not vendor.active:
            vendor.active = True
        if not vendor.start_hour <= now <= vendor.end_hour and vendor.active:
            vendor.active = False
        vendor.save()


def like(request):
    try:
        data = {'is_fav_now': False}
        pid = request.POST.get('id', None)
        vendor = Vendor.objects.get(id=pid)
        buyer = Student.objects.get(user=BaseUser.objects.get(user=request.user))
        if buyer.favorites.filter(user=vendor.user).values().count() != 0:
            buyer.favorites.remove(vendor)
            vendor.favorites_counter -= 1
            data['is_fav_now'] = False
        else:
            buyer.favorites.add(vendor)
            vendor.favorites_counter += 1
            data['is_fav_now'] = True
        buyer.save()
        vendor.save()
        data['favorites'] = vendor.favorites_counter
        return JsonResponse(data)
    except:
        return HttpResponseRedirect(reverse('home'))


def check_in(request):
    user = BaseUser.objects.get(user=request.user)
    vendor = Vendor.objects.get(user=user)

    if not vendor.active:
        vendor.active = True
        vendor.lat = request.POST.get('lat', 0.0)
        vendor.lng = request.POST.get('lng', 0.0)
    else:
        vendor.active = False
    vendor.save()
    return JsonResponse({
        'is_active': vendor.state()
    })


def delete_product(request):
    pid = request.POST.get('id')
    Product.objects.get(id=pid).delete()
    time.sleep(100)
    return JsonResponse({'success': True})


def delete_account(request):
    user = BaseUser.objects.get(user=request.user).user
    auth.logout(request)
    user.delete()
    return JsonResponse({'success': True})


class ActiveVendors(View):
    @staticmethod
    def post(request):
        def get_favorites():
            try:
                user = BaseUser.objects.get(user=request.user)
                return Student.objects.get(user=user).favorites.all()
            except:
                return []

        def has_stock(vendor):
            return Product.objects.filter(vendor=vendor, stock__gt=0).exists()

        for i in SettledVendor.objects.all():
            update(i)
        active = Vendor.objects.filter(active=True)
        favorites = set(get_favorites())

        return JsonResponse([{**vendor.serialize(), **{
            'fav': vendor in favorites
        }} for vendor in active if has_stock(vendor)], safe=False)


def adm_stock(request):
    user = BaseUser.objects.get(user=request.user)
    pid = request.POST.get('id')
    vendor = Vendor.objects.get(user=user)
    product = Product.objects.get(id=pid)
    action = request.POST.get('action')
    if action == 'true':  # suma
        product.stock += 1
        p = Transactions.objects.create(vendor=vendor, date=datetime.datetime.now().date(),
                                        amount=-product.price,
                                        product=product)
        p.save()
    elif product.stock > 0:
        product.stock -= 1
        p = Transactions.objects.create(vendor=vendor, date=datetime.datetime.now().date(), amount=product.price,
                                        product=product)
        p.save()

    product.save()
    return JsonResponse({'new_stock': product.stock})


def interval_chart(request):
    try:
        low_raw = request.POST['low']
        high_raw = request.POST['high']
        low = datetime.datetime.strptime(low_raw, '%d-%m-%Y').date()
        high = datetime.datetime.strptime(high_raw, '%d-%m-%Y').date()
        user = BaseUser.objects.get(user=request.user)
        vendor = Vendor.objects.get(user=user)
        delta = (high - low).days
        transactions = Transactions.objects.filter(vendor=vendor)
        days = {}
        earnings = [None] * (delta + 1)
        for i in range(delta, -1, -1):
            key = high - datetime.timedelta(days=+i)
            days[key] = i
            earnings[i] = ([key.strftime('%d-%m-%Y'), 0])
        earnigs_per_day = [i for i in transactions.filter(
            date__gte=low, date__lte=high).values('date').annotate(cash_amount=Sum('amount'))]
        for j in earnigs_per_day:
            earnings[days[j['date']]][1] += j['cash_amount']
        data = {
            'dates': ['x'] + [i[0] for i in earnings][::-1],
            'amounts': ['cash_amount'] + [j[1] for j in earnings][::-1]
        }
        return JsonResponse(data)
    except:
        return JsonResponse({})


def alert(request):
    if request.method == 'POST':
        try:
            alert = Alert(user=BaseUser.objects.get(user=request.user), posX=request.POST["lat"],
                          posY=request.POST["lng"])
            alert.save()

            tokens = [i for i in Token.objects.all()]

            filtered_tokens = list(filter(
                lambda x: dist(x.vendor.lat, x.vendor.lng, request.POST["lat"], request.POST["lng"]) <= 50,
                tokens))
            registration_ids = [i.token for i in filtered_tokens]
            print(registration_ids)
            message_title = "Beau-Chef"
            message_body = "Vienen los Carabineros"
            push_service.notify_multiple_devices(registration_ids=registration_ids,
                                                 message_title=message_title, message_body=message_body)
            return JsonResponse({})
        except:
            return render(request, 'app/index.html')


def token(request):
    user = BaseUser.objects.get(user=request.user)
    vendor = Vendor.objects.get(user=user)
    tokens = Token.objects.filter(vendor=vendor)
    code = request.POST.get('id', '')
    tokens_code = tokens.filter(code=code)
    if len(tokens_code) == 0:  # dispositivo nuevo
        tok = Token(vendor=vendor, token=request.POST.get('token', ''), code=code)
        tok.save()
    else:  # dispositivo ya registrado
        tok = tokens_code.first()
        tok.token = request.POST.get('token', '')
        tok.save()
    return JsonResponse({})
