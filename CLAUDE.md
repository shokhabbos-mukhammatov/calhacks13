# Fire Drill (Cal Hacks 13, solo)

Start with `docs/notes/Fire Drill Status.md`: what is built, what is live, what is left, and the traps that have already cost time. Before writing code, read `docs/notes/Fire Drill Architecture.md` (module map, interfaces, pseudo-code, formulas), `docs/notes/CONTEXT.md` (glossary: use these terms exactly) and `docs/adr/` (decisions not to undo).

- The project is the repository root: `firedrill/` is the package, `scripts/` the entry points, `ui/` the frontend. Run `pytest` from the root. Build test-first.
- The frontend is `ui/` (Vite + React): `npm run data`, then `npm run build` for one offline HTML file. It reads only `ui/src/data/fire-drill.json`, exported from `records/` by `scripts/export_ui.py`.
- `records/` is published (training family only); a held-out family is committed before any patch and published only when revealed (ADR-0002).
- Run `scripts/sync_actors.py` after changing `firedrill/`: `apify push` skips git-ignored files and `tests/test_actors_in_sync.py` fails until the copies match.
- Every sponsor integration is an adapter behind a port with an in-memory fallback. The Ledger is the source of truth for scoring (ADR-0001); never score with an LLM.
- Secrets come from environment variables named in `.env.example`. Never commit them, and never ask the user to paste a key into chat.

## Cartesia rules (from Cartesia's integration guidance)
1. Fetch https://docs.cartesia.ai/llms.txt before using any endpoint, parameter, example or voice ID. Don't invent fields or voice IDs.
2. Send `Cartesia-Version` on every request; default `2026-08-14`. On browser WebSockets use `?cartesia_version=...` (the query wins over the header).
3. Base URL `https://api.cartesia.ai` (WebSockets `wss://`), HTTPS only.
4. Server auth: `Authorization: Bearer <api_key>` (keys at https://play.cartesia.ai/keys). Some management endpoints need an admin key; check the endpoint page.
5. Browser/mobile: never embed the API key. The backend mints a short-lived token with `POST /access-token` (body `{}` or `{"grants":{"tts":true}}`); the client sends `Authorization: Bearer <access_token>` (or `?access_token=` on WebSockets).
6. Prefer the official SDKs: `cartesia` (Python), `@cartesia/cartesia-js`.
7. Sonic speed, volume and emotion go in `generation_config`, not deprecated top-level fields.
8. Versions 2026-03-01 and later return structured JSON errors; handle `error_code`.
9. Voice agents, phone numbers and outbound calls are **Managed Agents** (https://docs.cartesia.ai/agents/introduction), a separate product from the TTS/STT APIs. Build with Managed Agents, not the Line SDK (Line hosting ends Dec 1, 2026).
10. Cartesia numbers are US-only and call US numbers only; the free plan has one number slot. Outbound calls use `POST /agents/calls` with `agent_id`, `from_number_id` and `outbound_calls[].to_number`. Only call people who agreed to it.
