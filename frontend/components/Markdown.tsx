// Render de markdown MÍNIMO para las respuestas del chat: negrita (**), itálica
// (*) y código (`). No es un parser completo; los saltos de línea y sangrías se
// conservan con `whitespace-pre-wrap` en el contenedor.

import { ReactNode } from "react";

const INLINE = /(\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`)/g;

export function Markdown({ text }: { text: string }) {
  const nodes: ReactNode[] = [];
  let ultimo = 0;
  let clave = 0;
  let m: RegExpExecArray | null;

  INLINE.lastIndex = 0;
  while ((m = INLINE.exec(text)) !== null) {
    if (m.index > ultimo) nodes.push(text.slice(ultimo, m.index));
    if (m[2] !== undefined) {
      nodes.push(<strong key={clave++}>{m[2]}</strong>);
    } else if (m[3] !== undefined) {
      nodes.push(<em key={clave++}>{m[3]}</em>);
    } else if (m[4] !== undefined) {
      nodes.push(
        <code key={clave++} className="rounded bg-slate-100 px-1 py-0.5 text-[0.85em]">
          {m[4]}
        </code>,
      );
    }
    ultimo = m.index + m[0].length;
  }
  if (ultimo < text.length) nodes.push(text.slice(ultimo));

  return <>{nodes}</>;
}
