from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def connexion(request):
    if request.user.is_authenticated:
        return redirect("dossiers:liste")
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("dossiers:liste")
    else:
        form = AuthenticationForm()
    return render(request, "comptes/connexion.html", {"form": form})


@login_required
def deconnexion(request):
    logout(request)
    return redirect("comptes:connexion")
