# 🎫 Help Desk & Gestão de SLA de Chamados

**Disciplina:** Laboratório de Programação Full Stack  
**Professor:** Márcio Garrido  
**Aluno:** Marcos Vinícius Silva Estrela  
**Matrícula:** 202413893  
**Avaliação:** P1 — MVP Funcional (Aula 12)  
**Tema Escolhido:** Opção 4 — Help Desk / Chamados  

---

## 📌 1. Visão Geral do Projeto (P1)

Este projeto implementa o MVP funcional completo de um sistema de **Help Desk e Suporte Técnico** com cálculo automático de prazos de Acordo de Nível de Serviço (SLA) categorizados por prioridade e equipe responsável.

### As 5 Entidades da Rubrica:
1. **`Equipe`**: Grupos técnicos responsáveis por resolver incidentes (Infraestrutura, Banco de Dados, etc.).
2. **`Categoria`**: Tipos de incidentes vinculados à equipe competente.
3. **`Prioridade`**: Níveis de urgência (`Crítica`, `Alta`, `Média`, `Baixa`).
4. **`SLA`**: Definição do tempo máximo em horas acordado para cada prioridade.
5. **`Chamado`**: Registro do ticket de suporte com protocolo único, solicitante, prazos calculados e parecer conclusivo.

### Regra de Negócio P1 Implementada:
- **Cálculo Automático de SLA:** Ao abrir o chamado, o sistema busca as horas estabelecidas no SLA da prioridade e projeta o `prazo_sla` exato.
- **Auditoria de Conformidade:** Exibição visual em tempo real indicando se o chamado está dentro do prazo contratual ou com SLA violado/estourado.

---

## 🚀 2. Como Executar

```bash
cd "Laboratório de Programação Full Stack/p1_prova/marcos"
source venv/bin/activate
python manage.py migrate
python manage.py runserver
```

Acesse: **`http://127.0.0.1:8000/`**  
Admin: **`http://127.0.0.1:8000/admin/`** (User: `admin` | Senha: `admin123`)

---

## 📋 3. Relatório das Features Obrigatórias da Avaliação P1

### 🔍 Feature 1 — Busca e Filtro na Listagem Principal

- **Campos e Filtros Escolhidos:**
  - **Busca Textual Aberta (`q`):** Pesquisa case-insensitive (`icontains`) combinada nos campos `titulo`, `descricao`, `protocolo` e `solicitante_nome`.
  - **Filtros Categóricos:** Seletores `<select>` para **Status** (`aberto`, `em_atendimento`, `resolvido`, `fechado`), **Prioridade** e **Categoria**.
  - **Desafio Extra Implementado:** Utilização do objeto `Q()` (`from django.db.models import Q`) para compor dinamicamente a cláusula SQL na mesma consulta, integrando filtros relacionais e a busca textual multifatorial.
- **Justificativa da Escolha:**
  Em uma central de suporte técnico ou NOC, o volume de chamados cresce rapidamente. A busca por palavras-chave técnicas (ex: "Postgres", "VPN", "queda") ou pelo nome do cliente e protocolo permite atendimento imediato quando o solicitante entra em contato. Combinar isso com o filtro de status permite que os operadores filtrem rapidamente apenas os chamados em aberto que demandam ação urgente.
- **O que aconteceria se não existisse:**
  Os analistas de suporte precisariam percorrer visualmente páginas inteiras de registros para localizar um incidente específico. A ausência de filtros por prioridade e status impediria a identificação ágil de chamados críticos pendentes, resultando no estouro generalizado de prazos de SLA e degradação da qualidade do suporte.

---

### 🛡️ Feature 2 — Validação Customizada no Formulário (ModelForm)

- **Regras de Negócio Implementadas no `clean()`:**
  1. **Validação do Prazo de SLA (Rubrica Oficial P1):** O prazo de SLA calculado não pode ser anterior ou igual à data de abertura do chamado (`prazo_sla > data_abertura`).
  2. **Qualidade de Triagem para Incidentes Críticos:** Chamados classificados com prioridade **Crítica** exigem obrigatoriamente um detalhamento técnico do problema com no mínimo 30 caracteres (`clean()`).
  3. **Validação de Assunto Vago:** O campo de assunto (`titulo`) deve possuir no mínimo 5 caracteres e não aceita termos genéricos como "teste", "ajuda", "problema" ou "socorro" (`clean_titulo()`).
  4. **Encerramento Técnico com Parecer:** No `ResolverChamadoForm`, a finalização do chamado para "resolvido" ou "fechado" exige o preenchimento de uma solução técnica conclusiva com pelo menos 10 caracteres.
- **Justificativa da Escolha:**
  O cálculo automático e a auditoria do SLA são o core business do sistema. Se o prazo projetado fosse igual ou inferior ao instante de criação (como em caso de horas de SLA zeradas ou inconsistência temporal), o chamado já nasceria com status de SLA violado e sem conformidade. Além disso, incidentes críticos disparam escala de plantão; impedir descrições superficiais (ex: "caiu") força o solicitante a fornecer contexto mínimo para diagnóstico imediato.
- **O que aconteceria se não existisse:**
  O banco de dados seria corrompido com registros de tickets com prazos de SLA matematicamente absurdos (datas passadas ou nulas), distorcendo os indicadores de conformidade e auditoria. Ademais, analistas perderiam horas preciosas tentando descobrir o que aconteceu em chamados críticos sem qualquer detalhamento técnico.

