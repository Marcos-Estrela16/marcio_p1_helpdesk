from django.db import models
from django.utils import timezone
from datetime import timedelta

class Equipe(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome da Equipe de Suporte")
    descricao = models.TextField(blank=True, verbose_name="Atribuições da Equipe")
    email_contato = models.EmailField(verbose_name="E-mail da Equipe")
    ativa = models.BooleanField(default=True, verbose_name="Equipe Ativa")

    class Meta:
        verbose_name = "Equipe"
        verbose_name_plural = "Equipes"

    def __str__(self):
        return self.nome

class Prioridade(models.Model):
    NIVEL_CHOICES = [
        ("baixa", "Baixa"),
        ("media", "Média"),
        ("alta", "Alta"),
        ("critica", "Crítica"),
    ]

    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, unique=True, verbose_name="Nível")
    nome = models.CharField(max_length=50, verbose_name="Descrição da Prioridade")
    peso = models.PositiveIntegerField(default=1, verbose_name="Peso de Ordenação")
    cor_badge = models.CharField(max_length=20, default="info", verbose_name="Classe de Cor")

    class Meta:
        verbose_name = "Prioridade"
        verbose_name_plural = "Prioridades"
        ordering = ["peso"]

    def __str__(self):
        return f"{self.nome} ({self.get_nivel_display()})"

class SLA(models.Model):
    prioridade = models.OneToOneField(Prioridade, on_delete=models.CASCADE, related_name="sla", verbose_name="Prioridade Associada")
    horas_resolucao = models.PositiveIntegerField(verbose_name="Tempo Máximo de SLA (Horas)")
    descricao = models.CharField(max_length=150, blank=True, verbose_name="Termo do Acordo")

    class Meta:
        verbose_name = "Acordo de SLA"
        verbose_name_plural = "Acordos de SLA"

    def __str__(self):
        return f"SLA: {self.horas_resolucao}h para {self.prioridade.nome}"

class Categoria(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome da Categoria")
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name="categorias", verbose_name="Equipe Responsável")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    ativa = models.BooleanField(default=True, verbose_name="Categoria Ativa")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return f"{self.nome} ({self.equipe.nome})"

class Chamado(models.Model):
    STATUS_CHOICES = [
        ("aberto", "Aberto"),
        ("em_atendimento", "Em Atendimento"),
        ("resolvido", "Resolvido"),
        ("fechado", "Fechado"),
    ]

    protocolo = models.CharField(max_length=30, unique=True, verbose_name="Protocolo")
    titulo = models.CharField(max_length=200, verbose_name="Assunto do Chamado")
    descricao = models.TextField(verbose_name="Detalhamento do Problema")
    solicitante_nome = models.CharField(max_length=120, verbose_name="Nome do Solicitante")
    solicitante_email = models.EmailField(verbose_name="E-mail do Solicitante")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="chamados", verbose_name="Categoria")
    prioridade = models.ForeignKey(Prioridade, on_delete=models.PROTECT, related_name="chamados", verbose_name="Prioridade")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="aberto", verbose_name="Status")
    data_abertura = models.DateTimeField(auto_now_add=True, verbose_name="Data de Abertura")
    prazo_sla = models.DateTimeField(null=True, blank=True, verbose_name="Prazo Limite do SLA")
    data_resolucao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Resolução")
    solucao = models.TextField(blank=True, verbose_name="Parecer Técnico / Solução")

    class Meta:
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"
        ordering = ["-data_abertura"]

    def __str__(self):
        return f"[{self.protocolo}] {self.titulo} ({self.get_status_display()})"

    def calcular_prazo_sla(self):
        horas = 24
        if hasattr(self.prioridade, "sla"):
            horas = self.prioridade.sla.horas_resolucao
        abertura = self.data_abertura or timezone.now()
        return abertura + timedelta(hours=horas)

    def save(self, *args, **kwargs):
        if not self.protocolo:
            ano = timezone.now().year
            ultimo = Chamado.objects.filter(protocolo__startswith=f"HD-{ano}").count()
            self.protocolo = f"HD-{ano}-{ultimo+1001}"

        if not self.prazo_sla and self.prioridade_id:
            horas = 24
            try:
                horas = self.prioridade.sla.horas_resolucao
            except Exception:
                pass
            base_time = self.data_abertura if self.data_abertura else timezone.now()
            self.prazo_sla = base_time + timedelta(hours=horas)

        super().save(*args, **kwargs)

    @property
    def dentro_do_prazo(self):
        if self.status in ["resolvido", "fechado"] and self.data_resolucao:
            return self.data_resolucao <= self.prazo_sla
        return timezone.now() <= self.prazo_sla
