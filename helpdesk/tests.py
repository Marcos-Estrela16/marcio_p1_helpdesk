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

    def test_feature1_busca_e_filtros_combinados_com_q(self):
        """Testa busca por texto e múltiplos filtros combinados usando Q()."""
        # Criar dados para teste de busca e filtros
        p_critica = Prioridade.objects.create(nivel="critica", nome="Crítica Urgente", peso=1, cor_badge="danger")
        SLA.objects.create(prioridade=p_critica, horas_resolucao=4, descricao="SLA 4h")
        cat_bd = Categoria.objects.create(nome="Banco Postgres", equipe=self.equipe, ativa=True)

        c1 = Chamado.objects.create(
            titulo="Servidor de Produção Down",
            descricao="Nenhum usuário consegue acessar o sistema ERP.",
            solicitante_nome="Carlos Silva",
            solicitante_email="carlos@empresa.com",
            categoria=self.categoria,
            prioridade=self.prioridade,
            status="aberto"
        )
        c2 = Chamado.objects.create(
            titulo="Lentidão na Consulta SQL",
            descricao="Queries no Postgres estão levando mais de 10 segundos.",
            solicitante_nome="Ana Lima",
            solicitante_email="ana@empresa.com",
            categoria=cat_bd,
            prioridade=p_critica,
            status="resolvido"
        )

        # 1. Busca por texto (q) no título (não case-sensitive com icontains)
        res_busca = self.client.get(reverse("index") + "?q=produção")
        self.assertContains(res_busca, "Servidor de Produção Down")
        self.assertNotContains(res_busca, "Lentidão na Consulta SQL")
        self.assertContains(res_busca, 'value="produção"')

        # 2. Busca por texto (q) na descrição
        res_busca_desc = self.client.get(reverse("index") + "?q=Postgres")
        self.assertContains(res_busca_desc, "Lentidão na Consulta SQL")
        self.assertNotContains(res_busca_desc, "Servidor de Produção Down")

        # 3. Filtro por status
        res_status = self.client.get(reverse("index") + "?status=resolvido")
        self.assertContains(res_status, "Lentidão na Consulta SQL")
        self.assertNotContains(res_status, "Servidor de Produção Down")

        # 4. Desafio Extra: Busca por texto E filtro por categoria combinados com Q()
        res_combinado = self.client.get(reverse("index") + f"?q=Lentidão&categoria={cat_bd.id}&status=resolvido")
        self.assertContains(res_combinado, "Lentidão na Consulta SQL")
        self.assertNotContains(res_combinado, "Servidor de Produção Down")

        # 5. Resultado vazio exibe mensagem clara ({% empty %})
        res_vazio = self.client.get(reverse("index") + "?q=TextoInexistenteXYZ")
        self.assertContains(res_vazio, "Nenhum chamado encontrado")
        self.assertContains(res_vazio, "TextoInexistenteXYZ")

    def test_feature2_validacao_customizada_sla_e_prioridade_critica(self):
        """Testa regras de negócio customizadas no ChamadoForm (Feature 2)."""
        from .forms import ChamadoForm, ResolverChamadoForm

        # 1. Validação de título muito curto
        form_curto = ChamadoForm(data={
            "titulo": "Bug",
            "categoria": self.categoria.id,
            "prioridade": self.prioridade.id,
            "solicitante_nome": "Marcos",
            "solicitante_email": "marcos@empresa.com",
            "descricao": "Descrição válida do problema no servidor."
        })
        self.assertFalse(form_curto.is_valid())
        self.assertIn("titulo", form_curto.errors)
        self.assertIn("pelo menos 5 caracteres", form_curto.errors["titulo"][0])

        # 2. Validação de título vago (termo genérico)
        form_vago = ChamadoForm(data={
            "titulo": "teste",
            "categoria": self.categoria.id,
            "prioridade": self.prioridade.id,
            "solicitante_nome": "Marcos",
            "solicitante_email": "marcos@empresa.com",
            "descricao": "Descrição válida do problema no servidor."
        })
        self.assertFalse(form_vago.is_valid())
        self.assertIn("titulo", form_vago.errors)
        self.assertIn("muito vago", form_vago.errors["titulo"][0])

        # 3. Validação de Chamado com prioridade Crítica sem detalhamento suficiente (< 30 chars)
        p_critica = Prioridade.objects.create(nivel="critica", nome="Crítica", peso=1)
        SLA.objects.create(prioridade=p_critica, horas_resolucao=2, descricao="SLA 2h")
        form_critica_curta = ChamadoForm(data={
            "titulo": "Parada do Gateway",
            "categoria": self.categoria.id,
            "prioridade": p_critica.id,
            "solicitante_nome": "Marcos",
            "solicitante_email": "marcos@empresa.com",
            "descricao": "Caiu tudo." # Menos de 30 caracteres
        })
        self.assertFalse(form_critica_curta.is_valid())
        self.assertIn("descricao", form_critica_curta.errors)
        self.assertIn("30 caracteres", form_critica_curta.errors["descricao"][0])

        # 4. Validação da rubrica do professor: Prazo do SLA não pode ser anterior/igual à abertura
        p_invalida = Prioridade.objects.create(nivel="baixa", nome="Sem SLA", peso=4)
        SLA.objects.create(prioridade=p_invalida, horas_resolucao=0, descricao="SLA zero")
        form_sla_invalido = ChamadoForm(data={
            "titulo": "Dúvida de Procedimento",
            "categoria": self.categoria.id,
            "prioridade": p_invalida.id,
            "solicitante_nome": "Marcos",
            "solicitante_email": "marcos@empresa.com",
            "descricao": "Dúvida geral sobre o sistema operacional."
        })
        self.assertFalse(form_sla_invalido.is_valid())
        self.assertTrue(any("não pode ser anterior ou igual à data de abertura" in err for err in form_sla_invalido.non_field_errors()))

        # 5. Validação no ResolverChamadoForm: fechar chamado sem solução técnica deve falhar
        chamado = Chamado.objects.create(
            titulo="Queda de VPN Corporativa",
            descricao="Usuários remotos sem comunicação com a matriz.",
            solicitante_nome="Roberto",
            solicitante_email="roberto@empresa.com",
            categoria=self.categoria,
            prioridade=self.prioridade,
            status="aberto"
        )
        form_resolver_invalido = ResolverChamadoForm(instance=chamado, data={
            "status": "resolvido",
            "solucao": "Ok" # Menos de 10 caracteres
        })
        self.assertFalse(form_resolver_invalido.is_valid())
        self.assertIn("solucao", form_resolver_invalido.errors)

