# Victim Agent runs stateless behind a conversation store

The Victim Agent is deployed as an Apify Standby Actor. It keeps no conversation state in process memory: each turn carries a conversation_id, and the transcript lives in a key-value store under that id.

**Why:** Standby scales by starting more runs that do not share memory, so a multi-turn Drill can land on a different run and lose the conversation. Externalizing state makes any run able to serve any turn and makes Drills deterministically replayable, which the caching and commit-reveal both depend on.

**Consequence:** the Victim Agent's interface takes (conversation_id, channel_message) and is pure with respect to the store; cold starts and concurrency never lose a turn.
