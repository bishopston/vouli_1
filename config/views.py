from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser

@login_required
def custom_login_redirect(request):
    if request.user.is_superuser:
        return redirect('base:admin_dashboard')
    else:
        return redirect('base:user_dashboard')

# @login_required
# def delete_account(request):
#     if request.method == 'POST':
#         #myuser = CustomUser.get(user=request.user)
#         myuser = CustomUser.objects.get(email=request.user.email)
#         myuser.delete()
#         return redirect('account_logout')  # Redirect to the logout view (or another appropriate view)

#     return render(request, 'base/delete_account.html')