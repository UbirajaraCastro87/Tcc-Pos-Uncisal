from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper

class DashboardsView(LoginRequiredMixin, TemplateView):
    """
    View protegida do Dashboard Analytics.
    O LoginRequiredMixin garante que apenas usuários autenticados
    e com sessão ativa acessem esta página. Caso contrário, são
    redirecionados para a tela de login.
    """
    login_url = '/auth/login/'
    redirect_field_name = 'next'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update(
            {
                "layout_path": TemplateHelper.set_layout(
                    "layout_vertical.html", context
                )
            }
        )
        return context
