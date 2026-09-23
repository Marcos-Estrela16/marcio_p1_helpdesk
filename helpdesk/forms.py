from django import forms
from .models import Chamado, Categoria, Prioridade

class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["titulo", "categoria", "prioridade", "solicitante_nome", "solicitante_email", "descricao"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Erro no acesso ao banco de dados"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "prioridade": forms.Select(attrs={"class": "form-select"}),
            "solicitante_nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Seu nome completo"}),
            "solicitante_email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "email@empresa.com"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Descreva os sintomas do problema detalhadamente..."}),
        }

class ResolverChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["status", "solucao"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "solucao": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Descreva a ação técnica corretiva aplicada..."}),
        }
