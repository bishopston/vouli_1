# in your views.py
#from allauth.account.views import LoginView
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# class CustomLoginView(LoginView):
#     def get_success_url(self):
#         if self.request.user.is_superuser:
#             return 'base:admin_dashboard'  # replace with your poweruser URL
#         else:
#             return 'base:user_dashboard'  # replace with your regular user URL

@login_required
def custom_login_redirect(request):
    if request.user.is_superuser:
        return redirect('base:admin_dashboard')  # Replace with the actual URL for power users
    else:
        return redirect('base:user_dashboard')  # Replace with the actual URL for simple users