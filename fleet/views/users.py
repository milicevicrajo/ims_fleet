from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from core.models import CustomUser


class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = "fleet/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        return CustomUser.objects.all()
