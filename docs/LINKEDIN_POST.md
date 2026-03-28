# Post LinkedIn — ProcessSigma Delivery Intelligence Pipeline

---

Construí um Business Case completo de Black Belt com dados reais — unindo Engenharia de Dados, Six Sigma e Process Mining em um único pipeline.

Não foi um tutorial. Foi um projeto real, com dados reais, decisões reais e erros reais que precisaram ser resolvidos no caminho.

**O problema investigado:**

Uma cadeia de suprimentos global com mais de 180 mil registros, operando há 3 anos com mais de 57% de atraso nas entregas — sem que ninguém soubesse exatamente por quê.

**O que foi construído:**

Um pipeline completo com arquitetura Medalhão (Bronze → Silver → Gold) conectado ao Supabase, ETL em Python, análise estatística em R, Process Mining com PM4Py e GraphViz — tudo consumido por um dashboard interativo em Streamlit e conectado ao Power BI.

**Os números que saíram:**

- 180.519 registros brutos processados → 65.752 pedidos únicos analisados
- Nível Sigma: 1,5σ — processo crítico, estável no problema por 37 meses consecutivos
- DPMO: 573.336 — meta é chegar a 6.210 (4 sigma)
- Cpk: 0,11 — processo operando a menos de 10% da capacidade mínima aceitável
- 37.698 casos críticos mapeados via Process Mining

**O que os dados provaram:**

Três testes estatísticos — Qui-Quadrado (p=0,178), ANOVA (p=0,585) e Teste T (p=0,058) — chegaram à mesma conclusão: a causa raiz não está nas regiões.

Mesmo a diferença entre a pior região (Central Africa, 60,6%) e a melhor (Canada, 52,8%) é estatisticamente ruído.

O problema é sistêmico. Está no processo central de agendamento de envios — e afeta as 23 regiões com a mesma intensidade.

**O que aprendi que nenhum curso ensina:**

R e Python não são concorrentes — são complementares. Python faz o ETL e serve o dashboard. R faz o que o Minitab faz para os Belts: Cartas de Controle, Análise de Capabilidade, Testes de Hipótese — com output direto, sem implementar do zero.

Process Mining não substitui a estatística — ela a complementa. O Six Sigma diz quanto o processo está desviando. O mapa de processo mostra onde no fluxo o desvio acontece.

Um processo estável no lugar errado é tão preocupante quanto um processo fora de controle. Estável em 57% de atraso durante 3 anos não é acaso — é design.

**Stack utilizada:**

Python · R · Supabase (PostgreSQL) · PM4Py · GraphViz · Streamlit · Plotly · Power BI · renv · qcc · tidyverse · ggplot2

**Projeto:**

Dashboard: em breve no Streamlit Cloud
Repositório: github.com/seu-usuario/processsigma-delivery-intelligence

Este é o projeto Lab. A Vitrine está em construção com deploy completo e documentação para certificação Black Belt.

Aprendizado contínuo, projeto a projeto.

---

*Hashtags sugeridas:*
#sixsigma #blackbelt #engenhariadadados #python #rlanguage #supplychain #processimprovement #dataanalytics #streamlit #powerbi #processmining #portfólio #qualidade #leanseissigma
