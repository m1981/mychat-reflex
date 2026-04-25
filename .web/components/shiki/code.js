import { useEffect, useRef, useState, createElement } from "react";
import { codeToHtml } from "shiki";

const SHIKI_TRACE = true;
const HIGHLIGHT_CACHE_LIMIT = 200;
const highlightCache = new Map();
const DEFAULT_LIGHT_THEME = "github-light";
const DEFAULT_DARK_THEME = "nord";

const now = () => (typeof performance !== "undefined" ? performance.now() : Date.now());

function resolveDynamicTheme(theme, themes) {
  if (themes?.mode !== "dynamic-local-storage") {
    return theme;
  }

  if (typeof window === "undefined") {
    return themes?.dark_default || DEFAULT_DARK_THEME;
  }

  const root = window.document?.documentElement;
  const resolvedColorMode = root?.classList?.contains("light")
    ? "light"
    : root?.classList?.contains("dark")
      ? "dark"
      : (window.localStorage.getItem("theme") || "system") === "light"
        ? "light"
        : "dark";

  return resolvedColorMode === "light"
    ? window.localStorage.getItem(themes?.light_storage_key || "light_code_theme_v2") ||
        themes?.light_default ||
        DEFAULT_LIGHT_THEME
    : window.localStorage.getItem(themes?.dark_storage_key || "code_theme_v2") ||
        themes?.dark_default ||
        DEFAULT_DARK_THEME;
}

