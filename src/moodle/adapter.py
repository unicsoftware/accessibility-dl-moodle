# =====================================================================
# Repositório: accessibility-dl-moodle
# Arquivo: src/moodle/adapter.py
# Descrição: Adaptação e integração com a plataforma Moodle.
# =====================================================================
"""
Moodle Adapter
==============

Camada responsável por isolar toda a integração específica com a plataforma Moodle:
- Autenticação e gestão de sessão.
- Navegação por cursos, seções, atividades e recursos.
- Extração do HTML completo dos Objetos de Aprendizagem.
- Suporte a múltiplos modos configuráveis em config.py (DIRECT_URL, REST_API, FALLBACK).
- Geração de metadados de origem (curso, atividade, URL, timestamp, etc.).
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import urllib.parse

from loguru import logger
import requests

from src import config


class MoodleAdapter:
    """Adaptador para comunicação e extração de HTMLs e Objetos de Aprendizagem do Moodle."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = config.MOODLE_TIMEOUT,
    ) -> None:
        self.base_url = (base_url or config.MOODLE_URL).rstrip("/")
        self.token = token or config.MOODLE_TOKEN
        self.username = username or config.MOODLE_USERNAME
        self.password = password or config.MOODLE_PASSWORD
        self.timeout = timeout
        self.session = requests.Session()
        self.authenticated = False

    def authenticate(self) -> bool:
        """Realiza autenticação no Moodle via Web Service token ou formulário.

        Returns:
            bool: True se autenticado com sucesso, False caso contrário.
        """
        if self.token:
            self.authenticated = True
            logger.info("MoodleAdapter autenticado utilizando token Web Service.")
            return True

        login_url = f"{self.base_url}/login/token.php"
        params = {
            "username": self.username,
            "password": self.password,
            "service": "moodle_mobile_app",
        }
        try:
            response = self.session.post(login_url, data=params, timeout=self.timeout)
            if response.status_code == 200 and "token" in response.json():
                self.token = response.json()["token"]
                self.authenticated = True
                logger.info("Autenticação realizada com sucesso no Moodle via login/token.php.")
                return True
        except Exception as err:
            logger.warning(f"Não foi possível autenticar via Moodle Web Service API ({err}). MoodleAdapter operará em modo offline/fallback.")

        self.authenticated = False
        return False

    def fetch_courses(self) -> List[Dict[str, Any]]:
        """Busca a lista de cursos disponíveis no Moodle.

        Returns:
            Lista de dicionários representando cursos.
        """
        if not self.authenticated:
            self.authenticate()

        if self.token:
            ws_url = f"{self.base_url}/webservice/rest/server.php"
            params = {
                "wstoken": self.token,
                "wsfunction": "core_course_get_courses",
                "moodlewsrestformat": "json",
            }
            try:
                res = self.session.get(ws_url, params=params, timeout=self.timeout)
                if res.status_code == 200:
                    courses = res.json()
                    if isinstance(courses, list):
                        return courses
            except Exception as err:
                logger.warning(f"Erro ao buscar cursos da API do Moodle: {err}")

        # Fallback offline para testes/desenvolvimento
        return [
            {"id": 101, "fullname": "Curso de Teste de Acessibilidade 1", "shortname": "ACES-101"},
            {"id": 102, "fullname": "Design Instrucional Inclusivo", "shortname": "DII-202"},
        ]

    def fetch_course_contents(self, course_id: int) -> List[Dict[str, Any]]:
        """Busca o conteúdo (seções e módulos) de um determinado curso.

        Args:
            course_id: ID do curso no Moodle.

        Returns:
            Lista de seções e módulos do curso.
        """
        if self.token:
            ws_url = f"{self.base_url}/webservice/rest/server.php"
            params = {
                "wstoken": self.token,
                "wsfunction": "core_course_get_contents",
                "moodlewsrestformat": "json",
                "courseid": course_id,
            }
            try:
                res = self.session.get(ws_url, params=params, timeout=self.timeout)
                if res.status_code == 200 and isinstance(res.json(), list):
                    return res.json()
            except Exception as err:
                logger.warning(f"Erro ao obter conteúdos do curso {course_id}: {err}")

        # Fallback estruturado de páginas do Moodle
        return [
            {
                "id": 1,
                "name": "Geral",
                "modules": [
                    {
                        "id": 1001,
                        "name": "Página de Boas-Vindas",
                        "modname": "page",
                        "url": f"{self.base_url}/mod/page/view.php?id=1001",
                    },
                    {
                        "id": 1002,
                        "name": "Questionário de Introdução",
                        "modname": "quiz",
                        "url": f"{self.base_url}/mod/quiz/view.php?id=1002",
                    },
                ],
            }
        ]

    def extract_page_html(
        self,
        url: str,
        course_id: Optional[int] = None,
        activity_id: Optional[int] = None,
        activity_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extrai o HTML completo de uma página ou atividade do Moodle e gera metadados de origem.

        Args:
            url: URL da página.
            course_id: ID opcional do curso.
            activity_id: ID opcional da atividade.
            activity_type: Tipo de atividade (ex.: 'page', 'quiz', 'forum').

        Returns:
            Dicionário contendo o HTML completo e metadados de origem.
        """
        html_content = ""
        is_real_response = False
        try:
            res = self.session.get(url, timeout=self.timeout)
            if res.status_code == 200 and res.text and res.text.strip():
                html_content = res.text
                is_real_response = True
        except Exception as err:
            logger.debug(f"Aviso ao acessar URL real ({url}): {err}. Gerando HTML sintético representativo de OA Moodle.")

        if not html_content:
            html_content = self._generate_sample_moodle_page(activity_type or "page")

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return {
            "html": html_content,
            "url": url,
            "course_id": course_id or 101,
            "activity_id": activity_id or 1001,
            "activity_type": activity_type or "page",
            "timestamp": timestamp,
            "source_type": "REAL_MOODLE" if is_real_response else "FALLBACK",
        }

    def fetch_real_pages(self) -> List[Dict[str, Any]]:
        """Extrai páginas respeitando o modo configurado em config.MOODLE_EXTRACTION_MODE.

        Modos suportados:
        - 'DIRECT_URL': scraping de URLs em config.MOODLE_TARGET_URLS
        - 'REST_API': consumo via Web Service API Moodle
        - 'FALLBACK': páginas sintéticas de desenvolvimento
        """
        mode = getattr(config, "MOODLE_EXTRACTION_MODE", "DIRECT_URL")
        logger.info(f"MoodleAdapter iniciando extração de páginas no modo '{mode}'...")

        pages: List[Dict[str, Any]] = []

        if mode == "DIRECT_URL":
            target_urls = getattr(config, "MOODLE_TARGET_URLS", [self.base_url])
            for i, url in enumerate(target_urls):
                logger.info(f"Extraindo HTML da URL direta: {url}")
                p_data = self.extract_page_html(
                    url=url,
                    course_id=101 + i,
                    activity_id=1000 + i,
                    activity_type="page",
                )
                pages.append(p_data)

        elif mode == "REST_API":
            courses = self.fetch_courses()
            for course in courses:
                c_id = course.get("id", 101)
                contents = self.fetch_course_contents(c_id)
                for sec in contents:
                    for mod in sec.get("modules", []):
                        mod_url = mod.get("url", f"{self.base_url}/mod/{mod.get('modname', 'page')}/view.php?id={mod.get('id')}")
                        p_data = self.extract_page_html(
                            url=mod_url,
                            course_id=c_id,
                            activity_id=mod.get("id"),
                            activity_type=mod.get("modname"),
                        )
                        pages.append(p_data)

        else:  # FALLBACK
            logger.info("Utilizando modelo de página Moodle sintética para desenvolvimento offline.")
            p_data = self.extract_page_html(
                url=f"{self.base_url}/sample",
                course_id=101,
                activity_id=1001,
                activity_type="page",
            )
            pages.append(p_data)

        return pages

    def _generate_sample_moodle_page(self, activity_type: str) -> str:
        """Gera uma estrutura HTML típica de um Objeto de Aprendizagem Moodle para fallback."""
        return f"""
        <div class="activity-header moodle-oa" data-activity="{activity_type}">
            <h1>Introdução ao Objeto de Aprendizagem</h1>
            <p>Bem-vindo ao conteúdo interativo.</p>
            <div class="content-block">
                <img src="/moodle/pluginfile.php/1/course/overview.png" alt="Visão geral do curso">
                <p>Confira a figura abaixo:</p>
                <figure>
                    <svg height="100" width="100"><circle cx="50" cy="50" r="40" stroke="black" stroke-width="3" fill="red" /></svg>
                    <figcaption>Gráfico descritivo</figcaption>
                </figure>
            </div>
            <form action="/moodle/mod/quiz/process.php" method="post">
                <label for="answer">Sua Resposta:</label>
                <input type="text" id="answer" name="answer">
                <select name="options">
                    <option value="1">Opção A</option>
                    <option value="2">Opção B</option>
                </select>
                <textarea name="feedback" rows="4" cols="50"></textarea>
                <button type="submit" aria-label="Enviar Resposta">Submeter</button>
            </form>
            <table class="generaltable">
                <thead><tr><th>Critério</th><th>Nota</th></tr></thead>
                <tbody><tr><td>Acessibilidade</td><td>10</td></tr></tbody>
            </table>
            <video controls><source src="media.mp4" type="video/mp4"></video>
            <audio controls><source src="audio.mp3" type="audio/mpeg"></audio>
            <canvas id="chartCanvas" width="200" height="100"></canvas>
            <a href="/moodle/course/view.php?id=101">Voltar ao Curso</a>
        </div>
        """
