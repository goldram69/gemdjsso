# users/views.py
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm # Import your custom form

class SignUpView(CreateView):
    form_class = CustomUserCreationForm # Use your custom form
    success_url = reverse_lazy('login') # Redirect to a login page after successful signup
    template_name = 'registration/signup.html' # Path to your template
