from django.test import TestCase, Client
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
from .models import Equipe, Prioridade, SLA, Categoria, Chamado

class HelpDeskP1Testes(TestCase):
    def setUp(self):
        self.client = Client()
        self.equipe = Equipe.objects.create(nome="NOC Redes", email_contato="noc@empresa.com", ativa=True)
        self.prioridade = Prioridade.objects.create(nivel="alta", nome="Alta Severidade", peso=2, cor_badge="warning")
        self.sla = SLA.objects.create(prioridade=self.prioridade, horas_resolucao=12, descricao="SLA de 12 horas")
        self.categoria = Categoria.objects.create(nome="Falha de Roteamento", equipe=self.equipe, ativa=True)

    def test_todas_as_entidades_existem(self):
        self.assertEqual(Equipe.objects.count(), 1)
        self.assertEqual(Prioridade.objects.count(), 1)
        self.assertEqual(SLA.objects.count(), 1)
        self.assertEqual(Categoria.objects.count(), 1)

    def test_rotas_principais_http_200(self):
        self.assertEqual(self.client.get(reverse("index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("slas_info")).status_code, 200)
        self.assertEqual(self.client.get(reverse("novo_chamado")).status_code, 200)

    def test_calculo_automatico_sla_e_resolucao(self):
        # 1. Abertura do Chamado via POST
        res = self.client.post(reverse("novo_chamado"), {
            "titulo": "Link de Internet Caiu",
            "categoria": self.categoria.id,
            "prioridade": self.prioridade.id,
            "solicitante_nome": "Marcos Estrela",
            "solicitante_email": "marcos@empresa.com",
            "descricao": "Roteador principal sem sincronismo óptico.",
        })
        self.assertEqual(res.status_code, 302)

        chamado = Chamado.objects.get(titulo="Link de Internet Caiu")
        self.assertIsNotNone(chamado.protocolo)
        self.assertIsNotNone(chamado.prazo_sla)

        # Validação: o prazo de SLA deve ser aproximadamente data_abertura + 12 horas
        diferenca_horas = (chamado.prazo_sla - chamado.data_abertura).total_seconds() / 3600
        self.assertAlmostEqual(diferenca_horas, 12, delta=0.1)
        self.assertTrue(chamado.dentro_do_prazo)

        # 2. Resolução do Chamado
        res_resolver = self.client.post(reverse("detalhes_chamado", args=[chamado.id]), {
            "status": "resolvido",
            "solucao": "Reinicializada a porta do switch e reconfigurado BGP.",
        })
        self.assertEqual(res_resolver.status_code, 302)

        chamado.refresh_from_db()
        self.assertEqual(chamado.status, "resolvido")
        self.assertIsNotNone(chamado.data_resolucao)
        self.assertTrue(chamado.dentro_do_prazo)
