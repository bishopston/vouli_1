from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


@login_required
def custom_login_redirect(request):
    if request.user.is_superuser:
        return redirect('base:admin_dashboard')
    else:
        return redirect('base:user_dashboard')
