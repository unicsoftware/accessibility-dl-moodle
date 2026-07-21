# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/labeler/__init__.py
# Descrição: Inicializador do pacote labeler.
# =====================================================================

from src.labeler.axe_labeler import AxeLabeler
from src.labeler.wcag_mapper import WCAGMapper

__all__ = ["AxeLabeler", "WCAGMapper"]
