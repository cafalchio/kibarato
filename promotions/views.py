from django.views.generic import TemplateView
from .models import Promotion


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["promotions"] = Promotion.objects.all()
        return context
