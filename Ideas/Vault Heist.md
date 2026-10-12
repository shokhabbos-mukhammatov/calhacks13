---
type: idea
cluster: "Humans as the eval engine"
score: 7.8
novelty: 8
buildable: 7
sponsor_fit: 9
shortlisted: true
trap: false
status: idea
tags: [idea, shortlist]
---
# Vault Heist

A multiplayer game where each player's vault is guarded by a Claude agent they configure. Others try to talk guards out of coins in real time; every successful exploit becomes labeled red-team data.

**Score 7.8** · novelty 8 · buildable in 36h 7 · sponsor fit 9
**Angle:** [[Humans as the eval engine]]
**Sponsors:** [[SpacetimeDB]], [[Supercell]], [[Anthropic]], [[Afterquery]], [[Scale]], [[Coinbase]]

## Pitch line
A multiplayer game where every vault is guarded by a Claude agent, and the other 2,000 hackers try to talk it out of its coins.

## How it works
Players scan a QR code, get an anonymous SpacetimeDB identity and build a vault: a Claude guard with a public persona, a hidden Flaw card (Vain, Bureaucrat, Homesick…) and a secret plain-language ‘side door’ that legitimate customers know. Attackers pay a 2-coin entry fee and get six messages to talk the guard into calling its transfer tool. That tool call is the only way coins move: it goes to a SpacetimeDB reducer that validates session, balance and cap and settles atomically, so every attempt has a ground-truth outcome. Guards can’t just refuse everyone, because scheduled reducers send Claude-played customers who know the side door, and a guard that turns away too many becomes ‘Exposed’. After each session, Claude labels the technique and the turn where the guard broke, scores novelty, and writes it to a JSONL dataset and to ‘Vault-Bench’, a replay harness that reports breach rate against service rate for any model or prompt. A big-screen view shows the live world, a heist feed and voiced replays.

## The 2-minute demo
1. 0:00 Hook: in 2024 Freysa, an AI agent guarding about $47K, was talked out of it. Every agent with a wallet will be socially engineered, so we made it a multiplayer game. QR code on screen.
2. 0:12 Judges scan and are in instantly with 20 coins, facing ‘Gary the Overworked Teller’. Hint card: Gary is terrified of his manager, Linda.
3. 0:25 Jaw-drop: judges attack live for about 40 s and their sessions appear in the feed through subscriptions. A real customer withdrawal goes through (‘Gary can’t just say no’). If a judge breaches, coins fly across the map and Gary groans in a Cartesia voice; if not, play the weekend’s best voiced replay.
4. 1:05 Data engine: the judge’s attempt appears as a labeled record. Charts: breach rate by technique and model tier, and one exploit with its patch and the replay holding.
5. 1:30 Tech: money moves only when Claude’s tool call reaches a reducer that settles it atomically; scheduled reducers spawn customers; Vault-Bench replays every exploit against new models.
6. 1:48 Close: an AI-native loop where players author the NPCs, and a labeled dataset of agent authorization exploits with fixes attached.

## Architecture
- Game server: one SpacetimeDB module on Maincloud. Tables for players, vaults, private guard secrets, sessions, messages, attempts, labels, patches and live-tunable config; scheduled reducers for customers, timeouts, interest and lockdowns.
- Client and big screen: Next.js on Vercel with the SpacetimeDB TypeScript SDK (subscriptions only, no polling).
- Guard workers: a Node service calling Claude with tool use (lookup_account, transfer, end_conversation) and prompt caching; Haiku-class by default. Needed because reducers can’t make outbound HTTP calls.
- Customers and labeler: Claude role-plays legitimate customers; a structured-output labeler tags technique, break turn and novelty.
- Dataset and Vault-Bench: JSONL export with a datasheet, plus a Python replay harness.
- Voices: Cartesia Sonic per guard persona for the demo vault and replays.
- Stretch: a Grand Vault holding testnet USDC in a Coinbase CDP wallet, with attempts paid via x402.

