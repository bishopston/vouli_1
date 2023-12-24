def current_user(request):
    return {'current_user': request.user}