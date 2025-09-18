from django import forms
from .models import Lead, LeadNote

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'name',
            'horario',
            'telefone',
            'celular',
            'operadora',
            'whatsapp',
            'vendedor',
            'forma_conhecimento',
            'pacote_interessado',
            'valor_divulgado',
            'email',
        ]
        labels = {
            'name': 'Nome',
            'horario': 'Horário',
            'telefone': 'Telefone',
            'celular': 'Celular',
            'operadora': 'Operadora',
            'whatsapp': 'WhatsApp',
            'vendedor': 'Vendedor',
            'forma_conhecimento': 'Forma de Conhecimento',
            'pacote_interessado': 'Pacote Interessado',
            'valor_divulgado': 'Valor Divulgado',
            'email': 'E-mail',
        }
        widgets = {
            'horario': forms.TimeInput(attrs={'type': 'time'}),
            'valor_divulgado': forms.NumberInput(attrs={'step': '0.01'}),
            'whatsapp': forms.CheckboxInput(),
        }

class LeadNoteForm(forms.ModelForm):
    class Meta:
        model = LeadNote
        fields = ['note']
        labels = {
            'note': 'Adicionar Nota',
        }
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escreva uma nota sobre este lead'}),
        }
