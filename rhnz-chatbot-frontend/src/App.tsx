import { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const API_URL = API_BASE_URL + "/v1/ask/";
const GITHUB_URL = "https://github.com/HamishSalisbury/RHNZ-RAG-Chatbot";
const RULES_URL = "https://www.rhnz.co.nz/_files/ugd/104e29_4b09de6d5d764d3bb9de58b9a3f3f101.pdf";
const ACCENT = "#e8442a";

type Status = "idle" | "loading" | "error" | "done";

export default function App() {
  const [question, setQuestion] = useState<string>("");
  const [answer, setAnswer] = useState<string>("");
  const [status, setStatus] = useState<Status>("idle");

  async function send() {
    const q = question.trim();
    if (!q || status === "loading") return;
    setStatus("loading");
    setAnswer("");
    try {
      const resp = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      if (!resp.ok) {
        setStatus("error");
        setAnswer("Error " + resp.status + ": " + (await resp.text()));
        return;
      }
      const data = await resp.json();
      setStatus("done");
      setAnswer(data.answer[0].text);
    } catch (err) {
      setStatus("error");
      setAnswer("ChatService is not available right now");
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") send();
  }

  return (
    <div style={{ minHeight: "100vh", background: "#0a0a0b", color: "#f4f4f5", fontFamily: "system-ui, sans-serif", display: "flex", justifyContent: "center", padding: "48px 16px", boxSizing: "border-box" }}>
      <div style={{ width: "100%", maxWidth: 720 }}>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <h1 style={{ fontSize: 32, fontWeight: 700, margin: 0 }}>RHNZ Rules Assistant</h1>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: "inline-flex", alignItems: "center", gap: 8, color: "#a1a1aa", textDecoration: "none", fontSize: 14, border: "1px solid #27272a", borderRadius: 8, padding: "8px 12px" }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 .5A11.5 11.5 0 0 0 .5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.54-3.88-1.54-.53-1.34-1.3-1.7-1.3-1.7-1.06-.72.08-.71.08-.71 1.17.08 1.79 1.2 1.79 1.2 1.04 1.79 2.73 1.27 3.4.97.1-.75.4-1.27.73-1.56-2.55-.29-5.24-1.28-5.24-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.8 0c2.2-1.5 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.43-2.7 5.4-5.26 5.69.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5z" />
            </svg>
            GitHub
          </a>
        </div>

        <p style={{ color: "#a1a1aa", fontSize: 15, lineHeight: 1.6, marginTop: 0, marginBottom: 32, maxWidth: 620 }}>
          A retrieval-augmented chatbot for the World Skate Rink Hockey rules. Ask a question in plain English and it retrieves the most relevant rules from the official rulebook, then answers using only that source material.
        </p>

        <div style={{ background: "#111113", border: "1px solid #27272a", borderRadius: 16, padding: 24 }}>
          <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#a1a1aa", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 }}>Ask a question</label>

          <input
            type="text"
            value={question}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g. How many timeouts can each team request?"
            autoFocus
            style={{ width: "100%", background: "#0a0a0b", border: "1px solid #27272a", borderRadius: 10, color: "#f4f4f5", padding: "14px 16px", fontSize: 15, boxSizing: "border-box", outline: "none" }}
          />

          <button
            onClick={send}
            disabled={status === "loading"}
            style={{ marginTop: 16, width: "100%", background: ACCENT, color: "#fff", border: "none", borderRadius: 10, padding: "14px 16px", fontSize: 15, fontWeight: 600, cursor: status === "loading" ? "default" : "pointer", opacity: status === "loading" ? 0.6 : 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}
          >
            {status === "loading" ? "Thinking..." : "Send Message"}
          </button>

          {answer && (
            <div style={{ marginTop: 20, padding: 16, background: "#0a0a0b", border: "1px solid " + (status === "error" ? "#7f1d1d" : "#27272a"), borderRadius: 10, whiteSpace: "pre-wrap", lineHeight: 1.6, fontSize: 15, color: status === "error" ? "#f87171" : "#e4e4e7" }}>
              {answer}
            </div>
          )}
        </div>

        <div style={{ marginTop: 24, padding: 16, border: "1px solid #27272a", borderRadius: 10, background: "#111113" }}>
          <p style={{ color: "#a1a1aa", fontSize: 13, lineHeight: 1.6, margin: 0 }}>
            This chatbot is a work in progress; it currently does not have access to live player stats and has not been evaluated for accuracy. Take its responses with a grain of salt; they may not be 100% correct or accurate at all.
          </p>
          <a
            href={RULES_URL}
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: "inline-block", marginTop: 12, color: ACCENT, textDecoration: "none", fontSize: 13, fontWeight: 600 }}
          >
            View the official RHNZ rules (PDF)
          </a>
        </div>

      </div>
    </div>
  );
}
