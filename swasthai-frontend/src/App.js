import { useState, useEffect } from "react";
import axios from "axios";

const API = "http://localhost:8000";

const LANGUAGES = [
  { code: "hi", label: "हिंदी", name: "Hindi", flag: "🇮🇳" },
  { code: "ta", label: "தமிழ்", name: "Tamil", flag: "🇮🇳" },
  { code: "te", label: "తెలుగు", name: "Telugu", flag: "🇮🇳" },
  { code: "kn", label: "ಕನ್ನಡ", name: "Kannada", flag: "🇮🇳" },
  { code: "bn", label: "বাংলা", name: "Bengali", flag: "🇮🇳" },
  { code: "en", label: "English", name: "English", flag: "🇬🇧" },
];

const SAMPLE_SYMPTOMS = {
  hi: "मुझे तीन दिनों से तेज बुखार और जोड़ों में दर्द है",
  ta: "எனக்கு மூன்று நாட்களாக காய்ச்சல் இருக்கிறது",
  te: "నాకు తలనొప్పి మరియు జ్వరం ఉంది",
  kn: "ನನಗೆ ಮೂರು ದಿನಗಳಿಂದ ತೀವ್ರ ಜ್ವರ ಮತ್ತು ತಲೆನೋವು ಇದೆ",
  bn: "আমার তিন দিন ধরে জ্বর এবং মাথাব্যথা হচ্ছে",
  en: "I have had high fever and joint pain for three days",
};

