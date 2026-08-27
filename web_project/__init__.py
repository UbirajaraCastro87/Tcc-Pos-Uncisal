# from web_project.bootstrap import TemplateBootstrap
from web_project.template_helpers.theme import TemplateHelper


class TemplateLayout:
    # Initialize the bootstrap files and page layout
    def init(self, context):
        # Init the Template Context using TEMPLATE_CONFIG

        # Set a default layout globally using settings.py. Can be set in the page level view file as well.
        layout = "vertical"

        # Set the selected layout
        context.update(
            {
                "layout_path": TemplateHelper.set_layout(
                    "layout_" + layout + ".html", context
                ),
            }
        )

        # Map context variables
        TemplateHelper.map_context(context)

        # --- ADICIONE ESTE BLOCO DE SEGURANÇA E DADOS DO USUÁRIO ---
        request = context.get('request')
        if request and request.user.is_authenticated:
            context.update({
                'usuario_nome': request.user.get_full_name() or request.user.username,
                'usuario_email': request.user.email,
                'usuario_cargo': "Administrador" if request.user.is_superuser else "Usuário",
            })
        # -----------------------------------------------------------

        return context
