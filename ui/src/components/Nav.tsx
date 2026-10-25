import { useEffect, useState } from "react";
import { SECTIONS } from "../sections";
import { data } from "../data";
import "./Nav.css";

/** Sticky, with the section the reader is in marked, and the live phone line
 * always one tap away: it is the demo a judge can run themselves. */
export default function Nav() {
  const [active, setActive] = useState<string>("");

  useEffect(() => {
    // A thin band across the middle of the viewport: whichever section crosses
    // it is the one being read. Ranking by visible ratio instead loses every
    // tall section to its shorter neighbours.
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) if (e.isIntersecting) setActive(e.target.id);
      },
      { rootMargin: "-45% 0px -50% 0px", threshold: 0 },
    );
    for (const s of SECTIONS) {
      const el = document.getElementById(s.id);
      if (el) io.observe(el);
    }
    return () => io.disconnect();
  }, []);

  return (
    <header className="nav">
      <div className="nav__inner wrap">
        <a className="nav__brand" href="#top" aria-label="Fire Drill, back to top">
          <span className="nav__mark" aria-hidden="true">F</span>
          <span className="sign nav__word">Fire Drill</span>
        </a>
        <nav aria-label="Sections">
          <ol className="nav__links">
            {SECTIONS.map((s) => (
              <li key={s.id}>
                <a href={`#${s.id}`} aria-current={active === s.id ? "true" : undefined}>
                  <span className="nav__no">{s.no}</span>
                  {s.label}
                </a>
              </li>
            ))}
          </ol>
        </nav>
        <a className="nav__live" href={`tel:${data.live.phone_e164}`}>
          <span className="nav__dot" aria-hidden="true" />
          <span className="nav__live-label">Live line</span>
          <span className="num">{data.live.phone}</span>
        </a>
      </div>
    </header>
  );
}
