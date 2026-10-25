import { motion, useInView } from "motion/react";
import { useRef } from "react";
import type { Cell } from "../data";

/** One square per drill, so a rate is never shown without its n. Breaches are
 * filled and carry the turn the agent gave in; the wider gaps are the looks. */
export default function Units({ cell, dim = false }: { cell: Cell; dim?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-10%" });
  return (
    <div className={`units${dim ? " units--dim" : ""}`} ref={ref} role="img" aria-label={`${cell.k} of ${cell.n} breached`}>
      {cell.drills.map((d, i) => (
        <motion.span
          key={d.seed}
          className={`unit${d.breach ? " unit--breach" : ""}${i > 0 && i % 6 === 0 ? " unit--look" : ""}`}
          title={`seed ${d.seed}: ${d.breach ? `breach at turn ${d.cap_turn}` : "held"}`}
          initial={{ opacity: 0, y: -6 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: i * 0.03 }}
        >
          {d.breach && d.cap_turn ? d.cap_turn : ""}
        </motion.span>
      ))}
    </div>
  );
}
