from django.shortcuts import render, redirect
from .models import User
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages



# Create your views here.

def signup_view(request):
   
    if request.method == "POST":
        name = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = request.POST.get('role') or "admin"
        
        # Check password match
        if password != confirm_password:
            context = {"error":"Password doesn't match"}
            return render(request,"signup.html",context)

        # Check if username already exists
        if User.objects.filter(username=name).exists():
            return render(request, 'signup.html', {"error": "User already exists"})

        # Check if user use existing email id 
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {"error": "Email ID already exists"})
        
        # Create user only if all checks pass 
        user = User.objects.create_user(
            username = name,
            email = email,
            password = password,
            role = role
        )
            
        user.save()


        messages.success(request, "Account Created! Please Login")
        return redirect("home") # It checks
    return render(request,"signup.html")


def home(request):
    return render(request,"home.html")

def admin_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('signup')
    if request.user.role != 'admin':
        return redirect('signup')
    return render(request,"admin_dashboard.html")