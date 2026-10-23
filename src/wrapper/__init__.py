"""Módulo do INTERA-AI Runtime Wrapper e Ferramenta de Empacotamento SCORM."""

from .scorm_packager import inject_wrapper_into_scorm, SCORMPackager

__all__ = ["inject_wrapper_into_scorm", "SCORMPackager"]
