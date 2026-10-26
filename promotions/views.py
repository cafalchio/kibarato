from django.views.generic import TemplateView
from django.db.models import Q
from .models import Promotion, promotion_today


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["promotions"] = Promotion.objects.filter(
            Q(ends_on__isnull=True) | Q(ends_on__gte=promotion_today())
        )
        return context
