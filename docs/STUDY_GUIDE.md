# ProcessSigma — Delivery Intelligence Pipeline
## Guia de Estudo Completo — Do Conceito à Produção

---

## Como usar este guia

Este documento foi escrito para ser lido com o projeto aberto na frente. Cada seção explica o porquê de cada decisão técnica, o que cada indicador significa e como interpretá-lo. O objetivo não é memorizar — é entender profundamente para conseguir explicar, adaptar e evoluir.

---

## Parte 1 — Contexto e Motivação

### Por que Logística e Six Sigma?

Logística é uma das áreas onde a variabilidade tem custo direto e mensurável. Um dia de atraso tem custo. Uma avaria tem custo. Uma devolução tem custo. Isso significa que cada indicador que construímos tem um valor de negócio claro — e é isso que diferencia um projeto de portfólio de um exercício acadêmico.

Este projeto combina duas perspectivas que raramente aparecem juntas: a visão do Engenheiro de Dados (pipeline, automação, tempo real) e a visão do Black Belt (variabilidade, capabilidade, causa raiz). O resultado é um Business Case completo — não apenas um dashboard bonito.

### Por que dados reais?

O dataset DataCo Smart Supply Chain contém mais de 180 mil registros reais de uma cadeia de suprimentos global. Dados reais têm problemas reais — duplicatas por modelo de negócio (múltiplos itens por pedido), campos com risco de atraso que precisam ser interpretados, regiões com nomes inconsistentes. Tratar esses problemas é exatamente o trabalho de um analista no dia a dia.

---

## Parte 2 — Arquitetura Medalhão

### O conceito

A arquitetura medalhão divide o pipeline em três camadas com responsabilidades distintas:

- **Bronze** é o galpão de recebimento — a matéria-prima chega exatamente como veio, sem nenhum processamento
- **Silver** é a linha de produção — a matéria-prima é inspecionada, limpa e padronizada
- **Gold** é o produto acabado na prateleira — pronto para o cliente final consumir

### Por que essa separação é importante?

Sem essa separação, qualquer problema no processamento pode corromper os dados originais de forma irreversível. Com a Bronze intacta, sempre é possível reprocessar tudo do zero se algo der errado.

Cada camada atende um público diferente:
- A **Bronze** é do engenheiro — ele precisa auditar a origem
- A **Silver** é do analista — ele precisa de dados limpos e confiáveis
- A **Gold** é do negócio — ele precisa de respostas, não de dados brutos

### Camada Bronze — decisões técnicas

Todas as colunas preservam o tipo original do CSV. O objetivo é guardar o dado exatamente como chegou da fonte. O campo `ingested_at` registra o momento da ingestão e `source` registra a origem (`csv_upload` ou `form`) — isso garante rastreabilidade total.

Não há tratamento de duplicatas na Bronze. O DataCo registra uma linha por item do pedido — um pedido com 3 produtos gera 3 linhas. Isso é comportamento esperado do sistema ERP. A Bronze guarda tudo; a Silver consolida.

### Camada Silver — decisões técnicas

Dois campos calculados foram adicionados que não existem na fonte:

**delay_days** = days_real - days_scheduled

Representa o desvio entre o prazo prometido e o prazo realizado. Negativo significa adiantado, positivo significa atrasado. É a base de todos os cálculos de CEP e capabilidade.

**is_late** = delay_days > 0

Booleano que responde: a entrega foi atrasada? É a base do cálculo de OTD e DPMO.

A deduplicação por `order_id` reduziu 180.519 registros para 65.752 pedidos únicos — confirmando o modelo de múltiplos itens por pedido do DataCo.

### Camada Gold — decisões técnicas

Duas tabelas de agregação com atualização por período:

**gold_otd** — OTD por região e mês
**gold_sigma** — DPMO e Nível Sigma por mês

Ambas têm Realtime habilitado no Supabase — o Streamlit se inscreve via WebSocket e atualiza os indicadores automaticamente a cada INSERT, sem necessidade de refresh manual.

---

## Parte 3 — Os Indicadores Six Sigma

### OTD — On-Time Delivery

**O que é:** percentual de pedidos entregues dentro do prazo acordado.

