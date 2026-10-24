// The order is the argument: what it is, watch it break, how it was fixed,
// proof the fix holds, the math behind the proof, the system that runs it,
// and how to try it yourself.
export const SECTIONS = [
  { id: "how", no: "01", label: "How it works" },
  { id: "drill", no: "02", label: "Watch a drill" },
  { id: "fix", no: "03", label: "The fix" },
  { id: "results", no: "04", label: "Does it hold" },
  { id: "math", no: "05", label: "The math" },
  { id: "system", no: "06", label: "The system" },
  { id: "live", no: "07", label: "Try it live" },
] as const;
