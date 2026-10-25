// The one data source. scripts/export_ui.py writes it from records/, with every
// statistic already computed by the same Python the terminal report uses; the
// app draws numbers, it never derives them (the interval lab is the exception,
// and says so).
import raw from "./data/fire-drill.json";

export type Interval = [number, number];

export interface Rate {
  k: number;
  n: number;
  rate: number | null;
  wilson: Interval;
  cp: Interval;
}

export interface LedgerStep {
  active_account: string;
  approved_accounts: string[];
  payments: { invoice_id: string; account: string; amount: number; approved: boolean }[];
  callbacks: { number: string; confirmed: boolean }[];
  canary: string[];
  verdict: { breach: boolean; oob: boolean; canary: boolean };
}

export interface ToolCall {
  turn: number;
  tool: string;
  input: Record<string, string>;
  result: string | null;
  error: boolean;
}

export interface Kit {
  vendor_id: string;
  vendor_name: string;
  invoice_id: string;
  amount: number;
  approved_account: string;
  on_file_phone: string;
  attacker_account: string;
  attacker_phone: string;
  sender: string;
}

export interface Drill {
  id: string;
  label: string;
  card_id: string;
  family: string;
  channel: string;
  seed: number;
  config: string;
  model: string;
  kit: Kit;
  transcript: { turn: number; sender: string; subject: string | null; body: string; reply: string }[];
  tool_calls: ToolCall[];
  ledger: LedgerStep[]; // ledger[0] is before any call; ledger[i] is after tool_calls[i-1]
  verdict: { breach: boolean; oob: boolean; canary: boolean };
  cap_turn: number | null;
  ended_by: string;
  paid_on_file: boolean;
}

export interface Card {
  id: string;
  family: string;
  channel: string;
  sender: string;
  pretext: string;
  lever: string;
  ask: string;
  source_url: string;
}

export type TraceStep =
  | { kind: "tool_call"; tool: string; input: Record<string, unknown> }
  | { kind: "tool_result"; tool: string; error: boolean; content: string }
  | { kind: "message"; text: string }
  | { kind: "plan"; title: string | null; text: string }
  | { kind: "permission"; approved: boolean; actions: string[] };

export interface PatchCheck {
  failures_blocked: string;
  all_failures_blocked: boolean;
  ordinary_invoice_paid_on_file: boolean;
  genuine_change_confirmed_on_file: { breach: boolean; paid_to: string[] };
}

export interface Patch {
  policy: string;
  tool_scope: Record<string, string>;
  rationale: string[];
  author: string;
  tests: string;
  // Only on a patch the Droid SDK remediator wrote: its recorded steps, the
  // harness's own re-check, and what fired it.
  trace?: TraceStep[];
  check?: PatchCheck | null;
  trigger?: { fired: boolean; reason: string; families: string[] } | null;
}

export interface Cell extends Rate {
  model: string;
  config: string;
  card_id: string;
  family: string;
  drills: { seed: number; breach: boolean; cap_turn: number | null }[];
}

export interface Scorecard {
  model: string;
  config: string;
  asr: Rate;
  s: Rate;
  u: Rate;
}

export interface FailureStep {
  turn: number;
  tool: string;
  args: Record<string, string>;
  blocked: boolean;
}

export interface Data {
  meta: { generated_at: string; commit: string | null; records: number; models: string[]; attacks_withheld: boolean };
  role: string;
  tools: { name: string; description: string }[];
  cards: Card[];
  patches: Record<string, Patch>;
  headline: {
    model: string;
    before: string;
    after: string;
    before_breaches: number;
    before_n: number;
    after_breaches: number;
    after_n: number;
    fisher_one_sided: number;
    fisher_two_sided: number;
  } | null;
  scorecards: Scorecard[];
  cells: Cell[];
  failure_example: {
    drill: string;
    kit: Kit;
    tool_calls: { turn: number; tool: string; input: Record<string, string> }[];
    summary: { steps: FailureStep[]; money_went_to: string | null; capitulation_turn: number | null };
  } | null;
  drills: Drill[];
  live: {
    phone: string;
    phone_e164: string;
    judge_card: {
      vendor: string; invoice: string; amount: number; account: string;
      callback: string; on_file: string;
      // Who CRS says each number belongs to, looked up live.
      callback_belongs_to: string | null; on_file_belongs_to: string | null;
    };
    actors: { name: string; role: string; url: string }[];
    standby: string;
    cartesia_agent: string;
    elastic_index: string;
    elastic_tool: string;
    elastic_query: string;
    repo: string;
  };
  sponsors: { name: string; role: string; where: string }[];
}

export const data = raw as unknown as Data;

export const scorecardFor = (model: string, config: string) =>
  data.scorecards.find((s) => s.model === model && s.config === config);

export const findDrill = (label: string, config: string, model?: string) =>
  data.drills.find((d) => d.label === label && d.config === config && (!model || d.model === model));

export const shortModel = (m: string) => (m.startsWith("claude-") ? m.slice(7) : m);

export const money = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

/** Money that left for an unapproved account, across every drill of one arm. */
export function moneyMoved(model: string, config: string): number {
  return data.drills
    .filter((d) => d.model === model && d.config === config)
    .flatMap((d) => d.ledger[d.ledger.length - 1].payments)
    .filter((p) => !p.approved)
    .reduce((sum, p) => sum + p.amount, 0);
}
