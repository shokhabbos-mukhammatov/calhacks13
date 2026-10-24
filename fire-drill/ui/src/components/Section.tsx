import type { ReactNode } from "react";

interface Props {
  id: string;
  no: string;
  title: string;
  lede?: ReactNode;
  dark?: boolean;
  children: ReactNode;
}

/** A numbered plate, a sign, a lede, then the section's own content. */
export default function Section({ id, no, title, lede, dark, children }: Props) {
  return (
    <section id={id} className={`section${dark ? " section--dark" : ""}`} aria-labelledby={`${id}-title`}>
      <div className="wrap">
        <div className="plate">
          <span className="plate__no" aria-hidden="true">{no}</span>
          <h2 id={`${id}-title`} className="plate__title sign">{title}</h2>
        </div>
        {lede && <p className="lede">{lede}</p>}
        {children}
      </div>
    </section>
  );
}
