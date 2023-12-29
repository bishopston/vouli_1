from django.views.generic import TemplateView


class HomePageView(TemplateView):
    template_name = 'base/index.html'

class AdminDashboardView(TemplateView):
    template_name = 'base/admin_dashboard.html'