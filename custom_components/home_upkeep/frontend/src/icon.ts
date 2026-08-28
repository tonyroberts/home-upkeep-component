import { svg, type SVGTemplateResult } from "lit";

/** Render an `@mdi/js` icon path as an inline SVG (fills with `currentColor`). */
export function icon(path: string, size = 20): SVGTemplateResult {
  return svg`<svg viewBox="0 0 24 24" width=${size} height=${size} style="fill: currentColor; flex-shrink: 0;"><path d=${path}></path></svg>`;
}
