from django.views.generic import TemplateView
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .forms import SchoolSearchForm
from schools.models import SchoolUser
from accounts.models import CustomUser

class HomePageView(TemplateView):
    template_name = 'base/index.html'

class AdminDashboardView(TemplateView):
    template_name = 'base/admin_dashboard.html'

class UserDashboardView(TemplateView):
    template_name = 'base/user_dashboard.html'

def SchoolSearchView(request):
    form = SchoolSearchForm()
    form.encoding = 'utf-8'
    q = ''
    school_results = SchoolUser.objects.all()
    school_results_length = len(school_results)

    if 'q' in request.GET:
        form = SchoolSearchForm(request.GET)
        form.encoding = 'utf-8'
        if form.is_valid():
            q = form.cleaned_data['q']
            school_results = SchoolUser.objects.filter(school__name__icontains=q).order_by('department__name', 'school__name')
            school_results_length = len(school_results)

            return render(request, 'base/school_symbol_search.html',
                        {'form': form,
                        'q': q,
                        'school_results': school_results,
                        'school_results_length': school_results_length,}) 

    else:
        return render(request, 'base/school_symbol_search.html',
                    {'form': form,
                    'q': q,
                    'school_results': school_results,}) 

def SchoolSearchAutoCompleteView(request):
    if 'term' in request.GET:
        qs_schools = SchoolUser.objects.filter(school__name__icontains=request.GET.get('term'))
        print(f"qs_schools {qs_schools}")
        # schools = list()
        schools = [item.school.name for item in qs_schools]
        print(schools)
        return JsonResponse(schools, safe=False)
    return render(request, 'base/school_symbol_search.html')

def AccountEditView(request):
    user = get_object_or_404(CustomUser, pk=request.user.id)
    return render(request, 'base/account_edit.html', {'user': user})