**Fórmula:**
```
OTD % = (pedidos com is_late = False / total de pedidos) × 100
```

**Como interpretar:**
- Acima de 95% — processo sob controle, dentro das especificações
- Entre 85% e 95% — atenção, investigar causas
- Abaixo de 85% — crítico, redesenho de processo necessário

**No projeto:** o OTD global ficou em 42,7% — muito abaixo de qualquer referência de mercado. Isso confirma a necessidade de intervenção Six Sigma.

---

### DPMO — Defeitos Por Milhão de Oportunidades

**O que é:** quantos defeitos ocorrem a cada um milhão de oportunidades de defeito.

**Fórmula:**
```
DPMO = (total de defeitos / total de oportunidades) × 1.000.000
```

**Defeito neste projeto:** qualquer pedido com `is_late = True`, `damage_flag = True` ou `return_flag = True`.

**Referência Six Sigma:**

| Nível Sigma | DPMO | Classificação |
|-------------|------|---------------|
| 6σ | 3,4 | Classe Mundial |
| 5σ | 233 | Excelente |
| 4σ | 6.210 | Bom — meta mínima |
| 3σ | 66.807 | Atenção |
| 1,5σ | 500.000+ | Crítico |

**No projeto:** DPMO de 573.336 — nível 1,5 sigma. A meta é reduzir para 6.210 DPMO (4 sigma), o que representa uma redução de 98,9%.

---

### Nível Sigma

**O que é:** medida de quão longe o processo está de produzir defeitos, expressa em desvios padrão.

**Como converter DPMO em Sigma:**

Para DPMO acima de 500.000, usa-se tabela de referência direta (a fórmula matemática perde precisão nessa faixa):

```
DPMO ≥ 500.000 → 1,5 sigma
DPMO ≥ 308.538 → 2,0 sigma
DPMO ≥ 66.807  → 3,0 sigma
DPMO ≥ 6.210   → 4,0 sigma
```

**No projeto:** 1,5 sigma em todas as 23 regiões e todos os 37 meses — processo cronicamente crítico e uniforme.

---

### Cp e Cpk — Índices de Capabilidade

**O que é:** medidas de quanto o processo "cabe" dentro das especificações.

**Cp** (capabilidade potencial):
```
Cp = (USL - LSL) / (6 × desvio padrão)
```

**Cpk** (capabilidade real — considera o descentramento):
```
Cpk = min[(USL - média) / (3σ), (média - LSL) / (3σ)]
```

**Como interpretar:**
- Cpk ≥ 1,33 — processo capaz (padrão industrial)
- Cpk entre 1,0 e 1,33 — marginalmente capaz
- Cpk < 1,0 — processo incapaz

**Especificação do projeto:** delay_days deve estar entre -1 e +1 dia (LSL = -1, USL = +1, Target = 0)

**No projeto:** Cp = 0,23 e Cpk = 0,11 — o processo opera a menos de 10% da capacidade mínima aceitável. 37% das entregas ultrapassam o USL de +1 dia.

---

## Parte 4 — Análise Estatística em R

### Por que R e não Python?

Python consegue reproduzir os mesmos resultados, mas com muito mais código e sem um pacote consolidado equivalente ao `qcc`. O `qcc` entrega Carta P, Carta XBar, análise de capabilidade com Cp/Cpk e regras de Nelson em 3 linhas de código. Em Python, isso seria implementado do zero.

> A divisão ideal: Python para ETL, pipeline e entrega. R para CEP, capabilidade e testes estatísticos.

### EDA — Análise Exploratória

**O que revelou:**
- Média de delay_days: 0,57 dias — processo sistematicamente atrasado
- Desvio padrão: 1,49 dias — alta variabilidade
- Taxa de atraso: entre 52% e 61% em todas as 23 regiões

**Arquivo:** `analysis/r/eda.R`
**Exports:** `01_distribuicao_delay.png`, `02_atraso_por_regiao.png`, `03_evolucao_mensal.png`

### CEP — Controle Estatístico de Processo

**Carta P:** monitora a proporção de defeitos (atrasos) ao longo do tempo.

