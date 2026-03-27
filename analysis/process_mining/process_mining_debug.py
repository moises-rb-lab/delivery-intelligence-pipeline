"""
Script para debug do Process Mining - testa a configuração pm4py
"""

import sys
import traceback
from loguru import logger

logger.info("Iniciando teste de configuração pm4py...")

# Teste 1: Importar pm4py
try:
    import pm4py
    logger.success(f"✅ pm4py importado com sucesso (v{pm4py.__version__})")
except ImportError as e:
    logger.error(f"❌ Erro ao importar pm4py: {e}")
    sys.exit(1)

# Teste 2: Importar dataframe_utils
try:
    from pm4py.objects.log.util import dataframe_utils
    logger.success("✅ dataframe_utils importado")
except ImportError as e:
    logger.error(f"❌ Erro ao importar dataframe_utils: {e}")
    sys.exit(1)

# Teste 3: Verificar GraphViz
try:
    import pm4py.vis
    logger.success("✅ pm4py.vis disponível")
except ImportError as e:
    logger.error(f"❌ Erro ao importar pm4py.vis: {e}")

# Teste 4: Verificar se graphviz está instalado
try:
    import graphviz
    logger.success(f"✅ graphviz importado")
except ImportError as e:
    logger.warning("⚠️ graphviz não instalado (necessário para visualizações)")
    logger.warning("   Instale com: pip install graphviz")

# Teste 5: Verificar se graphviz executável está disponível
try:
    import subprocess
    result = subprocess.run(['dot', '-V'], capture_output=True, text=True)
    logger.success(f"✅ GraphViz (dot) disponível no sistema")
except FileNotFoundError:
    logger.warning("⚠️ GraphViz executável não encontrado no PATH")
    logger.warning("   Windows: https://graphviz.org/download/")
    logger.warning("   Linux: sudo apt-get install graphviz")
    logger.warning("   Mac: brew install graphviz")

logger.success("\n✅ Testes concluídos! Pronto para usar Process Mining")