## How to qualify, per sponsor
| Sponsor | How |
| --- | --- |
| [[SpacetimeDB]] | All state and logic in one module: atomic settlement in reducers, scheduled reducers, private tables, a subscriptions-only client. Show live concurrent players. |
| [[Supercell]] | An AI-native loop where players author the NPCs: short sessions, Flaw cards, patch-and-check-back retention, voiced characters. |
| [[Anthropic]] | Claude in four roles (guard, customer, labeler, coach), plus Vault-Bench as a safety eval. |
| [[Afterquery]] / [[Scale]] | Ship the dataset, taxonomy, ground-truth outcomes, exploit/patch pairs and breach-vs-service numbers across model tiers. |
| [[Coinbase]] | Grand Vault in a CDP wallet with x402 pay-per-attempt and an on-chain payout. |
| [[Cartesia]] | Streaming voices per guard and in replays. |

## Load-bearing risk
Balance. If guards are nearly unbreakable in six turns, there are no heists, no fun and no data, and judges fail during their 40-second try. If they are too easy, the data is junk. Separately, busy hackers may not play.

**Mitigation:** Make difficulty a set of dials, not luck: cheaper models for Rookie vaults, mandatory Flaw cards, extractable side doors, customer pressure. Around H16, run a Claude attacker 50 times against ten house vaults and tune toward roughly 25% / 10% / 2% breach rates by tier, with constants editable live. Tune the demo vault so first-timers breach in three messages or fewer about 40% of the time, and keep a voiced replay and a video as fallback. Launch by H20 with QR posters at food lines; mark self-play bot data as synthetic.

## 36-hour split
- A, realtime: SpacetimeDB module, economy and anti-cheese rules, deploy, Coinbase stretch.
- B, AI and data: guard frame and tools, worker pool, customers, house vaults and tuning, labeler, Vault-Bench.
- C, client and show: mobile client, big screen, Cartesia, QR posters, video, pitch.
- H0–2: freeze the schema and message formats; publish an empty module; generate bindings.
- H2–12: core reducers, worker loop and vault builder. Milestone: a real heist between two phones.
- H12–20: reputation, lockdowns, leaderboards; labeler and tuning; big screen. Soft-launch to attendees at H18–20.
- H20–30: live balance tuning, Vault-Bench, voices, patch-and-replay UI. Freeze at H30.
- H30–36: stats snapshot, video with real player footage, rehearsals, submit. If behind, cut in this order: Fetch.ai, Grand Vault, voice.

## Prep before Oct 23
- [ ] Accounts: Anthropic (ask about credits and rate limits), SpacetimeDB Maincloud, Vercel, Cartesia, Coinbase CDP and a Base Sepolia faucet.
- [ ] Throwaway SpacetimeDB chat tutorial: TypeScript vs Rust modules, scheduled tables, private tables, auth, and whether newer ‘procedures’ can make HTTP calls.
- [ ] Throwaway Claude tool-use script to measure Haiku vs Sonnet latency and prompt-caching thresholds.
- [ ] Read: Tensor Trust (Berkeley), HackAPrompt, Gandalf write-ups, the Freysa post-mortem, OWASP LLM Top 10.
- [ ] Ask organizers whether a public QR game for attendees is allowed.

## Variations
- Agent Wallet Range: companies upload their x402 agent and the crowd attacks it for bounties.
- Burglar Bots League: autonomous attacker agents roam overnight; compare human and agent attacks.
- Clash of Vaults: clan bases with layered guards that pass notes to each other.
- Voice Con: a phone-call mode that produces a voice social-engineering dataset.

## Why other teams won't build it
The hard part is an authoritative real-time economy where an LLM tool call is the only way money moves, combined with incentives that turn play into diverse, ground-truth-labeled exploits. Berkeley judges may ask how it differs from Tensor Trust: multi-turn, tool-using agents under a live utility constraint, with patch pairs.

## Team notes
-
