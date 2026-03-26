# Guia de Narrativa — Dashboard Power BI

## Princípio central

> O dashboard não mostra dados. Ele responde perguntas que o gestor já tem na cabeça.

A narrativa segue o fluxo natural de uma reunião de resultado:
**Onde estamos → O que está errado → Por quê → O que fazer.**

---

## Estrutura de páginas sugerida

### Página 1 — Visão Executiva
**Pergunta respondida:** "Como estamos no geral?"

Indicadores em destaque:
- OTD % do mês atual vs meta (ex: 95%)
- Nível Sigma atual
- Total de entregas no período
- Variação vs mês anterior (delta + seta)

> Regra de ouro: o gestor não deve rolar a tela nesta página.
> Tudo visível em um card de 1920x1080.

---

### Página 2 — Análise de Atrasos
**Pergunta respondida:** "Onde os atrasos estão acontecendo?"

Visuais sugeridos:
- Mapa ou gráfico de barras por região (OTD %)
- Linha do tempo de atrasos (trend mensal)
- Top 5 regiões com pior desempenho

---

### Página 3 — Avarias e Devoluções
**Pergunta respondida:** "O que está chegando com problema?"

Visuais sugeridos:
- Taxa de avaria % por categoria de produto
- Taxa de devolução % por região
- Correlação avaria × devolução

---

### Página 4 — Sigma e DPMO
**Pergunta respondida:** "Qual o nível de qualidade do processo?"

Visuais sugeridos:
- Carta de controle (importada do R via visual Python/R)
- DPMO histórico
- Nível Sigma com referência Six Sigma (meta: ≥ 4σ)

---

## Modelagem de dados no Power BI

Conectar direto às tabelas Gold do Supabase via conector PostgreSQL:

```
Server:   db.xxxx.supabase.co
Port:     5432
Database: postgres
Schema:   public
Tabelas:  gold_otd, gold_sigma
```

Criar medidas DAX apenas para:
- Variação percentual mês a mês
- Meta de OTD (parâmetro)
- Classificação do Sigma Level (texto: "Crítico / Atenção / Bom")

> Todo cálculo pesado já chega pronto na camada Gold.
> DAX aqui é só para apresentação, não para transformação.

---

## Entrega para o designer

O analista entrega:
- Modelo de dados conectado e funcional
- Medidas DAX criadas e documentadas
- Esboço das páginas com posição dos visuais (wireframe)
- Este guia de narrativa

O designer recebe e cuida de:
- Paleta de cores e tipografia
- Alinhamento e espaçamento
- Ícones e elementos visuais
- Versão mobile (se necessário)
