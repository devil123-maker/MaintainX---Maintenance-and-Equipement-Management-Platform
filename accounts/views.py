from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model, authenticate, login as auth_login, logout as auth_logout

User = get_user_model()
# Create your views here.
def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        
        full_name = request.POST.get("full_name")
        mobile_number = request.POST.get("mobile_number")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        user_type = request.POST.get("user_type")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/signup.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "accounts/signup.html")
        
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name,
            mobile_number=mobile_number,
            user_type=user_type
        )

        messages.success(request, "Account created successfully.")
        return redirect("login")

    return render(request, "accounts/signup.html")

def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")
        remember = request.POST.get("remember")

        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            auth_login(request, user)
            response = redirect('dashboard')
            if remember:
                # Keep user logged in for 2 weeks (14 days)
                request.session.set_expiry(1209600)
                # Store email in cookie for 30 days to autofill login field
                response.set_cookie('remembered_email', email, max_age=2592000, httponly=True, samesite='Lax')
            else:
                # Session expires when the browser is closed & clear cookie
                request.session.set_expiry(0)
                response.delete_cookie('remembered_email')
            return response

        messages.error(request, "Invalid email or password.")
        remembered_email = request.COOKIES.get('remembered_email', '')
        return render(request, "accounts/login.html", {
            'remembered_email': remembered_email,
            'remember_checked': bool(remembered_email),
        })

    remembered_email = request.COOKIES.get('remembered_email', '')
    return render(request, "accounts/login.html", {
        'remembered_email': remembered_email,
        'remember_checked': bool(remembered_email),
    })


def logout_view(request):
    # Consume any pending messages to avoid stale alerts
    storage = get_messages(request)
    for _ in storage:
        pass
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


    