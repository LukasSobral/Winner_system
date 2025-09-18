from django.db import models
from django.conf import settings

class Lead(models.Model):
    name = models.CharField(max_length=100)
    data_cadastro = models.DateField(auto_now_add=True)
    horario = models.CharField(max_length=20, blank=True, null=True)  # Ex: "14:00"
    telefone = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    operadora = models.CharField(max_length=50, blank=True, null=True)
    whatsapp = models.BooleanField(default=False)

    atendente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads_atendidos'
    )
    vendedor = models.CharField(max_length=100, blank=True, null=True)
    forma_conhecimento = models.CharField(max_length=100, blank=True, null=True)
    pacote_interessado = models.CharField(max_length=100, blank=True, null=True)
    valor_divulgado = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.codigo} - {self.name}"

    @property
    def codigo(self):
        return f"LEAD{self.id:04d}" if self.id else "LEAD0000"


class LeadNote(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='notes')
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Nota de {self.user} em {self.created_at.strftime('%d/%m/%Y %H:%M')}"
