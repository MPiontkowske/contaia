"""
Centralização de todos os prompts do ContaIA.

Cada tool tem:
  - label: nome legível para UI
  - category: grupo da ferramenta
  - model: modelo Anthropic a usar
  - max_tokens: limite de tokens por resposta
  - system: system prompt
  - build_user: função que constrói o user message a partir dos campos

Modelos:
  - claude-haiku-4-5-20251001 → tarefas simples (e-mails curtos)
  - claude-sonnet-4-6         → tarefas intermediárias (relatórios, reajuste)
  - claude-opus-4-6           → tarefas complexas (defesa fiscal, impugnação)
"""

MAX_CAMPO_LEN = 2000  # proteção contra prompt injection via campos longos


def _s(value, default="não informado") -> str:
    """Sanitiza campo: remove None, trunca texto longo."""
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    return text[:MAX_CAMPO_LEN]


TOOLS: dict = {
    # ─── COBRANÇAS ──────────────────────────────────────────────────────────────
    "cobranca_lembrete1": {
        "label": "1º Lembrete de Cobrança",
        "category": "cobranca",
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 512,
        "system": (
            "Você é um especialista em comunicação para escritórios contábeis brasileiros. "
            "Redija e-mails profissionais, cordiais e eficazes para cobrança de honorários. "
            "Nunca use linguagem ameaçadora ou constrangedora. "
            "Retorne APENAS o texto do e-mail, com Assunto: na primeira linha, "
            "depois uma linha em branco, depois o corpo. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija o primeiro lembrete de honorários em atraso.\n\n"
            f"Cliente: {_s(c.get('cliente'))}\n"
            f"Empresa do cliente: {_s(c.get('empresa'))}\n"
            f"Valor: R$ {_s(c.get('valor'))}\n"
            f"Vencimento original: {_s(c.get('vencimento'))}\n"
            f"Assinado por (contador): {_s(c.get('contador'))}\n"
            f"Escritório: {_s(c.get('escritorio'))}\n\n"
            f"Tom: cordial, sem constrangimento, máximo 6 linhas no corpo."
        ),
    },
    "cobranca_lembrete2": {
        "label": "2º Lembrete de Cobrança",
        "category": "cobranca",
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 600,
        "system": (
            "Você é um especialista em comunicação para escritórios contábeis brasileiros. "
            "Redija e-mails de cobrança profissionais, firmes e respeitosos. "
            "Mencione, de forma sutil, que a continuidade dos serviços pode ser afetada. "
            "Retorne APENAS o texto do e-mail, com Assunto: na primeira linha, "
            "depois uma linha em branco, depois o corpo. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija o segundo e-mail de cobrança de honorários.\n\n"
            f"Cliente: {_s(c.get('cliente'))}\n"
            f"Valor: R$ {_s(c.get('valor'))}\n"
            f"Dias em atraso: {_s(c.get('dias'))}\n"
            f"Assinado por (contador): {_s(c.get('contador'))}\n\n"
            f"Tom: firme mas respeitoso. Máximo 7 linhas no corpo."
        ),
    },
    "cobranca_parcelamento": {
        "label": "Proposta de Parcelamento",
        "category": "cobranca",
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 700,
        "system": (
            "Você é um especialista em comunicação para escritórios contábeis brasileiros. "
            "Redija propostas de parcelamento de honorários que preservem o relacionamento. "
            "Tom: parceiro, não credor. Demonstre flexibilidade e cuidado com o cliente. "
            "Retorne APENAS o texto do e-mail, com Assunto: na primeira linha, "
            "depois uma linha em branco, depois o corpo. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um e-mail propondo parcelamento de honorários atrasados.\n\n"
            f"Cliente: {_s(c.get('cliente'))}\n"
            f"Valor total em atraso: R$ {_s(c.get('valor'))}\n"
            f"Meses em atraso: {_s(c.get('meses'))}\n"
            f"Parcelas propostas: {_s(c.get('parcelas'))}x\n"
            f"Assinado por (contador): {_s(c.get('contador'))}\n\n"
            f"Tom: colaborativo, parceiro. Máximo 9 linhas no corpo."
        ),
    },
    "cobranca_reajuste": {
        "label": "Comunicado de Reajuste",
        "category": "cobranca",
        "model": "claude-sonnet-4-6",
        "max_tokens": 800,
        "system": (
            "Você é um especialista em comunicação estratégica para escritórios contábeis brasileiros. "
            "Redija comunicados de reajuste de honorários que valorizem os serviços prestados "
            "e minimizem cancelamentos. Justifique o aumento com base em valor entregue, "
            "não apenas em custos. "
            "Retorne APENAS o texto do e-mail, com Assunto: na primeira linha, "
            "depois uma linha em branco, depois o corpo. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um e-mail comunicando reajuste de honorários.\n\n"
            f"Cliente: {_s(c.get('cliente'))}\n"
            f"Valor atual mensal: R$ {_s(c.get('valor_atual'))}\n"
            f"Percentual de reajuste: {_s(c.get('percentual'))}%\n"
            f"Data de vigência do novo valor: {_s(c.get('data_vigencia'))}\n"
            f"Assinado por (contador): {_s(c.get('contador'))}\n\n"
            f"Justifique com base em valor, não apenas inflação. Máximo 10 linhas no corpo."
        ),
    },

    # ─── RELATÓRIOS ─────────────────────────────────────────────────────────────
    "relatorio_mensal": {
        "label": "Relatório Gerencial Mensal",
        "category": "relatorio",
        "model": "claude-sonnet-4-6",
        "max_tokens": 1200,
        "system": (
            "Você é um contador consultor especializado em traduzir números para empresários "
            "brasileiros sem formação financeira. "
            "Redija relatórios gerenciais claros, sem jargão técnico excessivo, "
            "que gerem valor percebido e orientem decisões. "
            "Use linguagem direta, destaque o que importa, seja acionável. "
            "Retorne APENAS o relatório formatado. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um relatório gerencial mensal em linguagem simples.\n\n"
            f"Empresa: {_s(c.get('empresa'))}\n"
            f"Mês/Ano: {_s(c.get('mes_ano'))}\n"
            f"Faturamento bruto: R$ {_s(c.get('faturamento'))}\n"
            f"Despesas totais: R$ {_s(c.get('despesas'))}\n"
            f"Lucro líquido: R$ {_s(c.get('lucro'))}\n"
            f"Observações do contador: {_s(c.get('observacoes'), 'Nenhuma')}\n"
            + (f"Preparado por: {_s(c.get('contador'))}\n" if c.get('contador') else "") +
            f"\nEstruture em:\n"
            f"1. Resumo Executivo (2-3 frases)\n"
            f"2. Destaques do Mês (3 pontos positivos ou neutros)\n"
            f"3. Pontos de Atenção (1-2 alertas práticos)\n"
            f"4. Próximos Passos sugeridos (1-2 ações)"
        ),
    },
    "relatorio_dre": {
        "label": "Análise de DRE",
        "category": "relatorio",
        "model": "claude-sonnet-4-6",
        "max_tokens": 1200,
        "system": (
            "Você é um contador consultor especializado em explicar DRE (Demonstração do Resultado "
            "do Exercício) para donos de negócio sem formação financeira. "
            "Use linguagem simples, analogias do cotidiano quando útil, seja direto. "
            "Destaque o que foi bem, o que preocupa e uma recomendação prática. "
            "Retorne APENAS a análise formatada. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Analise o DRE abaixo e explique para o dono da empresa em linguagem simples.\n\n"
            f"Empresa: {_s(c.get('empresa'))}\n"
            f"Período: {_s(c.get('periodo'))}\n\n"
            f"DRE:\n{_s(c.get('dre'))}\n\n"
            + (f"Preparado por: {_s(c.get('contador'))}\n\n" if c.get('contador') else "") +
            f"Estruture em:\n"
            f"1. O que esses números significam (2-3 frases simples)\n"
            f"2. O que foi bem\n"
            f"3. O que preocupa\n"
            f"4. Uma recomendação prática para o próximo período"
        ),
    },
    "relatorio_comparativo": {
        "label": "Comparativo Mensal",
        "category": "relatorio",
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "system": (
            "Você é um assistente contábil brasileiro especializado em análises comparativas mensais "
            "para pequenas e médias empresas. "
            "Tom: claro, sem alarmismo, orientado a decisão. "
            "Retorne APENAS o texto do comparativo formatado. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um comparativo mensal para o cliente.\n\n"
            f"Empresa: {_s(c.get('empresa'))}\n\n"
            f"Dados do mês anterior:\n{_s(c.get('mes_anterior'))}\n\n"
            f"Dados do mês atual:\n{_s(c.get('mes_atual'))}\n\n"
            + (f"Preparado por: {_s(c.get('contador'))}\n\n" if c.get('contador') else "") +
            f"Destaque variações relevantes (positivas e negativas). "
            f"Inclua percentual de variação quando possível. Máximo 10 linhas."
        ),
    },
    "relatorio_anual": {
        "label": "Resumo Anual Executivo",
        "category": "relatorio",
        "model": "claude-sonnet-4-6",
        "max_tokens": 1500,
        "system": (
            "Você é um consultor contábil especializado em apresentações executivas anuais "
            "para clientes de pequeno e médio porte. "
            "Redija resumos que sirvam como base para reunião anual de resultado. "
            "Tom: profissional, positivo mas honesto. "
            "Retorne APENAS o resumo formatado. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um resumo anual executivo para apresentação ao cliente.\n\n"
            f"Empresa: {_s(c.get('empresa'))}\n"
            f"Ano de referência: {_s(c.get('ano'))}\n\n"
            f"Dados anuais fornecidos:\n{_s(c.get('dados'))}\n\n"
            + (f"Preparado por: {_s(c.get('contador'))}\n\n" if c.get('contador') else "") +
            f"Estruture em:\n"
            f"1. Performance Geral do Ano (parágrafo)\n"
            f"2. 3 Conquistas do Período\n"
            f"3. 2 Pontos de Atenção para o próximo ano\n"
            f"4. Perspectivas e Recomendações"
        ),
    },

    # ─── RECEITA FEDERAL ────────────────────────────────────────────────────────
    "receita_intimacao": {
        "label": "Resposta a Intimação",
        "category": "receita",
        "model": "claude-opus-4-6",
        "max_tokens": 1800,
        "system": (
            "Você é um especialista em comunicação fiscal e tributária brasileira. "
            "Redija respostas formais à Receita Federal com linguagem técnica, clara e respeitosa. "
            "O texto deve ser objetivo, demonstrar boa-fé e apresentar os fatos de forma organizada. "
            "IMPORTANTE: o texto gerado é um RASCUNHO que deve ser revisado por um profissional "
            "habilitado antes do envio. "
            "Retorne APENAS o texto da resposta formal. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija uma resposta formal à intimação da Receita Federal.\n\n"
            f"Contribuinte: {_s(c.get('contribuinte'))}\n"
            f"CNPJ/CPF: {_s(c.get('cnpj'))}\n\n"
            f"Texto da intimação recebida:\n{_s(c.get('intimacao'))}\n\n"
            f"Informações e fatos para embasar a resposta:\n{_s(c.get('informacoes'))}\n\n"
            f"Estruture: identificação do contribuinte, referência à intimação recebida, "
            f"esclarecimentos objetivos, conclusão com pedido de arquivamento."
        ),
    },
    "receita_defesa": {
        "label": "Defesa / Impugnação",
        "category": "receita",
        "model": "claude-opus-4-6",
        "max_tokens": 2500,
        "system": (
            "Você é um especialista em defesa fiscal e tributária brasileira. "
            "Redija impugnações administrativas técnicas, objetivas e bem fundamentadas. "
            "Use linguagem jurídica adequada mas acessível. Demonstre embasamento legal sempre que possível. "
            "IMPORTANTE: este texto é um RASCUNHO inicial que DEVE ser revisado e complementado "
            "por um contador ou advogado tributarista habilitado antes da apresentação. "
            "Retorne APENAS o texto da impugnação. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija uma impugnação administrativa ao auto de infração abaixo.\n\n"
            f"Contribuinte: {_s(c.get('contribuinte'))}\n"
            f"CNPJ/CPF: {_s(c.get('cnpj'))}\n\n"
            f"Descrição do auto de infração:\n{_s(c.get('auto'))}\n\n"
            f"Argumentos e fatos para a defesa:\n{_s(c.get('argumentos'))}\n\n"
            f"Estruture: qualificação do contribuinte, tempestividade da impugnação, "
            f"mérito (fatos e fundamentos jurídicos), pedido final."
        ),
    },
    "receita_comunicar_cliente": {
        "label": "Comunicar Cliente sobre Fisco",
        "category": "receita",
        "model": "claude-sonnet-4-6",
        "max_tokens": 700,
        "system": (
            "Você é um assistente de comunicação contábil. "
            "Redija e-mails que informam clientes sobre notificações fiscais sem gerar pânico, "
            "demonstrando que o contador tem controle da situação. "
            "Ajuste o tom à gravidade: rotineiro = tranquilo; moderado = sério mas controlado; "
            "grave = urgente mas profissional. "
            "Retorne APENAS o texto do e-mail, com Assunto: na primeira linha, "
            "depois uma linha em branco, depois o corpo. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um e-mail comunicando uma notificação fiscal ao cliente.\n\n"
            f"Cliente: {_s(c.get('cliente'))}\n"
            f"Assunto da notificação: {_s(c.get('assunto'))}\n"
            f"Nível de gravidade: {_s(c.get('gravidade'))}\n"
            f"Assinado por (contador): {_s(c.get('contador'))}\n\n"
            f"Tom: profissional, tranquilizador, demonstrando controle. Máximo 9 linhas no corpo."
        ),
    },
    "receita_parcelamento": {
        "label": "Carta de Parcelamento Fiscal",
        "category": "receita",
        "model": "claude-opus-4-6",
        "max_tokens": 1200,
        "system": (
            "Você é um especialista em comunicação tributária brasileira. "
            "Redija cartas formais de solicitação de parcelamento fiscal demonstrando boa-fé "
            "e colaboração com o Fisco. Linguagem técnica e respeitosa. "
            "IMPORTANTE: o texto gerado é um RASCUNHO que deve ser revisado por profissional "
            "habilitado antes do envio. "
            "Retorne APENAS o texto da carta formal. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija uma carta formal de solicitação de parcelamento de débito fiscal.\n\n"
            f"Contribuinte: {_s(c.get('contribuinte'))}\n"
            f"CNPJ/CPF: {_s(c.get('cnpj'))}\n"
            f"Valor total do débito: R$ {_s(c.get('debito'))}\n"
            f"Tributo e período: {_s(c.get('tributo'))}\n"
            f"Número de parcelas solicitadas: {_s(c.get('parcelas'))}\n\n"
            f"Tom: formal, colaborativo, boa-fé. Inclua identificação completa, "
            f"pedido formal de parcelamento e justificativa."
        ),
    },

    # ─── COMUNICAÇÃO COM CLIENTES ────────────────────────────────────────────────
    "cliente_documentos": {
        "label": "Solicitação de Documentos",
        "category": "cliente",
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 600,
        "system": (
            "Você é um assistente de comunicação para escritórios contábeis brasileiros. "
            "Redija e-mails profissionais e objetivos solicitando documentos a clientes. "
            "Tom: cordial, organizado, sem burocracia desnecessária. "
            "Liste os documentos de forma clara com marcadores. "
            "Retorne APENAS o texto do e-mail, com Assunto: na primeira linha, "
            "depois uma linha em branco, depois o corpo. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um e-mail solicitando documentos ao cliente.\n\n"
            f"Cliente: {_s(c.get('cliente'))}\n"
            f"Empresa do cliente: {_s(c.get('empresa'))}\n"
            f"Finalidade: {_s(c.get('finalidade'))}\n"
            f"Documentos necessários:\n{_s(c.get('documentos'))}\n"
            f"Prazo para envio: {_s(c.get('prazo'))}\n"
            f"Assinado por (contador): {_s(c.get('contador'))}\n\n"
            f"Tom: cordial, organizado. Explique brevemente o motivo da solicitação. "
            f"Liste os documentos com marcadores. Máximo 10 linhas no corpo."
        ),
    },
    "cliente_obrigacoes": {
        "label": "Lembrete de Obrigação Fiscal",
        "category": "cliente",
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 550,
        "system": (
            "Você é um assistente de comunicação para escritórios contábeis brasileiros. "
            "Redija lembretes de obrigações fiscais e trabalhistas para clientes. "
            "Tom: informativo, profissional, sem alarmismo desnecessário. "
            "Deixe claro o prazo e a consequência do não-cumprimento de forma educativa. "
            "Retorne APENAS o texto do e-mail, com Assunto: na primeira linha, "
            "depois uma linha em branco, depois o corpo. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um e-mail de lembrete sobre obrigação fiscal/trabalhista.\n\n"
            f"Cliente: {_s(c.get('cliente'))}\n"
            f"Empresa do cliente: {_s(c.get('empresa'))}\n"
            f"Obrigação: {_s(c.get('obrigacao'))}\n"
            f"Prazo de entrega/pagamento: {_s(c.get('prazo'))}\n"
            f"Penalidade por atraso: {_s(c.get('penalidade'), 'multa e juros conforme legislação')}\n"
            f"Ação necessária do cliente: {_s(c.get('acao'), 'aguardar nosso contato')}\n"
            f"Assinado por (contador): {_s(c.get('contador'))}\n\n"
            f"Tom: profissional e claro. Destaque a data-limite. Máximo 8 linhas no corpo."
        ),
    },
    "cliente_abertura": {
        "label": "Orientações para Abertura de Empresa",
        "category": "cliente",
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "system": (
            "Você é um contador consultor especializado em abertura de empresas no Brasil. "
            "Redija orientações claras, em linguagem acessível, para clientes que desejam abrir uma empresa. "
            "Cubra etapas principais, documentos necessários e próximos passos. "
            "Tom: orientador, seguro, sem juridiquês excessivo. "
            "Retorne APENAS o texto do e-mail/comunicado. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um comunicado orientando o cliente sobre abertura de empresa.\n\n"
            f"Nome do futuro sócio/proprietário: {_s(c.get('cliente'))}\n"
            f"Tipo de empresa / regime: {_s(c.get('tipo_empresa'))}\n"
            f"Ramo de atividade: {_s(c.get('ramo'))}\n"
            f"Observações específicas: {_s(c.get('observacoes'), 'nenhuma')}\n"
            f"Assinado por (contador): {_s(c.get('contador'))}\n\n"
            f"Inclua: etapas do processo, documentos que o cliente deve providenciar, "
            f"prazo estimado e próximos passos com o escritório."
        ),
    },
    "cliente_encerramento": {
        "label": "Encerramento / Alteração Societária",
        "category": "cliente",
        "model": "claude-sonnet-4-6",
        "max_tokens": 900,
        "system": (
            "Você é um contador especializado em alterações societárias e encerramento de empresas no Brasil. "
            "Redija comunicados claros sobre o processo de encerramento ou alteração, "
            "orientando o cliente sobre etapas, documentos e obrigações pendentes. "
            "Tom: profissional, empático (encerramento pode ser momento delicado), objetivo. "
            "Retorne APENAS o texto do e-mail/comunicado. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um comunicado sobre encerramento ou alteração societária.\n\n"
            f"Empresa: {_s(c.get('empresa'))}\n"
            f"CNPJ: {_s(c.get('cnpj'))}\n"
            f"Tipo de procedimento: {_s(c.get('tipo'))}\n"
            f"Instruções e contexto: {_s(c.get('instrucoes'))}\n"
            f"Assinado por (contador): {_s(c.get('contador'))}\n\n"
            f"Inclua: etapas do processo, documentos necessários, obrigações a cumprir antes do encerramento/alteração, "
            f"prazo estimado e próximos passos."
        ),
    },
    # ─── FISCAL ─────────────────────────────────────────────────────────────────
    "fiscal_checklist": {
        "label": "Checklist de Obrigações Mensais",
        "category": "fiscal",
        "model": "claude-sonnet-4-6",
        "max_tokens": 1200,
        "system": (
            "Você é um contador especialista em obrigações fiscais brasileiras. "
            "Gere checklists detalhados e precisos de obrigações mensais conforme o regime tributário. "
            "Inclua prazos, órgãos responsáveis e penalidades por descumprimento. "
            "Formate como lista clara com seções por tipo de obrigação (federal, estadual, municipal, trabalhista). "
            "Retorne APENAS o checklist formatado. Sem introduções ou explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Gere um checklist de obrigações mensais para o mês de {_s(c.get('competencia'))}.\n\n"
            f"Empresa: {_s(c.get('empresa'))}\n"
            f"Regime tributário: {_s(c.get('regime'))}\n"
            f"Porte / tipo: {_s(c.get('porte'), 'não informado')}\n"
            f"Atividade principal: {_s(c.get('atividade'), 'não informada')}\n"
            f"Possui funcionários: {_s(c.get('funcionarios'), 'não informado')}\n"
            f"Observações específicas: {_s(c.get('observacoes'), 'nenhuma')}\n\n"
            f"Inclua prazos, valores de multa por atraso quando aplicável, "
            f"e uma coluna de status (A fazer / Entregue)."
        ),
    },
    "fiscal_declaracao": {
        "label": "Guia de Declaração ao Cliente",
        "category": "fiscal",
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "system": (
            "Você é um contador consultor especializado em declarações fiscais brasileiras. "
            "Redija guias de orientação para clientes sobre declarações (IRPF, IRPJ, DEFIS, DASN-SIMEI, etc.), "
            "em linguagem clara e acessível. "
            "Tom: didático, sem juridiquês, tranquilizador. "
            "Retorne APENAS o texto do comunicado/guia. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um guia de orientação ao cliente sobre declaração fiscal.\n\n"
            f"Cliente: {_s(c.get('cliente'))}\n"
            f"Tipo de declaração: {_s(c.get('declaracao'))}\n"
            f"Ano-calendário / exercício: {_s(c.get('exercicio'))}\n"
            f"Prazo de entrega: {_s(c.get('prazo'))}\n"
            f"Documentos necessários: {_s(c.get('documentos'), 'padrão conforme tipo')}\n"
            f"Pontos de atenção específicos: {_s(c.get('atencao'), 'nenhum')}\n"
            f"Assinado por (contador): {_s(c.get('contador'))}\n\n"
            f"Inclua: o que é a declaração, por que é importante, "
            f"documentos que o cliente precisa providenciar, prazo e próximos passos."
        ),
    },
    "fiscal_mudanca_regime": {
        "label": "Comunicado de Mudança de Regime",
        "category": "fiscal",
        "model": "claude-sonnet-4-6",
        "max_tokens": 900,
        "system": (
            "Você é um contador especialista em planejamento tributário brasileiro. "
            "Redija comunicados sobre mudança de regime tributário de forma clara e estratégica. "
            "Explique os impactos práticos, vantagens e próximos passos. "
            "Tom: consultivo, seguro, sem alarmismo. "
            "Retorne APENAS o texto do comunicado. Sem explicações adicionais."
        ),
        "build_user": lambda c: (
            f"Redija um comunicado sobre mudança de regime tributário.\n\n"
            f"Empresa: {_s(c.get('empresa'))}\n"
            f"CNPJ: {_s(c.get('cnpj'), 'não informado')}\n"
            f"Regime atual: {_s(c.get('regime_atual'))}\n"
            f"Novo regime: {_s(c.get('regime_novo'))}\n"
            f"Vigência da mudança: {_s(c.get('vigencia'))}\n"
            f"Motivo / justificativa: {_s(c.get('motivo'))}\n"
            f"Impacto estimado: {_s(c.get('impacto'), 'a ser detalhado')}\n"
            f"Assinado por (contador): {_s(c.get('contador'))}\n\n"
            f"Inclua: o que muda na prática, benefícios esperados, "
            f"obrigações do novo regime e ações que o cliente deve tomar."
        ),
    },
}


def get_tool_config(tool_key: str) -> dict | None:
    return TOOLS.get(tool_key)


def build_prompt(tool_key: str, campos: dict) -> tuple[str, str, int, str]:
    """
    Retorna (system_prompt, user_message, max_tokens, model).
    Lança KeyError se tool_key não existir.
    """
    config = TOOLS[tool_key]
    system = config["system"]
    user = config["build_user"](campos)
    max_tokens = config["max_tokens"]
    model = config["model"]
    return system, user, max_tokens, model


def auto_title(tool_key: str, campos: dict) -> str:
    """Gera um título curto e legível para uma geração."""
    label = TOOLS.get(tool_key, {}).get("label", tool_key)
    client = _s(campos.get("cliente") or campos.get("contribuinte") or campos.get("empresa"), "")
    if client and client != "não informado":
        return f"{label} — {client[:40]}"
    return label
