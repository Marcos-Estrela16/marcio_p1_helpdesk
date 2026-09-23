from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Chamado, Categoria, Prioridade, Equipe, SLA
from .forms import ChamadoForm, ResolverChamadoForm

def index(request):
    chamados = Chamado.objects.select_related("categoria", "prioridade", "categoria__equipe").all()
    total_chamados = chamados.count()
    abertos = chamados.filter(status__in=["aberto", "em_atendimento"]).count()
    resolvidos = chamados.filter(status="resolvido").count()
    fora_prazo = sum(1 for c in chamados if not c.dentro_do_prazo and c.status in ["aberto", "em_atendimento"])

    context = {
        "chamados": chamados,
        "total_chamados": total_chamados,
        "abertos": abertos,
        "resolvidos": resolvidos,
        "fora_prazo": fora_prazo,
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
