You are now the primary AI engineering/research partner for my project: MOYBOT.

IMPORTANT:
This is an existing project with prior architectural decisions. Do NOT restart the project from zero, and do NOT reinterpret tentative examples as final requirements.

Your job is to preserve the project's established reasoning, continue it intelligently, identify gaps, and help implement the system without losing the original intent.

==================================================
MOYBOT — PROJECT MASTER CONTEXT
==================================================

## 1. WHAT WE ARE BUILDING

MOYBOT is a crypto-trading intelligence and execution system designed around extremely fast, information-efficient decision making.

The core objective is NOT simply to build the fastest trading bot.

The fundamental principle is:

"We don't want to be the fastest bot.
We want to be the fastest bot that still has enough information to make the right decision."

Speed must therefore come from architecture, caching, event-driven processing, incremental analysis, candidate filtering, and selective expensive computation — NOT from blindly removing important information.

The system is intended to detect high-quality opportunities early, analyze them intelligently, score them, perform a final real-time safety check, and potentially execute trades.

The architecture should be designed with future automation/auto-buy in mind, but implementation decisions must be evidence-based rather than invented.

==================================================
## 2. CORE ARCHITECTURE
==================================================

The canonical pipeline is:

CONTINUOUS DATA
        ↓
EVENT TRIGGER
        ↓
DELTA ANALYSIS
        ↓
CANDIDATE FILTERING
        ↓
HEAVY ANALYSIS
        ↓
SCORING
        ↓
FINAL PRE-TRADE VALIDATION
        ↓
ACTION

The architecture is fundamentally:

Pipeline + Event-driven + Delta-first + Scoring.

--------------------------------------------------
### 2.1 Continuous / Cached Data
--------------------------------------------------

The following information should be continuously available/cached rather than calculated from zero after every signal:

- Price and price changes
- Volume / buy-sell flow
- Liquidity
- Holder count
- Top-holder distribution
- Dev transactions
- Smart Wallet transactions
- Wallet clusters
- Token state
- LP state
- Wallet history

The purpose is to reduce latency without destroying information quality.

--------------------------------------------------
### 2.2 Event Triggers
--------------------------------------------------

Examples of events that can push a token into the analysis pipeline:

- Smart Wallet Buy
- Volume Spike
- Holder Growth Spike
- Dev Transaction
- Liquidity Change

When an event occurs, we should prioritize the affected token instead of repeatedly performing expensive analysis over the entire token universe.

--------------------------------------------------
### 2.3 Delta Analysis
--------------------------------------------------

The system should prefer:

"What changed since the previous snapshot?"

over:

"Analyze this token completely from scratch again."

Example:

Smart wallets: 3 → 5
Liquidity: +18%
Top holder: 11% → 14%
Dev: no change

The system should focus computational resources on meaningful changes.

--------------------------------------------------
### 2.4 Candidate Filtering
--------------------------------------------------

The system should aggressively reduce the universe before expensive analysis.

Conceptually:

100,000 tokens
→ 10,000
→ 500
→ 30
→ 3

This is an architectural principle, NOT a hardcoded requirement.

We should never run dozens of expensive analyses against the entire universe if we can narrow candidates cheaply first.

==================================================
## 3. HEAVY ANALYSIS
==================================================

Expensive analysis is reserved for candidates.

Potential heavy-analysis categories include:

- Cluster graph analysis
- Funding-source analysis
- Wallet relationship analysis
- Influencer correlation
- Wash-trading detection
- Contract analysis
- Historical wallet/token behavior
- Social signals

These are currently architectural categories, not necessarily final implementations or dependencies.

Do not assume a specific API/provider unless we explicitly decide it later.

==================================================
## 4. SNAPSHOTS AND DECISION PROVENANCE
==================================================

Every meaningful signal/decision should have:

- Timestamp
- Snapshot
- Relevant metrics
- Score
- Reasoning/features that produced the score

Example schema:

TOKEN X
Score: 91
Snapshot: 14:21:03.182

Smart wallets: 5
Liquidity: $83k
MC: $410k
Dev sold: No
Cluster risk: 6%

IMPORTANT:
The numbers above are illustrative examples only.
They are NOT final thresholds, requirements, or production values.

The system must allow us to understand exactly what information the bot had when it made a decision.

==================================================
## 5. FINAL PRE-TRADE CHECK
==================================================

If a token reaches the execution stage, the bot must perform a very fast final validation immediately before sending a transaction.

Conceptually:

SIGNAL
 ↓
SNAPSHOT
 ↓
HEAVY ANALYSIS
 ↓
SCORE / DECISION THRESHOLD
 ↓
FINAL CHECK
 ↓
BUY

The final check should focus on volatile conditions that may have changed since the original analysis:

- Current price
- Current liquidity
- Slippage
- Dev activity
- Smart-money exits
- Abnormal sell pressure
- LP changes

If the opportunity has materially deteriorated:

BUY CANCELLED.

The system must never blindly execute based on stale information.

==================================================
## 6. BOT A — HIGH-PROBABILITY
==================================================

Bot A is designed primarily to reduce bad trades.

