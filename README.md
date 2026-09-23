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