**Resultado:** 37 meses dentro dos limites de controle. O processo é estável — mas estável no nível errado. A linha central em 57,3% de atraso é o problema.

**Carta XBar:** monitora a variabilidade do delay_days médio por período.

**Resultado:** 1 ponto fora de controle em junho/2016 — evento especial que merece investigação de causa raiz específica.

**Análise de Capabilidade:** responde "o processo é capaz de cumprir as especificações?"

**Resultado:** Cpk = 0,11 — não capaz. O processo não consegue manter o delay_days entre -1 e +1 dia de forma consistente.

**Arquivo:** `analysis/r/control_charts.R`
**Exports:** `04_carta_p_atrasos.png`, `05_carta_xbar_delay.png`, `06_capabilidade.png`

### Testes de Hipótese

**Teste Qui-Quadrado**

Pergunta: a taxa de atraso é diferente entre as regiões?

Resultado: p = 0,178 — não rejeita H0. As taxas são estatisticamente iguais entre regiões.

**ANOVA**

Pergunta: o delay_days médio é diferente entre regiões?

Resultado: p = 0,585 — não rejeita H0. Os desvios médios são iguais entre regiões.

**Teste T**

Pergunta: a diferença entre a pior (Central Africa) e a melhor região (Canada) é significativa?

Resultado: p = 0,058 — não rejeita H0. A diferença de 8 pontos percentuais é ruído estatístico.

**Conclusão:** o problema não está nas regiões. A causa raiz está no processo central de agendamento de envios — afeta todas as 23 regiões igualmente.

**Arquivo:** `analysis/r/hypothesis_tests.R`
**Export:** `07_boxplot_regiao.png`

### Nível Sigma Consolidado

Relatório final que agrega todos os indicadores em um resumo executivo.

**Resultado:**
- DPMO: 573.336
- Nível Sigma: 1,5
- Classificação: Crítico
- Gap para meta (4σ): 98,9%
- Recomendação: redesenho do processo central

**Arquivo:** `analysis/r/sigma_level.R`
**Exports:** `08_evolucao_sigma.png`, `09_sigma_por_regiao.png`

---

## Parte 5 — Process Mining com PM4Py

### O que é Process Mining?

Process Mining extrai conhecimento de dados de eventos (event logs) para descobrir, monitorar e melhorar processos. Em vez de desenhar o processo como ele deveria ser, o Process Mining mostra o processo como ele realmente acontece.

### Por que Process Mining complementa o Six Sigma?

O Six Sigma diz **quanto** o processo está desviando (DPMO, Sigma Level). O Process Mining mostra **onde** no fluxo o desvio acontece. São perspectivas complementares — a estatística quantifica, o mapa de processo localiza.

### Heuristics Net

O mapa gerado pelo PM4Py é uma Heuristics Net — uma rede que mostra as atividades do processo e as frequências de transição entre elas. Os números nas arestas representam quantas vezes aquela transição ocorreu nos dados reais.

**No projeto:** 37.698 casos críticos mapeados com dois eventos cada — "Pedido Registrado" e "Envio Concluído". O mapa confirma que todos os casos críticos seguem o mesmo fluxo, reforçando a conclusão de causa raiz sistêmica.

**Arquivo:** `pipeline/silver_to_gold.py`
**Exports:** `analysis/process_mining/process_events_delay_analysis.csv`, `analysis/process_mining/process_map_delay_analysis.png`

---

## Parte 6 — Dashboard Streamlit

### Filosofia de design

O princípio adotado foi: cada página responde uma pergunta específica para um público específico.

### Estrutura das 5 páginas

**Visão Geral** — para o executivo
KPIs consolidados, OTD mensal com linha de meta, top e bottom 5 regiões. Pergunta: "como estamos?"

**OTD por Região** — para o gestor logístico
Filtros por região e período, gráfico de barras com escala de cor, evolução temporal por região. Pergunta: "onde estamos com problema?"

**Sigma e DPMO** — para o analista e o Black Belt
Evolução do nível sigma com faixas de referência, DPMO mensal, tabela de classificação. Pergunta: "qual é a qualidade do processo?"

