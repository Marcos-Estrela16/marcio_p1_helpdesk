from datetime import timedelta
from django import forms
from django.utils import timezone
from .models import Chamado, Categoria, Prioridade

class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["titulo", "categoria", "prioridade", "solicitante_nome", "solicitante_email", "descricao"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Falha de autenticação no servidor de banco de dados"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "prioridade": forms.Select(attrs={"class": "form-select"}),
            "solicitante_nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Seu nome completo"}),
            "solicitante_email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "email@empresa.com"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Descreva os sintomas do problema detalhadamente..."}),
        }

    def clean_titulo(self):
        """Validação customizada do campo 'titulo' (mínimo 5 caracteres e sem termos vagos)."""
        titulo = self.cleaned_data.get("titulo", "").strip()
        if len(titulo) < 5:
            raise forms.ValidationError("O assunto do chamado deve ter pelo menos 5 caracteres com um resumo objetivo do incidente.")
        termos_invalidos = ["teste", "ajuda", "socorro", "problema", "erro", "chamado"]
        if titulo.lower() in termos_invalidos:
            raise forms.ValidationError(f"O termo '{titulo}' é muito vago. Especifique brevemente qual serviço ou equipamento foi afetado.")
        return titulo

    def clean(self):
        """
        Validação customizada de domínio (Feature 2):
        1. Regra Oficial da Rubrica P1: O prazo de SLA não pode ser anterior ou igual à data de abertura do chamado.
        2. Regra de Negócio de Help Desk: Chamados com prioridade 'Crítica' exigem detalhamento mínimo de 30 caracteres.
        3. Validação de integridade: Categoria selecionada deve estar ativa.
        """
        cleaned_data = super().clean()
        prioridade = cleaned_data.get("prioridade")
        descricao = cleaned_data.get("descricao", "").strip()
        categoria = cleaned_data.get("categoria")

        # 1. Regra Oficial da Avaliação P1: O prazo do SLA não pode ser anterior à data de abertura
        if prioridade:
            horas_sla = 24
            if hasattr(prioridade, "sla"):
                horas_sla = prioridade.sla.horas_resolucao

            data_base = self.instance.data_abertura if (self.instance and self.instance.data_abertura) else timezone.now()
            prazo_projetado = data_base + timedelta(hours=horas_sla)

            if prazo_projetado <= data_base or horas_sla <= 0:
                raise forms.ValidationError(
                    "Violação de Regra de Negócio de SLA: O prazo do SLA calculado não pode ser anterior ou igual à data de abertura do chamado."
                )

        # 2. Regra de Domínio: Chamado de urgência Crítica exige detalhamento técnico mínimo (30 caracteres)
        if prioridade and prioridade.nivel == "critica" and len(descricao) < 30:
            self.add_error(
                "descricao",
                "Chamados de prioridade 'Crítica' acionam plantão de emergência e exigem descrição detalhada de no mínimo 30 caracteres."
            )

        # 3. Categoria inativa não pode receber novos chamados
        if categoria and not categoria.ativa:
            self.add_error("categoria", "A categoria selecionada está inativa para abertura de novos chamados.")

        return cleaned_data


class ResolverChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["status", "solucao"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "solucao": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Descreva a ação técnica corretiva aplicada..."}),
        }

    def clean(self):
        """Garante que chamados resolvidos/fechados tenham um parecer técnico conclusivo mínimo."""
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        solucao = cleaned_data.get("solucao", "").strip()

        if status in ["resolvido", "fechado"]:
            if not solucao or len(solucao) < 10:
                self.add_error(
                    "solucao",
                    "Para encerrar ou resolver o chamado, é obrigatório registrar um parecer técnico detalhado da solução (mínimo de 10 caracteres)."
                )
        return cleaned_data

