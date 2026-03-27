# 🔍 Process Mining - Guia de Uso

## O que é Process Mining?

Process Mining é uma técnica de análise que extrai conhecimento de dados de eventos para descobrir, monitorar e melhorar processos. Neste projeto, utilizamos para analisar padrões de atrasos nas entregas.

## 📊 Saída Gerada

O script `pipeline/silver_to_gold.py` agora gera as seguintes evidências:

### 1. **Event Log CSV** (`analysis/process_events_delay_analysis.csv`)
- Arquivo estruturado com todos os eventos de casos críticos
- Colunas: `case:concept:name`, `concept:name`, `time:timestamp`, `region`, `status`
- Pode ser importado em ferramentas de análise (Excel, Tableau, Power BI)

### 2. **Event Log JSON** (`analysis/process_events_delay_analysis.json`)
- Mesmos dados em formato JSON
- Ideal para integração com dashboards e análises programáticas

### 3. **Mapa de Processo PNG** (`analysis/process_map_delay_analysis.png`)
- **Requer GraphViz instalado**
- Visualização do heuristics net (rede de atividades)
- Mostra fluxos entre "Pedido Registrado" e "Envio Concluído"

## 🚀 Como Executar

### Modo 1: Sem GraphViz (gera CSV e JSON)
```powershell
python pipeline/silver_to_gold.py
```
✅ Funciona imediatamente
✅ Gera CSV e JSON para análise
⚠️ Não gera PNG (opcional)

### Modo 2: Com GraphViz (gera PNG também)

#### Passo 1: Instalar GraphViz

**Opção A - Chocolatey (automático):**
```powershell
.\install_graphviz.ps1
```

**Opção B - Manual:**
1. Download: https://graphviz.org/download/
2. Instale o executável MSI
3. Reinicie o terminal PowerShell

**Opção C - Windows Package Manager:**
```powershell
winget install graphviz
```

#### Passo 2: Executar o Pipeline
```powershell
python pipeline/silver_to_gold.py
```

✅ Gera CSV, JSON e PNG

## 📈 Interpretando os Resultados

### Evento Log (CSV/JSON)
- **Pedido Registrado**: Momento da criação do pedido (order_date)
- **Envio Concluído**: Data calculada (order_date + days_real)
- **Region**: Região geográfica do pedido
- **Status**: "registered" ou "delivered"

### Mapa de Processo (PNG)
O heuristics net mostra:
- **Nós (círculos)**: Atividades ("Pedido Registrado", "Envio Concluído")
- **Arestas (setas)**: Fluxo entre atividades
- **Numero nas arestas**: Frequência da transição
- **Espessura das linhas**: Frequência normalizada

## 💾 Arquivos Gerados

```
analysis/
├── process_events_delay_analysis.csv      # Event log em CSV
├── process_events_delay_analysis.json     # Event log em JSON
└── process_map_delay_analysis.png         # Visualização (requer GraphViz)
```

## 🔧 Troubleshooting

### Erro: "failed to execute WindowsPath('dot')"
**Solução**: GraphViz não está no PATH
1. Instale GraphViz (veja acima)
2. Reinicie o terminal PowerShell
3. Teste: `dot -V`

### Erro: "module 'pm4py.objects.log.util.dataframe_utils' has no attribute..."
**Solução**: Versão incorreta de pm4py
```powershell
pip install --upgrade pm4py
```

### Script completa mas PNG não foi gerado
✅ Isso é OK! Significa que:
- CSV e JSON foram gerados com sucesso
- GraphViz não está disponível
- Você tem todas as evidências de Process Mining! 📊

## 📚 Recursos Adicionais

- **PM4PY Docs**: https://pm4py.fit.fraunhofer.de/
- **GraphViz**: https://graphviz.org/
- **Process Mining**: https://www.en.rwth-aachen.de/go/id/iawz

## 🎓 Para Certificação Black Belt

### Evidências Coletadas:
✅ Event log estruturado (CSV/JSON)
✅ Visualização do processo (PNG)
✅ Estatísticas de casos críticos
✅ Análise de atrasos por região

Todos os arquivos estão em `analysis/` para incluir na sua documentação de certificação!

---

**Última atualização**: 2026-03-27
