# -*- coding: utf-8 -*-

from django import forms
from app.models import PaymentMethod, Product
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)

    class Meta:
        model = User


class EditAccountForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'dropify'}))
    choices = []
    payment_methods = forms.MultipleChoiceField(required=False, choices=choices,
                                                widget=forms.SelectMultiple(attrs={'class': 'multiple'}))
    init_hour = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    end_hour = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False)
    lat = forms.DecimalField(max_digits=10, decimal_places=7, required=False)
    lng = forms.DecimalField(max_digits=10, decimal_places=7, required=False)


class SignUpForm(EditAccountForm):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    repassword = forms.CharField(widget=forms.PasswordInput, required=False)
    choices = ((1, 'Alumno'), (2, 'Vendedor Fijo'), (3, 'Vendedor Ambulante'))
    type = forms.ChoiceField(widget=forms.Select(attrs={'class': 'multiple'}),
                             choices=choices, required=False)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    lat = forms.DecimalField(max_digits=10, decimal_places=7, required=False)
    lng = forms.DecimalField(max_digits=10, decimal_places=7, required=False)


class AddProductForm(forms.Form):
    name = forms.CharField(max_length=200, required=True)
    choices = []
    categories = forms.MultipleChoiceField(required=False, choices=choices,
                                           widget=forms.SelectMultiple(attrs={'class': 'multiple'}))
    description = forms.CharField(required=False, max_length=500,
                                  widget=forms.Textarea(attrs={'class': 'materialize-textarea'}))
    stock = forms.IntegerField(required=False)
    price = forms.IntegerField(required=True)
    image = forms.ImageField(required=False)

    class Meta:
        model = Product


class EditProductForm(forms.Form):
    name = forms.CharField(max_length=200, required=False)
    elecciones = []
    categories = forms.MultipleChoiceField(required=False, choices=elecciones,
                                           widget=forms.SelectMultiple(attrs={'class': 'multiple'}))
    description = forms.CharField(required=False, max_length=500,
                                  widget=forms.Textarea(attrs={'class': 'materialize-textarea'}))
    stock = forms.IntegerField(required=False)
    price = forms.IntegerField(required=False)
    image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'dropify'}))

    class Meta:
        model = Product