if (typeof window !== "undefined") {
  window.__SHIKI_TRACE_LOGS__ = window.__SHIKI_TRACE_LOGS__ || [];
  window.__dumpShikiTrace = window.__dumpShikiTrace || (() => {
    const logs = window.__SHIKI_TRACE_LOGS__ || [];
    const blob = new Blob([JSON.stringify(logs, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `shiki-trace-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    return logs.length;
  });
}

function mkBlockId(code) {
  const s = String(code || "");
  return `len:${s.length}|head:${s.slice(0, 24).replace(/\n/g, "\\n")}`;
}

function stableStringify(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) {
    return `[${value.map((v) => stableStringify(v)).join(",")}]`;
  }
  const keys = Object.keys(value).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${stableStringify(value[k])}`).join(",")}}`;
}

function getRenderSignature({ code, theme, language, transformers, decorations }) {
  return [
    `t:${theme || ""}`,
    `l:${language || "text"}`,
    `c:${String(code || "")}`,
    `tr:${stableStringify(transformers ?? null)}`,
    `de:${stableStringify(decorations ?? null)}`,
  ].join("|");
}

function cacheGet(signature) {
  if (!highlightCache.has(signature)) return null;
  const value = highlightCache.get(signature);
  // LRU touch
  highlightCache.delete(signature);
  highlightCache.set(signature, value);
  return value;
}

function cacheSet(signature, html) {
  if (highlightCache.has(signature)) {
    highlightCache.delete(signature);
  }
  highlightCache.set(signature, html);
  if (highlightCache.size > HIGHLIGHT_CACHE_LIMIT) {
    const oldestKey = highlightCache.keys().next().value;
    highlightCache.delete(oldestKey);
  }
}

export function Code({
  code,
  theme,
  themes,
  language,
  transformers,
  decorations,
  ...divProps
}) {
  const [frontHtml, setFrontHtml] = useState("");
  const [backHtml, setBackHtml] = useState("");
  const [showBack, setShowBack] = useState(false);
  const [lockHeight, setLockHeight] = useState(null);
  const [frontSignature, setFrontSignature] = useState("");
  const resolvedTheme = resolveDynamicTheme(theme, themes);

  const rootRef = useRef(null);
  const debounceRef = useRef(null);
  const reqIdRef = useRef(0);
  const swapTimerRef = useRef(null);
  const mountedRef = useRef(true);
  const activeSignatureRef = useRef("");
  const instanceRef = useRef(
    `codeblk-${Math.random().toString(36).slice(2, 8)}`
  );

  const trace = (event, payload = {}) => {
    if (!SHIKI_TRACE) return;
    const entry = {
      ts: new Date().toISOString(),
      t: Math.round(now()),
      instance: instanceRef.current,
      event,
      payload,
    };
    if (typeof window !== "undefined") {
      window.__SHIKI_TRACE_LOGS__ = window.__SHIKI_TRACE_LOGS__ || [];
      window.__SHIKI_TRACE_LOGS__.push(entry);
      if (window.__SHIKI_TRACE_LOGS__.length > 5000) {
        window.__SHIKI_TRACE_LOGS__.shift();
      }
    }
    // eslint-disable-next-line no-console
    console.log(`[ShikiTrace][${instanceRef.current}] ${event}`, payload);
  };

  const renderHtml = async (
    srcCode,
    srcTheme,
    srcLang,
    srcTransformers,
    srcDecorations,
    reqId
  ) => {
    const safeLang = srcLang || "text";
    const signature = getRenderSignature({
      code: srcCode,
      theme: srcTheme,
      language: safeLang,
      transformers: srcTransformers,
      decorations: srcDecorations,
    });

    const cached = cacheGet(signature);
    if (cached != null) {
      trace("render:cache_hit", {
        reqId,
        signatureLen: signature.length,
        htmlLen: cached?.length ?? 0,
      });
      return { html: cached, signature };
    }

    const t0 = now();
    trace("render:start", {
      reqId,
      theme: srcTheme,
      language: srcLang,
      safeLang,
      codeId: mkBlockId(srcCode),
      signatureLen: signature.length,
    });

    try {
      const html = await codeToHtml(srcCode, {
        lang: safeLang,
        theme: srcTheme,
        transformers: srcTransformers,
        decorations: srcDecorations,
      });
      cacheSet(signature, html);
      trace("render:ok", {
        reqId,
        ms: Math.round(now() - t0),
        htmlLen: html?.length ?? 0,
      });
      return { html, signature };
    } catch (e1) {
      trace("render:primary_failed", {
        reqId,
        ms: Math.round(now() - t0),
        err: String(e1?.message || e1),
      });
      try {
        const html = await codeToHtml(srcCode, { lang: "text", theme: srcTheme });
        cacheSet(signature, html);
        trace("render:fallback_text_ok", {
          reqId,
          ms: Math.round(now() - t0),
          htmlLen: html?.length ?? 0,
        });
        return { html, signature };
      } catch (e2) {
        trace("render:fallback_text_failed", {
          reqId,
          ms: Math.round(now() - t0),
          err: String(e2?.message || e2),
        });
        const html = `<pre><code>${srcCode}</code></pre>`;
        cacheSet(signature, html);
        return { html, signature };
      }
    }
  };

  useEffect(() => {
    mountedRef.current = true;
    trace("mount", {
      theme,
      resolvedTheme,
      language,
      codeId: mkBlockId(code),
    });
    return () => {
      mountedRef.current = false;
      trace("unmount");
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // First paint
  useEffect(() => {
    if (frontHtml) return;
    const reqId = ++reqIdRef.current;
    trace("first_paint:begin", { reqId });

    let alive = true;
    (async () => {
      const { html, signature } = await renderHtml(
        code,
        resolvedTheme,
        language,
        transformers,
        decorations,
        reqId
      );
      if (!alive || !mountedRef.current) {
        trace("first_paint:drop_not_alive", { reqId });
        return;
      }
      if (reqId !== reqIdRef.current) {
        trace("first_paint:drop_stale", { reqId, currentReqId: reqIdRef.current });
        return;
      }
      activeSignatureRef.current = signature;
      setFrontSignature(signature);
      setFrontHtml(html);
      trace("first_paint:set_front", { reqId, htmlLen: html?.length ?? 0 });
    })();

    return () => {
      alive = false;
      trace("first_paint:cleanup", { reqId });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Subsequent updates
  useEffect(() => {
    if (!frontHtml) return;

    const nextSignature = getRenderSignature({
      code,
      theme: resolvedTheme,
      language: language || "text",
      transformers,
      decorations,
    });

    if (nextSignature === activeSignatureRef.current || nextSignature === frontSignature) {
      trace("update:skip_same_signature", {
        signatureLen: nextSignature.length,
      });
      return;
    }

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
      trace("update:clear_debounce");
    }
    if (swapTimerRef.current) {
      clearTimeout(swapTimerRef.current);
      trace("update:clear_swap_timer");
    }

    const reqId = ++reqIdRef.current;
    trace("update:schedule", {
      reqId,
      theme,
      resolvedTheme,
      language,
      codeId: mkBlockId(code),
      showBack,
      frontLen: frontHtml?.length ?? 0,
      backLen: backHtml?.length ?? 0,
    });

    debounceRef.current = setTimeout(async () => {
      const el = rootRef.current;
      if (el) {
        const h = el.getBoundingClientRect().height;
        if (h > 0) {
          setLockHeight(h);
          trace("update:lock_height", { reqId, h: Math.round(h) });
        } else {
          trace("update:lock_height_skip_zero", { reqId, h });
        }
      } else {
        trace("update:no_root_for_height", { reqId });
      }

      const { html, signature } = await renderHtml(
        code,
        resolvedTheme,
        language,
        transformers,
        decorations,
        reqId
      );

      if (!mountedRef.current) {
        trace("update:drop_unmounted", { reqId });
        return;
      }
      if (reqId !== reqIdRef.current) {
        trace("update:drop_stale_after_render", {
          reqId,
          currentReqId: reqIdRef.current,
        });
        return;
      }

      setBackHtml(html);
      setShowBack(true);
      trace("update:crossfade_start", {
        reqId,
        htmlLen: html?.length ?? 0,
      });

      swapTimerRef.current = setTimeout(() => {
        if (!mountedRef.current) {
          trace("update:swap_drop_unmounted", { reqId });
          return;
        }
        if (reqId !== reqIdRef.current) {
          trace("update:swap_drop_stale", {
            reqId,
            currentReqId: reqIdRef.current,
          });
          return;
        }

        activeSignatureRef.current = signature;
        setFrontSignature(signature);
        setFrontHtml(html);
        setBackHtml("");
        setShowBack(false);
        setLockHeight(null);

        trace("update:crossfade_commit", {
          reqId,
          frontLen: html?.length ?? 0,
        });
      }, 120);
    }, 120);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
        trace("update:cleanup_clear_debounce", { reqId });
      }
      if (swapTimerRef.current) {
        clearTimeout(swapTimerRef.current);
        trace("update:cleanup_clear_swap", { reqId });
      }
    };
  }, [code, resolvedTheme, language, transformers, decorations, frontHtml, frontSignature]);

  return createElement(
    "div",
    {
      ref: rootRef,
      style: {
        position: "relative",
        minHeight: "1.5em",
        ...(lockHeight != null ? { height: `${lockHeight}px`, overflow: "hidden" } : {}),
        ...(divProps.style || {}),
      },
      ...divProps,
    },
    createElement("div", {
      style: {
        position: "relative",
        opacity: showBack ? 0 : 1,
        transition: "opacity 120ms ease",
      },
      dangerouslySetInnerHTML: { __html: frontHtml },
    }),
    backHtml
      ? createElement("div", {
          style: {
            position: "absolute",
            inset: 0,
            opacity: showBack ? 1 : 0,
            transition: "opacity 120ms ease",
          },
          dangerouslySetInnerHTML: { __html: backHtml },
        })
      : null
  );
}