**Process Mining** — para a liderança e consultoria
Funil de dados com narrativa das duas hipóteses, atrasos por região, evolução temporal, downloads das evidências. Pergunta: "o que os dados estão realmente dizendo?"

**Injeção de Dados** — para operações
Upload CSV/Excel com templates para download, formulário manual para registros individuais. Pergunta: "como alimentar o pipeline?"

---

## Parte 7 — Decisões de Infraestrutura

### Por que Supabase?

O Supabase é um PostgreSQL gerenciado com três características relevantes:

Primeiro, expõe automaticamente uma API REST de todas as tabelas — o Streamlit e o R consomem dados sem precisar escrever SQL de conexão.

Segundo, tem Realtime nativo via WebSocket — indicadores atualizam automaticamente no dashboard quando novos dados chegam.

Terceiro, é PostgreSQL por baixo — todo o SQL escrito aqui funciona em qualquer banco PostgreSQL do mercado.

### Por que API REST no R e não conexão direta?

O Supabase no plano gratuito bloqueia conexões diretas via porta 5432 por padrão. A API REST (`httr2`) é a solução correta para este contexto — mesma abordagem usada pelo SDK Python.

### Por que renv no R?

O `renv` é o equivalente ao `.venv` do Python para projetos R. Ele isola os pacotes do projeto em uma pasta `renv/library/` local, evitando conflitos entre projetos e garantindo reprodutibilidade. O `renv.lock` sobe para o repositório; a pasta `renv/library/` vai no `.gitignore`.

---

## Parte 8 — Resumo Executivo do Business Case

```
Processo analisado:  Order-to-Shipping (pedido ao envio)
Dataset:             DataCo Smart Supply Chain (180.519 registros)
Período:             Janeiro/2015 a Janeiro/2018 (37 meses)

SITUAÇÃO ATUAL
  Nível Sigma:       1,5σ (Crítico)
  DPMO:              573.336
  OTD:               42,7%
  Cpk:               0,11 (processo incapaz)

META
  Nível Sigma:       4,0σ (Bom)
  DPMO:              6.210
  OTD:               ≥ 95%
  Cpk:               ≥ 1,33

EVIDÊNCIAS
  ✅ Carta P:         processo estável em 57,3% de atraso (37 meses)
  ✅ Qui-Quadrado:    p = 0,178 — problema NÃO é regional
  ✅ ANOVA:           p = 0,585 — desvios iguais entre todas as regiões
  ✅ Teste T:         p = 0,058 — diferença pior/melhor região é ruído
  ✅ Process Mining:  37.698 casos críticos com fluxo uniforme

CAUSA RAIZ
  Sistêmica — afeta as 23 regiões com a mesma intensidade.
  Origem: processo central de agendamento de envios.

RECOMENDAÇÃO
  Redesenho do processo de agendamento, não intervenção regional.
  Gap para meta: redução de 98,9% no DPMO.
```

---

## Glossário

| Termo | Definição |
|-------|-----------|
| Arquitetura Medalhão | Padrão de organização de dados em camadas Bronze, Silver e Gold |
| ETL | Extract, Transform, Load — transformação antes de carregar no banco |
| OTD | On-Time Delivery — percentual de entregas no prazo |
| DPMO | Defeitos Por Milhão de Oportunidades |
| Nível Sigma | Medida de qualidade do processo em desvios padrão |
| Cp | Índice de capabilidade potencial do processo |
| Cpk | Índice de capabilidade real — considera descentramento |
| CEP | Controle Estatístico de Processo |
| Carta P | Carta de controle para proporções de defeitos |
| Carta XBar | Carta de controle para médias de subgrupos |
| USL / LSL | Upper/Lower Specification Limit — limites de especificação |
| UCL / LCL | Upper/Lower Control Limit — limites de controle estatístico |
| Process Mining | Técnica de análise que extrai conhecimento de event logs |
| Heuristics Net | Mapa de processo descoberto automaticamente pelo PM4Py |
| renv | Gerenciador de ambiente virtual para projetos R |
| Realtime | Canal WebSocket do Supabase para atualizações em tempo real |
| RLS | Row Level Security — controle de acesso por linha no Supabase |
| Black Belt | Certificação Six Sigma de nível avançado em melhoria de processos |