export default function App() {
  const [screen, setScreen] = useState("home");
  const [language, setLanguage] = useState("hi");
  const [symptomText, setSymptomText] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [roundInfo, setRoundInfo] = useState("");
  const [riskLevel, setRiskLevel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [questionNumber, setQuestionNumber] = useState(0);
  const [userLocation, setUserLocation] = useState({
    latitude: 12.9716,
    longitude: 77.5946,
  });
  const [locationStatus, setLocationStatus] = useState("detecting");

  const totalQuestions = 9;

  // Get real GPS location on load
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setUserLocation({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
          });
          setLocationStatus("found");
        },
        () => {
          setLocationStatus("default");
        }
      );
    } else {
      setLocationStatus("default");
    }
  }, []);

  const handleStartTriage = async () => {
    if (!symptomText.trim()) {
      setError("Please describe your symptoms.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await axios.post(`${API}/triage`, {
        text: symptomText,
        language,
      });
      const data = res.data;
      setSessionId(data.session_id);
      setQuestionNumber(1);
      if (data.risk_level) {
        setRiskLevel(data.risk_level);
        setScreen("result");
      } else {
        setQuestion(data.follow_up_question);
        setRoundInfo(data.status);
        setScreen("followup");
      }
    } catch {
      setError("Server not responding. Is the backend running?");
    }
    setLoading(false);
  };

  const handleFollowUp = async () => {
    if (!answer.trim()) {
      setError("Please type your answer.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await axios.post(`${API}/triage/followup`, {
        session_id: sessionId,
        answer,
        latitude: userLocation.latitude,
        longitude: userLocation.longitude,
      });
      const data = res.data;
      setAnswer("");
      setQuestionNumber((n) => n + 1);
      if (data.risk_level) {
        setRiskLevel(data.risk_level);
        setScreen("result");
      } else {
        setQuestion(data.follow_up_question);
        setRoundInfo(data.status);
      }
    } catch {
      setError("Something went wrong. Please try again.");
    }
    setLoading(false);
  };

  const handleReset = () => {
    setScreen("home");
    setSymptomText("");
    setSessionId(null);
    setQuestion("");
    setAnswer("");
    setRoundInfo("");
    setRiskLevel(null);
    setError("");
    setQuestionNumber(0);
  };

  const getRiskConfig = (risk) => {
    if (!risk) return {};
    if (risk.includes("RED"))
      return {
        color: "#c0392b",
        bg: "#fdf0ef",
        border: "#e74c3c",
        icon: "🔴",
        label: "Emergency",
        action: "Go to hospital immediately. Call 108 now.",
      };
    if (risk.includes("YELLOW"))
      return {
        color: "#d35400",
        bg: "#fef9f0",
        border: "#f39c12",
        icon: "🟡",
        label: "Attention needed",
        action: "Visit a clinic or doctor within 24 hours.",
      };
    if (risk.includes("GREEN"))
      return {
        color: "#1e8449",
        bg: "#eafaf1",
        border: "#27ae60",
        icon: "🟢",
        label: "You are okay",
        action: "Monitor at home. Rest and stay hydrated.",
      };
    return {};
  };

  const progressPercent = Math.min(
    (questionNumber / totalQuestions) * 100,
    100
  );
  const isPhase2 = roundInfo.includes("phase2");

  return (
    <div style={s.page}>
      <div style={s.blob1} />
      <div style={s.blob2} />

      <div style={s.wrapper}>
        {/* Header */}
        <div style={s.header}>
          <div style={s.logoRow}>
            <div style={s.logoIcon}>🏥</div>
            <div>
              <h1 style={s.logoText}>SwasthAI</h1>
              <p style={s.logoSub}>Multilingual Medical Triage</p>
            </div>
          </div>
          <div style={s.headerBadge}>AI · ICMR guidelines</div>
        </div>

        {/* Location status bar */}
        <div style={s.locationBar}>
          <span style={s.locationDot(locationStatus)} />
          <span style={s.locationText}>
            {locationStatus === "found"
              ? "Using your GPS location for nearby hospitals"
              : locationStatus === "detecting"
              ? "Detecting location..."
              : "Using default location (Bangalore)"}
          </span>
        </div>

        {/* HOME */}
        {screen === "home" && (
          <div style={s.card}>
            <div style={s.cardHeader}>
              <h2 style={s.cardTitle}>Tell us how you feel</h2>
              <p style={s.cardSub}>
                Describe your symptoms in your language. Our AI will assess
                urgency using ICMR clinical guidelines.
              </p>
            </div>

            {/* Language selector */}
            <label style={s.label}>Select your language</label>
            <div style={s.langGrid}>
              {LANGUAGES.map((l) => (
                <button
                  key={l.code}
                  style={{
                    ...s.langBtn,
                    ...(language === l.code ? s.langBtnActive : {}),
                  }}
                  onClick={() => {
                    setLanguage(l.code);
                    setSymptomText("");
                    setError("");
                  }}
                >
                  <span style={s.langFlag}>{l.flag}</span>
                  <span style={s.langName}>{l.name}</span>
                  <span style={s.langLocal}>{l.label}</span>
                </button>
              ))}
            </div>

            {/* Symptom input */}
            <div style={s.inputGroup}>
              <label style={s.label}>Describe your symptoms</label>
              <textarea
                style={s.textarea}
                placeholder={`e.g. ${SAMPLE_SYMPTOMS[language]}`}
                value={symptomText}
                onChange={(e) => {
                  setSymptomText(e.target.value);
                  setError("");
                }}
                rows={4}
              />
              <button
                style={s.hintBtn}
                onClick={() => setSymptomText(SAMPLE_SYMPTOMS[language])}
              >
                Use example sentence →
              </button>
            </div>

            {error && <div style={s.errorBox}>{error}</div>}

            <button
              style={{ ...s.primaryBtn, ...(loading ? s.btnDisabled : {}) }}
              onClick={handleStartTriage}
              disabled={loading}
            >
              {loading ? (
                <span style={s.loadingRow}>
                  <span style={s.spinner} /> Analyzing symptoms...
                </span>
              ) : (
                "Start triage →"
              )}
            </button>

            {/* Feature pills */}
            <div style={s.pillRow}>
              <span style={s.pill}>🔒 Anonymous</span>
              <span style={s.pill}>📋 ICMR guidelines</span>
              <span style={s.pill}>🏥 Finds nearby PHC</span>
              <span style={s.pill}>📱 SMS follow-up</span>
            </div>

            <div style={s.emergency}>
              <span>⚠️</span>
              <span>
                Life-threatening emergency?{" "}
                <strong style={{ color: "#c0392b" }}>Call 108 now</strong>
              </span>
            </div>
          </div>
        )}

        {/* FOLLOW-UP */}
        {screen === "followup" && (
          <div style={s.card}>
            {/* Progress */}
            <div style={s.progressSection}>
              <div style={s.progressHeader}>
                <span style={s.progressLabel}>
                  {isPhase2
                    ? "🔬 Disease-specific questions"
                    : "📋 General assessment"}
                </span>
                <span style={s.progressCount}>
                  {questionNumber} / {totalQuestions}
                </span>
              </div>
              <div style={s.progressTrack}>
                <div
                  style={{
                    ...s.progressFill,
                    width: `${progressPercent}%`,
                    backgroundColor: isPhase2 ? "#8e44ad" : "#1a6b3c",
                  }}
                />
              </div>
              {isPhase2 && (
                <div style={s.phase2Badge}>
                  AI has identified a suspected condition — now confirming with
                  targeted questions
                </div>
              )}
            </div>

            {/* Question */}
            <div style={s.questionCard}>
              <div style={s.questionIcon}>💬</div>
              <p style={s.questionText}>{question}</p>
            </div>

            {/* Answer */}
            <div style={s.inputGroup}>
              <label style={s.label}>Your answer</label>
              <input
                style={s.input}
                placeholder="Type your answer here..."
                value={answer}
                onChange={(e) => {
                  setAnswer(e.target.value);
                  setError("");
                }}
                onKeyDown={(e) => e.key === "Enter" && handleFollowUp()}
                autoFocus
              />
            </div>

            {error && <div style={s.errorBox}>{error}</div>}

            <button
              style={{ ...s.primaryBtn, ...(loading ? s.btnDisabled : {}) }}
              onClick={handleFollowUp}
              disabled={loading}
            >
              {loading ? (
                <span style={s.loadingRow}>
                  <span style={s.spinner} /> Processing...
                </span>
              ) : (
                "Submit answer →"
              )}
            </button>

            <button style={s.ghostBtn} onClick={handleReset}>
              ← Start over
            </button>
          </div>
        )}

        {/* RESULT */}
        {screen === "result" &&
          (() => {
            const cfg = getRiskConfig(riskLevel);

            // Split risk level from facility message
            const parts = riskLevel ? riskLevel.split("\n\n") : [];
            const riskPart = parts[0] || "";
            const facilityPart = parts.slice(1).join("\n\n") || "";

            return (
              <div style={s.card}>
                <div style={s.resultHeader}>
                  <div style={s.resultIconWrap}>{cfg.icon}</div>
                  <h2 style={{ ...s.resultLabel, color: cfg.color }}>
                    {cfg.label}
                  </h2>
                </div>

                {/* Risk box */}
                <div
                  style={{
                    ...s.riskBox,
                    backgroundColor: cfg.bg,
                    borderColor: cfg.border,
                  }}
                >
                  <p style={{ ...s.riskText, color: cfg.color }}>{riskPart}</p>
                </div>

                {/* Recommended action */}
                <div style={s.actionBox}>
                  <p style={s.actionLabel}>Recommended action</p>
                  <p style={s.actionText}>{cfg.action}</p>
                </div>

                {/* Facility message */}
                {facilityPart && (
                  <div style={s.facilityBox}>
                    <p style={s.facilityTitle}>📍 Nearby facilities</p>
                    <pre style={s.facilityText}>{facilityPart}</pre>
                  </div>
                )}

                {/* Helplines */}
                <div style={s.helplineGrid}>
                  <div style={s.helplineCard}>
                    <span style={s.helplineNum}>104</span>
                    <span style={s.helplineName}>Health helpline</span>
                  </div>
                  <div style={s.helplineCard}>
                    <span style={s.helplineNum}>108</span>
                    <span style={s.helplineName}>Ambulance</span>
                  </div>
                  <div style={s.helplineCard}>
                    <span style={s.helplineNum}>112</span>
                    <span style={s.helplineName}>Emergency</span>
                  </div>
                </div>

                {/* SMS confirmation */}
                <div style={s.smsBox}>
                  📱 A follow-up summary has been logged for this session.
                </div>

                <div style={s.disclaimer}>
                  ⚕️ This is an AI-assisted triage, not a medical diagnosis.
                  Always consult a qualified doctor.
                </div>

                <button style={s.primaryBtn} onClick={handleReset}>
                  Start new triage
                </button>
              </div>
            );
          })()}

        {/* Footer */}
        <p style={s.footer}>
          SwasthAI v0.4.0 · Built with ICMR clinical guidelines · For
          demonstration purposes only
        </p>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        * { box-sizing: border-box; }
        body { margin: 0; }
        textarea:focus, input:focus { outline: 2px solid #1a6b3c; border-color: #1a6b3c; }
        button:hover { opacity: 0.92; }
      `}</style>
    </div>
  );
}

const s = {
  page: {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #f0f7f4 0%, #e8f4fd 100%)",
    fontFamily: "'Segoe UI', Arial, sans-serif",
    position: "relative",
    overflowX: "hidden",
  },
  blob1: {
    position: "fixed",
    width: 400,
    height: 400,
    borderRadius: "50%",
    background: "rgba(26,107,60,0.06)",
    top: -100,
    right: -100,
    pointerEvents: "none",
  },
  blob2: {
    position: "fixed",
    width: 300,
    height: 300,
    borderRadius: "50%",
    background: "rgba(52,152,219,0.06)",
    bottom: -80,
    left: -80,
    pointerEvents: "none",
  },
  wrapper: {
    maxWidth: 520,
    margin: "0 auto",
    padding: "24px 16px 40px",
    position: "relative",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  logoRow: {
    display: "flex",
    alignItems: "center",
    gap: 12,
  },
  logoIcon: {
    fontSize: 36,
    lineHeight: 1,
  },
  logoText: {
    fontSize: 24,
    fontWeight: 700,
    color: "#1a6b3c",
    margin: 0,
    lineHeight: 1.2,
  },
  logoSub: {
    fontSize: 12,
    color: "#666",
    margin: 0,
  },
  headerBadge: {
    fontSize: 11,
    color: "#1a6b3c",
    background: "#e8f5ee",
    border: "1px solid #b8dfc9",
    borderRadius: 20,
    padding: "4px 10px",
    fontWeight: 500,
  },
  locationBar: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    marginBottom: 16,
    padding: "6px 12px",
    background: "#f8f8f8",
    borderRadius: 8,
    border: "1px solid #eee",
  },
  locationDot: (status) => ({
    width: 8,
    height: 8,
    borderRadius: "50%",
    flexShrink: 0,
    backgroundColor:
      status === "found"
        ? "#27ae60"
        : status === "detecting"
        ? "#f39c12"
        : "#888",
  }),
  locationText: {
    fontSize: 12,
    color: "#666",
  },
  card: {
    background: "#fff",
    borderRadius: 16,
    padding: "28px 24px",
    boxShadow: "0 4px 24px rgba(0,0,0,0.08)",
    border: "1px solid rgba(0,0,0,0.06)",
  },
  cardHeader: {
    marginBottom: 20,
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: 700,
    color: "#1a1a1a",
    margin: "0 0 6px",
  },
  cardSub: {
    fontSize: 14,
    color: "#666",
    margin: 0,
    lineHeight: 1.5,
  },
  langGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: 8,
    marginBottom: 20,
  },
  langBtn: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 2,
    padding: "10px 6px",
    border: "1.5px solid #e0e0e0",
    borderRadius: 10,
    background: "#fafafa",
    cursor: "pointer",
  },
  langBtnActive: {
    border: "1.5px solid #1a6b3c",
    background: "#eaf5ef",
  },
  langFlag: { fontSize: 18 },
  langName: { fontSize: 12, fontWeight: 600, color: "#333" },
  langLocal: { fontSize: 10, color: "#888" },
  inputGroup: { marginBottom: 16 },
  label: {
    display: "block",
    fontSize: 13,
    fontWeight: 600,
    color: "#444",
    marginBottom: 6,
  },
  textarea: {
    width: "100%",
    padding: "12px 14px",
    border: "1.5px solid #ddd",
    borderRadius: 10,
    fontSize: 15,
    fontFamily: "inherit",
    resize: "vertical",
    color: "#1a1a1a",
    background: "#fafafa",
  },
  input: {
    width: "100%",
    padding: "12px 14px",
    border: "1.5px solid #ddd",
    borderRadius: 10,
    fontSize: 15,
    fontFamily: "inherit",
    color: "#1a1a1a",
    background: "#fafafa",
  },
  hintBtn: {
    background: "none",
    border: "none",
    color: "#1a6b3c",
    fontSize: 12,
    cursor: "pointer",
    padding: "4px 0",
    marginTop: 4,
    textDecoration: "underline",
  },
  primaryBtn: {
    width: "100%",
    padding: "14px",
    background: "#1a6b3c",
    color: "#fff",
    border: "none",
    borderRadius: 10,
    fontSize: 16,
    fontWeight: 600,
    cursor: "pointer",
    marginBottom: 12,
  },
  btnDisabled: {
    background: "#7fb89a",
    cursor: "not-allowed",
  },
  ghostBtn: {
    width: "100%",
    padding: "12px",
    background: "none",
    color: "#666",
    border: "1.5px solid #e0e0e0",
    borderRadius: 10,
    fontSize: 14,
    cursor: "pointer",
  },
  loadingRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
  },
  spinner: {
    display: "inline-block",
    width: 16,
    height: 16,
    border: "2px solid rgba(255,255,255,0.3)",
    borderTopColor: "#fff",
    borderRadius: "50%",
    animation: "spin 0.7s linear infinite",
  },
  errorBox: {
    background: "#fdf0ef",
    border: "1px solid #f5c6c6",
    borderRadius: 8,
    padding: "10px 14px",
    fontSize: 13,
    color: "#c0392b",
    marginBottom: 12,
  },
  pillRow: {
    display: "flex",
    gap: 6,
    flexWrap: "wrap",
    marginBottom: 16,
  },
  pill: {
    fontSize: 11,
    color: "#555",
    background: "#f4f4f4",
    borderRadius: 20,
    padding: "4px 10px",
    border: "1px solid #e8e8e8",
  },
  emergency: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 14px",
    background: "#fdf0ef",
    border: "1px solid #fcc",
    borderRadius: 8,
    fontSize: 13,
    color: "#555",
  },
  progressSection: { marginBottom: 24 },
  progressHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  progressLabel: { fontSize: 12, color: "#666", fontWeight: 500 },
  progressCount: { fontSize: 12, color: "#1a6b3c", fontWeight: 600 },
  progressTrack: {
    height: 6,
    background: "#eee",
    borderRadius: 10,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    borderRadius: 10,
    transition: "width 0.4s ease",
  },
  phase2Badge: {
    marginTop: 8,
    fontSize: 12,
    color: "#8e44ad",
    background: "#f5eeff",
    border: "1px solid #d8b8f0",
    borderRadius: 6,
    padding: "6px 10px",
    lineHeight: 1.4,
  },
  questionCard: {
    background: "#f0f7f4",
    border: "1.5px solid #b8dfc9",
    borderRadius: 12,
    padding: "16px 18px",
    marginBottom: 20,
    display: "flex",
    gap: 12,
    alignItems: "flex-start",
  },
  questionIcon: { fontSize: 22, flexShrink: 0 },
  questionText: {
    fontSize: 16,
    color: "#1a1a1a",
    margin: 0,
    lineHeight: 1.6,
  },
  resultHeader: { textAlign: "center", marginBottom: 20 },
  resultIconWrap: { fontSize: 52, lineHeight: 1, marginBottom: 8 },
  resultLabel: { fontSize: 22, fontWeight: 700, margin: 0 },
  riskBox: {
    border: "2px solid",
    borderRadius: 12,
    padding: "16px 18px",
    marginBottom: 16,
  },
  riskText: {
    fontSize: 15,
    fontWeight: 600,
    margin: 0,
    lineHeight: 1.6,
  },
  actionBox: {
    background: "#f8f8f8",
    borderRadius: 10,
    padding: "14px 16px",
    marginBottom: 16,
  },
  actionLabel: {
    fontSize: 11,
    fontWeight: 700,
    color: "#888",
    textTransform: "uppercase",
    letterSpacing: 0.8,
    margin: "0 0 4px",
  },
  actionText: {
    fontSize: 15,
    color: "#1a1a1a",
    margin: 0,
    fontWeight: 500,
  },
  facilityBox: {
    background: "#f0f7f4",
    border: "1px solid #b8dfc9",
    borderRadius: 10,
    padding: "14px 16px",
    marginBottom: 16,
  },
  facilityTitle: {
    fontSize: 13,
    fontWeight: 700,
    color: "#1a6b3c",
    margin: "0 0 8px",
  },
  facilityText: {
    fontSize: 13,
    color: "#333",
    margin: 0,
    whiteSpace: "pre-wrap",
    fontFamily: "inherit",
    lineHeight: 1.6,
  },
  helplineGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: 10,
    marginBottom: 16,
  },
  helplineCard: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 4,
    padding: "12px 8px",
    background: "#f4f4f4",
    borderRadius: 10,
    border: "1px solid #e8e8e8",
  },
  helplineNum: { fontSize: 22, fontWeight: 700, color: "#1a6b3c" },
  helplineName: { fontSize: 11, color: "#666", textAlign: "center" },
  smsBox: {
    fontSize: 13,
    color: "#1a6b3c",
    background: "#eaf5ef",
    border: "1px solid #b8dfc9",
    borderRadius: 8,
    padding: "10px 14px",
    marginBottom: 16,
    textAlign: "center",
  },
  disclaimer: {
    fontSize: 12,
    color: "#888",
    textAlign: "center",
    marginBottom: 20,
    lineHeight: 1.5,
    padding: "0 8px",
  },
  footer: {
    textAlign: "center",
    fontSize: 11,
    color: "#aaa",
    marginTop: 20,
    lineHeight: 1.6,
  },
};