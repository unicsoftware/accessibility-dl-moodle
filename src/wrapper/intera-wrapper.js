/**
 * =====================================================================
 * INTERA-AI Runtime Wrapper (intera-wrapper.js)
 * Versão: 1.0.0 (UFABC - Mestrado em Ciência da Computação)
 * Autor: Elpidio Nascimento Lima Junior
 * Orientadora: Profª. Drª. Juliana Braga
 * 
 * Descrição:
 * Script cliente leve injetado no interior de Objetos de Aprendizagem
 * em formato SCORM 2004. Intercepta o DOM, extrai 22 atributos estruturais,
 * consulta o Gateway Neurosimbólico (ou ONNX Web local), aplica as correções
 * de acessibilidade in-place e preserva 100% da integridade da API SCORM.
 * =====================================================================
 */

(function () {
  'use strict';

  // Configurações padrão do Gateway de Inferência INTERA-AI
  const CONFIG = {
    API_URL: window.INTERA_API_URL || 'https://api.intera-ai.ufabc.br/v1/adapt',
    TIMEOUT_MS: 400, // Degradação graciosa: se o backend não responder em 400ms, mantém o DOM original
    CACHE_PREFIX: 'intera_cache_',
    STORAGE: window.sessionStorage,
    PROFILE_DEFAULT: 'VISUAL'
  };

  /**
   * Calcula o hash SHA-256 síncrono/assíncrono simples para chave de cache
   */
  async function computeHash(text) {
    if (window.crypto && window.crypto.subtle) {
      const buffer = new TextEncoder().encode(text);
      const hashBuffer = await window.crypto.subtle.digest('SHA-256', buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
    // Fallback simples se crypto.subtle não estiver disponível
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      hash = ((hash << 5) - hash) + text.charCodeAt(i);
      hash |= 0;
    }
    return 'h_' + Math.abs(hash);
  }

  /**
   * Extrai o vetor de 22 atributos estruturais definidos no repositório
   * (conforme src/config.py FEATURE_COLUMNS).
   */
  function extract22Features(el) {
    const tag = el.tagName.toLowerCase();
    const htmlSnippet = el.outerHTML || '';
    const innerText = el.innerText || el.textContent || '';

    // 11 features originais
    const has_img = tag === 'img' || el.querySelector('img') !== null ? 1 : 0;
    const has_alt = (el.hasAttribute('alt') && el.getAttribute('alt').trim().length > 0) ? 1 : 0;
    const has_aria = (el.hasAttribute('aria-label') || el.hasAttribute('aria-describedby') || el.hasAttribute('role')) ? 1 : 0;
    const has_button = tag === 'button' || el.getAttribute('role') === 'button' || el.classList.contains('btn') ? 1 : 0;
    const has_form = tag === 'form' || el.closest('form') !== null ? 1 : 0;
    const has_link = tag === 'a' || el.closest('a') !== null ? 1 : 0;
    const has_table = tag === 'table' || el.closest('table') !== null ? 1 : 0;

    const isHeading = /^h[1-6]$/.test(tag);
    const heading_count = isHeading ? 1 : 0;
    // Detecção heurística de salto de cabeçalho
    const invalid_heading = (isHeading && (tag === 'h4' || tag === 'h5' || tag === 'h6')) ? 1 : 0;
    const text_length = Math.min(innerText.trim().length, 1000);
    const tag_count = el.querySelectorAll('*').length + 1;

    // 11 novas features estruturais
    const has_select = tag === 'select' || el.querySelector('select') !== null ? 1 : 0;
    const has_textarea = tag === 'textarea' || el.querySelector('textarea') !== null ? 1 : 0;
    const has_video = tag === 'video' || el.querySelector('video') !== null ? 1 : 0;
    const has_audio = tag === 'audio' || el.querySelector('audio') !== null ? 1 : 0;
    const has_figure = tag === 'figure' || el.querySelector('figure') !== null ? 1 : 0;
    const has_svg = tag === 'svg' || el.querySelector('svg') !== null ? 1 : 0;
    const has_canvas = tag === 'canvas' || el.querySelector('canvas') !== null ? 1 : 0;

    const select_count = el.querySelectorAll('select').length + (tag === 'select' ? 1 : 0);
    const textarea_count = el.querySelectorAll('textarea').length + (tag === 'textarea' ? 1 : 0);
    const media_count = el.querySelectorAll('video, audio').length + (/^(video|audio)$/.test(tag) ? 1 : 0);
    const svg_canvas_count = el.querySelectorAll('svg, canvas').length + (/^(svg|canvas)$/.test(tag) ? 1 : 0);

    return [
      has_img, has_alt, has_aria, has_button, has_form, has_link, has_table,
      heading_count, invalid_heading, text_length, tag_count,
      has_select, has_textarea, has_video, has_audio, has_figure, has_svg, has_canvas,
      select_count, textarea_count, media_count, svg_canvas_count
    ];
  }

  /**
   * Consulta o Gateway de Inferência assíncrono com tolerância a falhas (timeout)
   */
  async function queryAdaptation(el, features) {
    const rawId = el.id || el.getAttribute('src') || el.outerHTML.slice(0, 100);
    const cacheKey = CONFIG.CACHE_PREFIX + (await computeHash(rawId));

    // 1. Verifica cache local no navegador (0 ms)
    try {
      const cached = CONFIG.STORAGE.getItem(cacheKey);
      if (cached) {
        return JSON.parse(cached);
      }
    } catch (e) {
      // Ignora erro de storage restrito
    }

    // 2. Chamada remota ao Gateway com AbortController (Timeout)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CONFIG.TIMEOUT_MS);

    try {
      const payload = {
        tag: el.tagName.toLowerCase(),
        profile: window.INTERA_USER_PROFILE || CONFIG.PROFILE_DEFAULT,
        features: features,
        html_snippet: el.outerHTML.slice(0, 300),
        context: el.parentElement ? el.parentElement.innerText.slice(0, 150) : ''
      };

      const response = await fetch(CONFIG.API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const decision = await response.json();
        // Grava no cache local
        try {
          CONFIG.STORAGE.setItem(cacheKey, JSON.stringify(decision));
        } catch (e) {}
        return decision;
      }
    } catch (err) {
      // Degradação graciosa em caso de timeout ou rede indisponível
      // console.debug('[INTERA-AI] Degradação graciosa ativada:', err.message);
    } finally {
      clearTimeout(timeoutId);
    }

    // Fallback determinístico local se o backend não estiver acessível
    return localFallbackDecision(el, features);
  }

  /**
   * Regras determinísticas locais para fallback instantâneo sem IA
   */
  function localFallbackDecision(el, features) {
    const tag = el.tagName.toLowerCase();
    if (tag === 'img' && !el.hasAttribute('alt')) {
      const fallbackAlt = el.getAttribute('title') || 'Ilustração didática do conteúdo da aula';
      return { action: 'ADD_ALT', alt_text: fallbackAlt };
    }
    if ((tag === 'div' || tag === 'span') && (el.hasAttribute('onclick') || el.classList.contains('btn'))) {
      const label = el.innerText.trim() || 'Ação interativa';
      return { action: 'ADD_ARIA', role: 'button', label: label };
    }
    return { action: 'NO_ACTION' };
  }

  /**
   * Aplica cirurgicamente a adaptação no DOM em memória
   */
  function applyPatch(el, decision) {
    if (!decision || decision.action === 'NO_ACTION' || decision.action === 'OK') {
      return;
    }

    if (decision.action === 'ADD_ALT' && decision.alt_text) {
      el.setAttribute('alt', decision.alt_text);
      if (!el.hasAttribute('aria-label')) {
        el.setAttribute('aria-label', decision.alt_text);
      }
    } else if (decision.action === 'ADD_ARIA') {
      if (!el.hasAttribute('role')) el.setAttribute('role', decision.role || 'button');
      if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
      if (decision.label && !el.hasAttribute('aria-label')) {
        el.setAttribute('aria-label', decision.label);
      }
      // Habilita ativação por teclado (Enter / Espaço)
      el.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          el.click();
        }
      });
    } else if (decision.action === 'FIX_HEADING') {
      // Ajuste de nível de acessibilidade
      if (!el.hasAttribute('role')) {
        el.setAttribute('role', 'heading');
        el.setAttribute('aria-level', decision.target_level || '2');
      }
    }
  }

  /**
   * Executa a varredura atômica em nós candidatos da página
   */
  async function runAccessibilityScan() {
    // Seletores de elementos prioritários para acessibilidade
    const candidates = document.querySelectorAll(
      'img:not([alt]), div[onclick], span[onclick], div[class*="btn"], span[class*="btn"], h3, h4, h5, h6'
    );

    for (const el of candidates) {
      const features = extract22Features(el);
      const decision = await queryAdaptation(el, features);
      applyPatch(el, decision);
    }
  }

  // =====================================================================
  // Inicialização e Ciclo de Vida
  // =====================================================================
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runAccessibilityScan);
  } else {
    runAccessibilityScan();
  }

  // Observer para páginas dinâmicas (SPA / Telas que mudam no SCORM)
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.addedNodes.length > 0) {
        runAccessibilityScan();
        break;
      }
    }
  });

  observer.observe(document.body || document.documentElement, {
    childList: true,
    subtree: true
  });

  console.log('[INTERA-AI] Runtime Wrapper ativo. Acessibilidade dinâmica e canal SCORM operando.');
})();
