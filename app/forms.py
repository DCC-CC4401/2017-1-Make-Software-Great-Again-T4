# -*- coding: utf-8 -*-

from django import forms
from app.models import FormasDePago, Producto
from django.contrib.auth.models import User

DIAS = [
    (1, 'Lunes'),
    (2, 'Martes'),
    (3, 'Miércoles'),
    (4, 'Jueves'),
    (5, 'Viernes'),
    (6, 'Sábado'),
    (7, 'Domingo')
]


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)

    class Meta:
        model = User


class EditarCuenta(forms.Form):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'dropify'}))
    choices = []
    formas_pago = forms.MultipleChoiceField(required=False, choices=choices,
                                            widget=forms.SelectMultiple(attrs={'class': 'multiple'}))
    # dias_ini = forms.ChoiceField(choices=DIAS, required=False)
    # dias_fin = forms.ChoiceField(choices=DIAS, required=False)
    hora_ini = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    hora_fin = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    lat = forms.DecimalField(max_digits=10, decimal_places=7, required=False)
    lng = forms.DecimalField(max_digits=10, decimal_places=7, required=False)


# Hereda los atributos del vendedor
class SignUpForm(EditarCuenta):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    repassword = forms.CharField(widget=forms.PasswordInput, required=False)
    elecciones_tipo = ((0, 'Admin'), (1, 'Alumno'), (2, 'Vendedor Fijo'), (3, 'Vendedor Ambulante'))
    tipo = forms.ChoiceField(widget=forms.Select(attrs={'class': 'multiple'}),
                             choices=elecciones_tipo, required=False)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    lat = forms.DecimalField(max_digits=10, decimal_places=7, required=False)
    lng = forms.DecimalField(max_digits=10, decimal_places=7, required=False)


class AgregarProductoForm(forms.Form):
    nombre = forms.CharField(max_length=200, required=True)
    choices = []
    categorias = forms.MultipleChoiceField(required=False, choices=choices,
                                           widget=forms.SelectMultiple(attrs={'class': 'multiple'}))
    descripcion = forms.CharField(required=False, max_length=500,
                                  widget=forms.Textarea(attrs={'class': 'materialize-textarea'}))
    stock = forms.IntegerField(required=False)
    precio = forms.IntegerField(required=True)
    imagen = forms.ImageField(required=False)

    class Meta:
        model = Producto


class EditarProductoForm(forms.Form):
    nombre = forms.CharField(max_length=200, required=False)
    elecciones = []
    categorias = forms.MultipleChoiceField(required=False, choices=elecciones,
                                           widget=forms.SelectMultiple(attrs={'class': 'multiple'}))
    descripcion = forms.CharField(required=False, max_length=500,
                                  widget=forms.Textarea(attrs={'class': 'materialize-textarea'}))
    stock = forms.IntegerField(required=False)
    precio = forms.IntegerField(required=False)
    imagen = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'dropify'}))

    class Meta:
        model = Producto
