from django.db import models
from django.contrib.auth.models import User

# Account model
class Account(models.Model):
  CURRENCY_CHOICES = [
    ('GBP', 'British Pound'),
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
  ]

  # One-to-One relationship between Accounts and Users
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  balance = models.DecimalField(max_digits=10, decimal_places=2)
  currency = models.CharField(choices=CURRENCY_CHOICES, max_length=3)

# Transaction model
class Transaction(models.Model):
  sender = models.ForeignKey(User, related_name='sent_transactions', on_delete=models.CASCADE)
  receiver = models.ForeignKey(User, related_name='received_transactions', on_delete=models.CASCADE)
  amount = models.DecimalField(max_digits=10, decimal_places=2)
  currency = models.CharField(max_length=3)
  converted_amount = models.DecimalField(max_digits=10, decimal_places=2)
  converted_currency = models.CharField(max_length=3)
  timestamp = models.DateTimeField(auto_now_add=True)

# Payment request model
class PaymentRequest(models.Model):
  STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('accepted', 'Accepted'),
    ('rejected', 'Rejected'),
  ]

  requester = models.ForeignKey(User, related_name='payment_requests_sent', on_delete=models.CASCADE)
  recipient = models.ForeignKey(User, related_name='payment_requests_received', on_delete=models.CASCADE)
  amount = models.DecimalField(max_digits=10, decimal_places=2)
  currency = models.CharField(max_length=3)
  converted_amount = models.DecimalField(max_digits=10, decimal_places=2)
  converted_currency = models.CharField(max_length=3)
  status = models.CharField(choices=STATUS_CHOICES, max_length=10, default='pending')
  timestamp = models.DateTimeField(auto_now_add=True)