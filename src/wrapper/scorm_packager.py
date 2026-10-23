#!/usr/bin/env python3
# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/wrapper/scorm_packager.py
# Descrição: Utilitário automatizado para injeção do INTERA-AI Runtime
#            Wrapper em pacotes de aprendizagem SCORM 2004 / 1.2.
# =====================================================================
"""
Utilitário de Empacotamento Automatizado SCORM (INTERA-AI Packager).

Permite receber um pacote SCORM legado (.zip ou pasta descompactada),
descompactar de forma segura, injetar a chamada para o `intera-wrapper.js`
nos arquivos HTML, atualizar o manifesto `imsmanifest.xml` (garantindo
conformidade normativa na validação do LMS) e reempacotar o artefato pronto
para publicação direta no Moodle.

Uso via Linha de Comando:
    python scorm_packager.py \\
        --input aula_original.zip \\
        --output aula_acessivel.zip

Uso Programático:
    from src.wrapper.scorm_packager import inject_wrapper_into_scorm
    inject_wrapper_into_scorm("aula_original.zip", "aula_acessivel.zip")
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import List, Optional

# Diretório padrão onde o script do wrapper reside
CURRENT_DIR = Path(__file__).resolve().parent
DEFAULT_WRAPPER_JS = CURRENT_DIR / "intera-wrapper.js"


class SCORMPackager:
    """Orquestrador do ciclo de vida de injeção e empacotamento SCORM."""

    def __init__(self, wrapper_path: Optional[Path] = None, verbose: bool = True):
        self.wrapper_path = Path(wrapper_path) if wrapper_path else DEFAULT_WRAPPER_JS
        self.verbose = verbose

        if not self.wrapper_path.exists():
            raise FileNotFoundError(
                f"Arquivo do wrapper não encontrado em: {self.wrapper_path}"
            )

    def log(self, message: str) -> None:
        """Exibe mensagem de log se verbose for True."""
        if self.verbose:
            print(f"[INTERA-AI Packager] {message}")

    def unpack(self, input_path: Path, target_dir: Path) -> Path:
        """Descompacta o pacote SCORM (.zip) ou copia o diretório de origem."""
        if input_path.is_file() and zipfile.is_zipfile(input_path):
            self.log(f"Descompactando pacote SCORM: {input_path.name} -> {target_dir}")
            with zipfile.ZipFile(input_path, "r") as zip_ref:
                zip_ref.extractall(target_dir)
            return target_dir
        elif input_path.is_dir():
            self.log(f"Copiando diretório SCORM de entrada: {input_path}")
            shutil.copytree(input_path, target_dir, dirs_exist_ok=True)
            return target_dir
        else:
            raise ValueError(
                f"Entrada inválida. Deve ser um arquivo .zip ou diretório: {input_path}"
            )

    def find_html_files(self, scorm_dir: Path) -> List[Path]:
        """Localiza todos os arquivos HTML/HTM dentro do pacote SCORM."""
        html_files = []
        for ext in ("*.html", "*.htm", "*.xhtml"):
            html_files.extend(scorm_dir.rglob(ext))
        return sorted(html_files)

    def inject_script_tag(self, html_file: Path, script_rel_name: str = "intera-wrapper.js") -> bool:
        """Injeta a tag <script src="intera-wrapper.js" defer></script> no HTML."""
        try:
            content = html_file.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            self.log(f"Aviso: Não foi possível ler {html_file}: {e}")
            return False

        # Verifica se já está injetado
        if script_rel_name in content:
            self.log(f"Script já presente em {html_file.name}. Ignorando injeção.")
            return False

        # Tag padronizada não destrutiva com atributo defer
        injection_tag = f'\n    <!-- [INTERA-AI Runtime Wrapper] Injetado automaticamente -->\n    <script src="{script_rel_name}" defer></script>\n'

        # Tenta injetar antes de </head>
        if re.search(r'</head>', content, re.IGNORECASE):
            modified = re.sub(r'(</head>)', f'{injection_tag}\\1', content, count=1, flags=re.IGNORECASE)
        elif re.search(r'</body>', content, re.IGNORECASE):
            # Fallback: injeta antes de </body> se não houver </head>
            modified = re.sub(r'(</body>)', f'{injection_tag}\\1', content, count=1, flags=re.IGNORECASE)
        else:
            # Fallback extremo: adiciona no final
            modified = content + injection_tag

        html_file.write_text(modified, encoding="utf-8")
        self.log(f"Wrapper injetado com sucesso em: {html_file.name}")
        return True

    def update_imsmanifest(self, manifest_file: Path, script_rel_name: str = "intera-wrapper.js") -> bool:
        """Registra o intera-wrapper.js dentro do imsmanifest.xml para validação estrita SCORM."""
        if not manifest_file.exists():
            self.log("Aviso: imsmanifest.xml não encontrado na raiz do pacote.")
            return False

        try:
            content = manifest_file.read_text(encoding="utf-8", errors="ignore")
            if script_rel_name in content:
                self.log("Arquivo wrapper já declarado no imsmanifest.xml.")
                return False

            # Inserção de declaração <file href="intera-wrapper.js"/> em resources
            file_declaration = f'    <file href="{script_rel_name}"/>\n'
            if "</resources>" in content:
                updated = content.replace("</resources>", f"{file_declaration}  </resources>")
                manifest_file.write_text(updated, encoding="utf-8")
                self.log(f"imsmanifest.xml atualizado com o arquivo {script_rel_name}.")
                return True
            else:
                self.log("Aviso: Tag </resources> não localizada no manifesto.")
                return False
        except Exception as e:
            self.log(f"Aviso ao atualizar manifesto: {e}")
            return False

    def pack(self, source_dir: Path, output_zip: Path) -> Path:
        """Reempacota o diretório SCORM em um arquivo ZIP limpo."""
        output_zip = output_zip.resolve()
        if output_zip.exists():
            output_zip.unlink()

        self.log(f"Empacotando SCORM adaptado em: {output_zip}")
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    # Caminho relativo para manter estrutura interna do zip
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)

        self.log(f"Pacote gerado com sucesso! Tamanho: {output_zip.stat().st_size / 1024:.2f} KB")
        return output_zip

    def process(self, input_path: Path, output_zip: Path) -> Path:
        """Executa o ciclo completo de desempacotamento, injeção e reempacotamento."""
        input_path = Path(input_path).resolve()
        output_zip = Path(output_zip).resolve()

        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo ou diretório de entrada não existe: {input_path}")

        # Diretório temporário seguro para a operação
        with tempfile.TemporaryDirectory(prefix="intera_scorm_") as tmp_dir:
            work_dir = Path(tmp_dir)

            # 1. Desempacota
            self.unpack(input_path, work_dir)

            # 2. Copia o script wrapper para a raiz do pacote
            target_wrapper = work_dir / "intera-wrapper.js"
            shutil.copy2(self.wrapper_path, target_wrapper)
            self.log(f"Arquivo {self.wrapper_path.name} copiado para a raiz do pacote.")

            # 3. Localiza e injeta nos arquivos HTML
            html_files = self.find_html_files(work_dir)
            if not html_files:
                self.log("Aviso: Nenhum arquivo HTML encontrado no pacote SCORM.")
            else:
                self.log(f"Localizados {len(html_files)} arquivo(s) HTML para injeção.")
                for html_file in html_files:
                    self.inject_script_tag(html_file, "intera-wrapper.js")

            # 4. Atualiza o manifesto do SCORM
            manifest_file = work_dir / "imsmanifest.xml"
            self.update_imsmanifest(manifest_file, "intera-wrapper.js")

            # 5. Empacota no arquivo ZIP de saída
            self.pack(work_dir, output_zip)

        return output_zip


def inject_wrapper_into_scorm(
    input_path: str | Path,
    output_path: str | Path,
    wrapper_path: Optional[str | Path] = None,
    verbose: bool = True
) -> Path:
    """Função utilitária de alto nível para injeção do wrapper no SCORM."""
    packager = SCORMPackager(wrapper_path=wrapper_path, verbose=verbose)
    return packager.process(Path(input_path), Path(output_path))


def main():
    """Ponto de entrada CLI do SCORM Packager."""
    parser = argparse.ArgumentParser(
        description="INTERA-AI SCORM Packager: Injeta o Runtime Wrapper em pacotes SCORM legados."
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Caminho do pacote SCORM de entrada (.zip ou pasta descompactada)."
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Caminho do arquivo ZIP SCORM adaptado a ser gerado."
    )
    parser.add_argument(
        "-w", "--wrapper",
        default=None,
        help="Caminho opcional para versão personalizada do intera-wrapper.js."
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Modo silencioso (sem logs detalhados no terminal)."
    )

    args = parser.parse_args()

    try:
        inject_wrapper_into_scorm(
            input_path=args.input,
            output_path=args.output,
            wrapper_path=args.wrapper,
            verbose=not args.quiet
        )
        print("\n✅ Processamento concluído! Pacote pronto para upload no Moodle.")
    except Exception as e:
        print(f"\n❌ Erro durante o empacotamento: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
