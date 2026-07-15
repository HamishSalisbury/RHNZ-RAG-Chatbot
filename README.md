# RHNZ RAG Chatbot

A Retrieval-Augmented Generation (RAG) microservice that answers natural-language questions about Rink Hockey New Zealand, covering both live player statistics and the official World Skate rulebook, through a single stateless API endpoint.

<!--
## Link to Live Application 
[Link](LinkHere) --!>

<!-- Built end-to-end as a solo project: ingestion, retrieval, agentic routing, deterministic answer construction, evaluation, and containerised deployment. -->

---

## What It Does

```
"How many red cards does Quinn Fraser have?"
-> "Quinn Fraser has 2 red cards as of 29 June 2026."   (pulled live from the database, states freshness of data)

"and how many games has he played?"
-> Resolves "he" from history, then re-queries the database live.

"How high can players raise their stick?"
-> Answers from the official rulebook, citing the exact rule ID and quoting the source text.
```

A single request can mix stats and rules, contain multiple sub-questions, and chain dependent questions ("Who has the most red cards, and how many games have they played?"), resolved automatically in a bounded two-round tool loop.

---

## Highlights

- **The LLM never generates a factual value.** It emits templates with placeholders; real values are injected deterministically from live retrieval. Hallucination is eliminated by construction, not by prompting.
- **The LLM never writes a query.** It emits a typed, structured intent that is validated against a live schema catalogue before a swappable adapter builds the actual parameterised database call. Model output is treated as a claim to be verified, not an instruction to be executed.
- **Runtime schema discovery.** The service introspects the database schema at runtime and refreshes on cache miss, so tables added minutes ago are answerable without a redeploy.
- **Grounded, cited rules answers.** The rulebook is chunked by rule boundary into a read-only vector index baked into the container image; every rule's answer cites its rule ID and quotes the source chunk.
- **Honest failure modes.** "Not found" is said. Unknown players, missing rules, and unavailable dependencies degrade cleanly rather than producing a guess.
<!-- - **Measured quality.** Targets 95% accuracy over a 200-question evaluation set scored against live ground-truth values, with P95 latency under 5 seconds. -->

Full rationale for each of these decisions is in the Design Document below.

---

## Architecture
<!--
[Insert architecture diagram here: a request arriving at POST /v1/ask, the LLM router (native function calling) contextualising and decomposing the question, the two retrieval paths branching from it (stats: structured intent -> validation against the schema catalogue -> PostgREST adapter -> live read-only query; rules: semantic search over the read-only Chroma index), and both paths converging into the format-only response builder where values are injected deterministically into the final JSON answer.] -->

**Stack:** Python / Django REST Framework, Gemini Flash-Lite (swappable), local sentence-transformer embeddings, Chroma, Supabase PostgreSQL via PostgREST (read-only), Docker.

---

## Project Documentation

| Document | Description | Link |
|----------|-------------|------|
| Design Document | Full system architecture, design decisions and rationale | [View](https://docs.google.com/document/d/1nLufA5eKJQWDMl6mXlbp06IHfQTBe573ItAlfiX0hRk/edit?tab=t.0) |
| Requirements Document | Objectives, scope, functional and non-functional requirements | [View](https://docs.google.com/document/d/1cd-emBGzdRLcQsqyWsjQpgX-uF0lwgd_qcMh_hbCc1Q/edit?tab=t.0) |
| Project Plan | Deliverables, work breakdown, milestones, risk register | [View](https://docs.google.com/document/d/1AVzZTAVaveXA1dcjn3KmIyJ2Sgxh_1_EzvJLu7mgNaQ/edit?tab=t.0) |
<!-- | API Contract (OpenAPI) | Formal request/response specification | [View](INSERT_VIEW_ONLY_LINK_HERE) | -->
<!--| Security and Data-Access Note | Trust boundaries, threat model, access posture | [View](INSERT_VIEW_ONLY_LINK_HERE) | -->
<!--
---

## Running Locally

```bash
cd rhnz-rag-chatbot
cp .env.example .env        # fill in LLM API key, Supabase URL and read-only key

docker build -t rhnz-chatbot .    # ingestion runs during the build and bakes the rules index into the image
docker run -p 8000:8000 --env-file .env rhnz-chatbot

curl http://localhost:8000/health
```

--- -->

## Author

Hamish Salisbury, 2026

<!--
## License

See [LICENSE](LICENSE). INSERT_LICENSE_TYPE_HERE. -- >
