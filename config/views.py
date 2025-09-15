from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

def home(request):
    # if request.user.is_authenticated:
    #     return redirect('accounts:dashboard')  
    return redirect('https://nawabganjcitycollege.edu.bd/')