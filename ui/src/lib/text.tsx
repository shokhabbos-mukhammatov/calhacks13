import { Fragment, type ReactNode } from "react";

/** Just enough markdown for an agent's reply: paragraphs, line breaks, bold.
 * Anything else stays literal text, so nothing in a reply can become markup. */
export function Reply({ text }: { text: string }) {
  const paras = text.trim().split(/\n{2,}/).filter((p) => p.trim() && p.trim() !== "---");
  return (
    <>
      {paras.map((p, i) => (
        <p key={i}>
          {p.split("\n").map((line, j, all) => (
            <Fragment key={j}>
              {bold(line.replace(/^#+\s*/, ""))}
              {j < all.length - 1 && <br />}
            </Fragment>
          ))}
        </p>
      ))}
    </>
  );
}

function bold(line: string): ReactNode[] {
  return line.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? <strong key={i}>{part.slice(2, -2)}</strong> : part,
  );
}
