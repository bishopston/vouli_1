from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import School, SchoolUser
from .forms import SchoolUserForm

@ login_required
def SchoolUserView(request):
    my_schools = SchoolUser.objects.filter(creator=request.user)

    return render(request, 'schools/schools.html', {'my_schools': my_schools})

@ login_required
def SchoolUserCreateView(request):
    my_schools = SchoolUser.objects.filter(creator=request.user)

    form = SchoolUserForm()
    if request.method == "POST":
        form = SchoolUserForm(request.POST)
        if form.is_valid():
            privacy_accepted_ = form.cleaned_data["privacy_accepted"]
            school_user = SchoolUser(
                department = form.cleaned_data["department"],
                school = form.cleaned_data["school"],
                director_name = form.cleaned_data["director_name"],
                director_surname = form.cleaned_data["director_surname"],
                address = form.cleaned_data["address"],
                address_number = form.cleaned_data["address_number"],
                city = form.cleaned_data["city"],
                zipcode = form.cleaned_data["zipcode"],
                phone = form.cleaned_data["phone"],
                email = form.cleaned_data["email"],
                privacy_accepted = form.cleaned_data["privacy_accepted"],
                creator = request.user
            )
            if len(my_schools) == 0 and privacy_accepted_ == True:
                school_user.save()
                #form.save()
                return HttpResponseRedirect(reverse('base:home'))
            if len(my_schools) > 0:
                form = SchoolUserForm()
                return render(request, 'schools/school_add.html', {'form': form, 'error_message': "Έχετε ήδη προβεί σε εγγραφή σχολείου"})
            if privacy_accepted_ == False:
                form = SchoolUserForm()
                return render(request, 'schools/school_add.html', {'form': form, 'error_message': "Πρέπει να συναινέσετε στην πολιτική συλλογής και επεξεργασίας προσωπικών δεδομένων"})                

        # else:
        #     form = SchoolUserForm()

    context = {'form': form}

    return render(request, 'schools/school_add.html', context)

def load_schools(request):
    department_id = request.GET.get('department')
    schools = School.objects.filter(department_id=department_id).order_by('name')
    return render(request, 'schools/school_dropdown_list_options.html', {'schools': schools})