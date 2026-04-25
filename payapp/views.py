from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import Account, Transaction, PaymentRequest
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
import decimal, requests
from register.forms import RegisterForm

@login_required
def dashboard(request):
    # Tries to get account associated with user
    try:
        account = Account.objects.get(user=request.user)
    except Account.DoesNotExist:
        return redirect('logout')

    pending_requests = PaymentRequest.objects.filter(
        recipient=request.user,
        status='pending'
    )

    return render(request, 'dashboard.html', {
        'account': account,
        'pending_requests': pending_requests
    })

@login_required
def send_payment(request):
    # Get sender account to pass in currency
    sender_account = Account.objects.get(user=request.user)

    if request.method == 'POST':
        recipient_username = request.POST.get('recipient')
        amount = decimal.Decimal(request.POST.get('amount'))

        # Try to grab recipient user with username
        try:
            recipient = User.objects.get(username=recipient_username)
            recipient_account = Account.objects.get(user=recipient)
        except User.DoesNotExist:
            return render(request, 'send_payment.html', {
                'error': 'User not found',
                'currency': sender_account.currency
            })

        if recipient == request.user:
            return render(request, 'send_payment.html', {
                'error': 'You cannot pay yourself',
                'currency': sender_account.currency
            })

        if sender_account.balance < amount:
            return render(request, 'send_payment.html', {
                'error': 'Insufficient funds',
                'currency': sender_account.currency
            })

        # Call the REST service to convert if currencies differ
        if sender_account.currency != recipient_account.currency:
            response = requests.get(
                f'http://localhost:8000/api/conversion/'
                f'{sender_account.currency}/{recipient_account.currency}/{amount}/'
            )
            if response.status_code != 200:
                return render(request, 'send_payment.html', {
                    'error': 'Currency conversion failed',
                    'currency': sender_account.currency
                })

            converted_amount = decimal.Decimal(str(response.json()['converted_amount']))
        else:
            converted_amount = amount

        # Atomic transaction logic
        with transaction.atomic():
            sender_account.balance -= amount
            sender_account.save()
            recipient_account.balance += converted_amount
            recipient_account.save()
            Transaction.objects.create(
                sender=request.user,
                receiver=recipient,
                amount=amount,
                currency=sender_account.currency,
                converted_amount = converted_amount,
                converted_currency = recipient_account.currency
            )

        return redirect('dashboard')

    return render(request, 'send_payment.html', {'currency': sender_account.currency})

@login_required
def request_payment(request):
    # Get sender account to pass in currency
    sender_account = Account.objects.get(user=request.user)

    if request.method == 'POST':
        recipient_username = request.POST.get('recipient')
        amount = decimal.Decimal(request.POST.get('amount'))

        try:
            recipient = User.objects.get(username=recipient_username)
        except User.DoesNotExist:
            return render(request, 'request_payment.html', {
                'error': 'User not found',
                'currency': sender_account.currency
            })

        if recipient == request.user:
            return render(request, 'request_payment.html', {
                'error': 'You cannot request from yourself',
                'currency': sender_account.currency
            })

        recipient_account = Account.objects.get(user=recipient)

        # Call the REST service to convert if currencies differ
        if sender_account.currency != recipient_account.currency:
            response = requests.get(
                f'http://localhost:8000/api/conversion/'
                f'{sender_account.currency}/{recipient_account.currency}/{amount}/'
            )
            if response.status_code != 200:
                return render(request, 'request_payment.html', {
                    'error': 'Currency conversion failed',
                    'currency': sender_account.currency
                })
            converted_amount = decimal.Decimal(str(response.json()['converted_amount']))
        else:
            converted_amount = amount

        # Creates payment request object
        PaymentRequest.objects.create(
            requester=request.user,
            recipient=recipient,
            amount=amount,
            currency=sender_account.currency,
            converted_amount=converted_amount,
            converted_currency=recipient_account.currency
        )

        return redirect('dashboard')

    return render(request, 'request_payment.html', {'currency': sender_account.currency})

@login_required
def handle_payment_request(request, pk):
    payment_request = get_object_or_404(PaymentRequest, pk=pk, recipient=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'accept':
            payer_account = Account.objects.get(user=request.user)
            requester_account = Account.objects.get(user=payment_request.requester)

            if payer_account.balance < payment_request.converted_amount:
                return render(request, 'handle_request.html', {
                    'payment_request': payment_request,
                    'error': 'Insufficient funds'
                })

            # Atomic transaction logic
            with transaction.atomic():
                payer_account.balance -= payment_request.converted_amount
                payer_account.save()
                requester_account.balance += payment_request.amount
                requester_account.save()
                payment_request.status = 'accepted'
                payment_request.save()
                Transaction.objects.create(
                    sender=request.user,
                    receiver=payment_request.requester,
                    amount=payment_request.converted_amount,
                    currency=payment_request.converted_currency,
                    converted_amount=payment_request.amount,
                    converted_currency=payment_request.currency
                )

        elif action == 'reject':
            payment_request.status = 'rejected'
            payment_request.save()

        return redirect('dashboard')

    return render(request, 'handle_request.html', {'payment_request': payment_request})

@login_required
def transaction_history(request):
    # Use query to get transactions received or sent by user
    transactions = Transaction.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp')

    return render(request, 'transaction_history.html', {'transactions': transactions})

@staff_member_required
def admin_dashboard(request):
    # Gets all accounts and users
    accounts = Account.objects.all().select_related('user')
    transactions = Transaction.objects.all().order_by('-timestamp').select_related('sender', 'receiver')

    return render(request, 'admin_dashboard.html', {
        'accounts': accounts,
        'transactions': transactions
    })

@staff_member_required
def register_admin(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                is_staff=True,
            )
            Account.objects.create(user=user, balance=0, currency=form.cleaned_data['currency'])
            return redirect('admin_dashboard')
    else:
        form = RegisterForm()

    return render(request, 'register_admin.html', {'form': form})