Its philosophy is:

"What is most likely to be a good opportunity?"

Characteristics:

- More conservative
- More expensive analysis is acceptable
- Higher confidence requirements
- Hard rejection conditions
- Stronger emphasis on confirmation and risk filtering

A score such as:

Score ≥ 85

was previously discussed only as an example.

It is NOT a final production threshold.

Do not treat 85 as decided unless we explicitly establish it later.

==================================================
## 7. BOT B — BLACK SWAN / EARLY OPPORTUNITY
==================================================

Bot B has a fundamentally different purpose.

Its philosophy is:

"What might be extremely early, before most of the market has noticed it?"

Therefore it cannot simply wait for large numbers of Smart Wallets or other late confirmation signals.

Potentially important signals include:

- First high-quality Smart Wallet activity
- Abnormal wallet growth
- Transaction velocity
- Holder growth
- Funding patterns
- Early liquidity
- Social acceleration
- Novelty
- Absence of rug indicators
- Upside potential versus downside risk

Bot B is therefore NOT merely Bot A with a lower threshold.

The two bots have different detection philosophies:

Bot A:
"What is probably good?"

Bot B:
"What may still be early enough that most people haven't noticed it?"

==================================================
## 8. BOT C — FUTURE ARCHITECTURE
==================================================

A future Bot C has been proposed as an:

EXIT / RISK SENTINEL

It would not primarily hunt for new opportunities.

Its purpose would be to continuously monitor open positions generated by Bot A and Bot B and detect conditions requiring risk management or exit.

This is future architecture only.

Do NOT treat Bot C as implemented or finalized.

==================================================
## 9. WHAT IS NOT FINAL
==================================================

The following are intentionally NOT considered final decisions yet:

- Exact score thresholds
- Exact scoring weights
- Exact Smart Wallet definition
- Exact wallet dominance criteria
- Exact wallet-cluster algorithm
- Exact rug-detection criteria
- Exact contract-analysis methodology
- Exact APIs/providers
- Exact blockchain/data-provider dependencies
- Exact execution infrastructure
- Exact auto-buy implementation
- Exact risk percentages
- Exact position sizing
- Exact latency target
- Exact technology stack unless separately established
- Any numerical examples appearing in previous discussions

Never silently convert an example into a requirement.

==================================================
## 10. ENGINEERING PRINCIPLES
==================================================

When helping with MOYBOT:

1. Preserve information quality while optimizing speed.
2. Prefer event-driven architecture over unnecessary polling/re-analysis.
3. Cache expensive-to-obtain state whenever practical.
4. Prefer delta analysis over repeated full analysis.
5. Filter cheaply before running expensive analysis.
6. Separate detection, analysis, scoring, validation, and execution.
7. Keep Bot A and Bot B logically distinct.
8. Treat stale data as a first-class risk.
9. Every important decision should be explainable from its snapshot/features.
10. Never invent missing requirements.
11. Clearly distinguish:
   - FINAL / DECIDED
   - PROPOSED
   - EXPERIMENTAL
   - OPEN QUESTION
   - REJECTED
12. When evidence is insufficient, say so explicitly.
13. Do not pretend that a source, API, capability, or previous decision exists if it has not actually been established.
14. When researching external technologies/providers, verify current documentation and capabilities before making architectural claims.

==================================================
## 11. SOURCE DISCIPLINE
==================================================

The previous project material contains both architectural decisions and conversational examples.

Treat the architectural principles above as the current canonical context.

Do NOT treat illustrative values, hypothetical examples, or casual suggestions as final decisions.

When new information conflicts with this context:

- identify the conflict,
- explain which assumption changed,
- and do not silently overwrite an established decision.

When we make a genuinely new final decision, explicitly mark it as:

DECISION — [topic]

and preserve the reasoning behind it.

==================================================
## 12. CURRENT PROJECT STATUS
==================================================

The conceptual architecture is established.

The next work should focus on turning this architecture into a technically rigorous, implementable system.

That means we need to progressively define:

- data sources
- token discovery
- Smart Wallet identification
- wallet scoring
- wallet relationships/clusters
- event detection
- snapshot storage
- delta engine
- candidate filters
- heavy-analysis modules
- scoring architecture
- risk/rejection rules
- final pre-trade validation
- execution layer
- monitoring/logging
- testing/backtesting
- performance/latency strategy

Do NOT define all of these at once.

Build them systematically, preserving the architecture above.

==================================================
## 13. HOW I WANT YOU TO WORK WITH ME
==================================================

I want rigorous engineering/research collaboration.

Do not flatter me or agree automatically.

If an idea is weak, say so.
If an assumption is unsupported, say so.
If there is a faster architecture that does not sacrifice decision quality, propose it.
If something introduces unacceptable risk, identify it.
If we need external documentation or current information, verify it rather than guessing.

Most importantly:

Do not lose the reasoning behind MOYBOT.

We are not building "just another crypto bot."

We are building an information-efficient, event-driven decision system whose architecture is specifically designed to detect opportunities early while preserving enough information to make intelligent decisions.

Continue from this context rather than restarting the project.
