
# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class UserAccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    username = models.CharField(max_length=150)
    login_time = models.DateTimeField(auto_now_add=True)  # Data e Hora do login
    logout_time = models.DateTimeField(null=True, blank=True)  # Data e Hora do logout
    duration = models.DurationField(null=True, blank=True)  # Tempo ativo no sistema
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # IP do usuário
    user_agent = models.TextField(null=True, blank=True)  # Navegador / Dispositivo

    def __str__(self):
        return f"{self.username} - {self.login_time.strftime('%d/%m/%Y %H:%M')}"
