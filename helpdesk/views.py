from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Chamado, Categoria, Prioridade, Equipe, SLA
from .forms import ChamadoForm, ResolverChamadoForm

from django.db.models import Q

def index(request):
    chamados_qs = Chamado.objects.select_related("categoria", "prioridade", "categoria__equipe").all()

    # Métricas globais da fila
    total_chamados = chamados_qs.count()
    abertos = chamados_qs.filter(status__in=["aberto", "em_atendimento"]).count()
    resolvidos = chamados_qs.filter(status="resolvido").count()
    fora_prazo = sum(1 for c in chamados_qs if not c.dentro_do_prazo and c.status in ["aberto", "em_atendimento"])

    # Parâmetros de Busca e Filtro (Feature 1)
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    prioridade_id = request.GET.get("prioridade", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()

    # Desafio Extra: Filtros combinados na mesma consulta utilizando Q()
    filtros = Q()
    if q:
        filtros &= (
            Q(titulo__icontains=q) |
            Q(descricao__icontains=q) |
            Q(protocolo__icontains=q) |
            Q(solicitante_nome__icontains=q)
        )

    if status:
        filtros &= Q(status=status)

    if prioridade_id:
        filtros &= Q(prioridade_id=prioridade_id)

    if categoria_id:
        filtros &= Q(categoria_id=categoria_id)

    chamados = chamados_qs.filter(filtros)
    total_filtrados = chamados.count()

    categorias = Categoria.objects.filter(ativa=True).select_related("equipe").order_by("nome")
    prioridades = Prioridade.objects.all().order_by("peso")

    context = {
        "chamados": chamados,
        "total_chamados": total_chamados,
        "abertos": abertos,
        "resolvidos": resolvidos,
        "fora_prazo": fora_prazo,
        "total_filtrados": total_filtrados,
        "categorias": categorias,
        "prioridades": prioridades,
        "filtros_ativos": bool(q or status or prioridade_id or categoria_id),
    }
    return render(request, "helpdesk/index.html", context)


def novo_chamado(request):
    if request.method == "POST":
        form = ChamadoForm(request.POST)
        if form.is_valid():
            chamado = form.save()
            messages.success(request, f"Chamado {chamado.protocolo} aberto com sucesso! Prazo de SLA calculado: {chamado.prazo_sla.strftime("%d/%m/%Y %H:%M")}")
            return redirect("detalhes_chamado", chamado_id=chamado.id)
    else:
        form = ChamadoForm()
    return render(request, "helpdesk/novo_chamado.html", {"form": form})

def detalhes_chamado(request, chamado_id):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    form_resolver = ResolverChamadoForm(instance=chamado)

    if request.method == "POST":
        form_resolver = ResolverChamadoForm(request.POST, instance=chamado)
        if form_resolver.is_valid():
            c = form_resolver.save(commit=False)
            if c.status in ["resolvido", "fechado"] and not c.data_resolucao:
                c.data_resolucao = timezone.now()
            c.save()
            messages.success(request, f"Chamado {c.protocolo} atualizado com sucesso!")
            return redirect("detalhes_chamado", chamado_id=c.id)

    context = {
        "chamado": chamado,
        "form_resolver": form_resolver,
    }
    return render(request, "helpdesk/detalhes_chamado.html", context)

def slas_info(request):
    slas = SLA.objects.select_related("prioridade").all()
    equipes = Equipe.objects.prefetch_related("categorias").all()
    return render(request, "helpdesk/slas_info.html", {"slas": slas, "equipes": equipes})
