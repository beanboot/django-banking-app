from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import RegisterForm
from payapp.models import Account
from django.contrib.auth import authenticate, login, logout
import requests, decimal

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )

            currency = form.cleaned_data['currency']

            # Call the REST service to convert 500 GBP to the user's currency
            response = requests.get(
                f'http://localhost:8000/api/conversion/GBP/{currency}/500/'
            )
            data = response.json()
            balance = decimal.Decimal(str(data['converted_amount']))

            Account.objects.create(
                user=user,
                balance=balance,
                currency=currency
            )

            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('login')