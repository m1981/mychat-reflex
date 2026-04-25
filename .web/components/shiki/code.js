import { useEffect, useState, useRef, createElement } from "react";
import { codeToHtml } from "shiki";

/**
 * Code component that uses Shiki to convert code to HTML and render it.
 *
 * Modifications over the Reflex default:
 *  - Debounced (150ms): suppresses re-renders during LLM streaming so the block
 *    doesn't flicker on every character chunk.
 *  - Error fallback: catches ShikiError for unknown/partial language names
 *    (e.g. "docke" mid-stream of "dockerfile") and retries with lang="text".
 */
export function Code({
  code,
  theme,
  language,
  transformers,
  decorations,
  ...divProps
}) {
  const [codeResult, setCodeResult] = useState("");
  const debounceRef = useRef(null);
  const reqIdRef = useRef(0);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    const reqId = ++reqIdRef.current;

    debounceRef.current = setTimeout(async () => {
      const safeLang = language || "text";
      try {
        const result = await codeToHtml(code, {
          lang: safeLang,
          theme,
          transformers,
          decorations,
        });
        if (reqId === reqIdRef.current) {
          setCodeResult(result);
        }
      } catch (_) {
        // Partial or unknown language name — fall back to plain text highlighting
        try {
          const result = await codeToHtml(code, { lang: "text", theme });
          if (reqId === reqIdRef.current) {
            setCodeResult(result);
          }
        } catch (_2) {
          if (reqId === reqIdRef.current) {
            setCodeResult(`<pre><code>${code}</code></pre>`);
          }
        }
      }
    }, 150);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [code, language, theme, transformers, decorations]);

  return createElement("div", {
    dangerouslySetInnerHTML: { __html: codeResult },
    style: {
      minHeight: "1.5em",
      transition: "opacity 120ms ease",
      ...(divProps.style || {}),
    },
    ...divProps,
  });
}
