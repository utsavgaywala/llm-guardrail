# 🛡️ LLM GuardRail

> Production-grade safety middleware that sits between users and any LLM — blocking PII leakage, prompt injections, jailbreaks, and toxic responses before they cause harm.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)
![LLM](https://img.shields.io/badge/LLM-Llama--3.1-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 What is this?

Most developers just call an LLM API directly — no safety, no validation, no control.

**LLM GuardRail** adds a 3-stage protection pipeline between the user and the AI:
User Message → [Input Guardrails] → [LLM] → [Output Guardrails] → Safe Response

---

## ✨ Features

### 🔴 Input Guardrails
| Check | What it catches |
|---|---|
| PII Detection | Credit cards, emails, phone numbers, Aadhaar, PAN, passwords |
| Prompt Injection | "Ignore previous instructions", "Your new rules are..." |
| Jailbreak Detection | DAN prompts, "no restrictions", developer mode |
| Length Limit | Configurable max character limit |

### 🟡 Output Guardrails
| Check | What it catches |
|---|---|
| Toxicity Filter | Harmful or dangerous content in AI responses |
| Min Length | Rejects unhelpfully short responses |
| JSON Schema | Validates structure if JSON output is required |

### 🟢 YAML Policy Engine
- All rules live in one YAML file — no code changes needed
- Turn any rule ON/OFF with `enabled: true/false`
- Non-engineers can configure the gateway

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/utsavgaywala/llm-guardrail.git
cd llm-guardrail
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your API key
Create a `.env` file:
GROQ_API_KEY=your-key-here
LLM_MODEL=llama-3.1-8b-instant
Get free Groq API key at 👉 **console.groq.com**

### 5. Run the API server
```bash
uvicorn app.main:app --reload
```

### 6. Run the Streamlit dashboard
```bash
streamlit run streamlit_app.py
```

### 7. Open browser
- API docs → http://127.0.0.1:8000/docs
- Dashboard → http://localhost:8501

---

## 📁 Project Structure
llm-guardrail/
├── app/
│   ├── main.py                    # FastAPI app & /chat endpoint
│   ├── guardrails/
│   │   ├── input_guard.py         # PII, injection, jailbreak detection
│   │   ├── output_guard.py        # Toxicity, schema, length checks
│   │   └── policy_engine.py       # Loads & manages YAML policies
│   └── api/
│       └── llm_client.py          # LLM API wrapper (Groq/Llama)
├── config/
│   └── policies.yaml              # All rules configured here
├── tests/
│   └── test_guardrails.py         # Test suite
├── streamlit_app.py               # Visual dashboard UI
├── requirements.txt
└── README.md

---

## 🔌 API Usage

### Safe message
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is machine learning?", "user_id": "user_1"}'
```

### Response — Passed
```json
{
  "response": "Machine learning is...",
  "blocked": false,
  "block_reason": null,
  "checks_performed": [
    "pii_check: pass",
    "injection_check: pass",
    "jailbreak_check: pass",
    "llm_call: success",
    "toxicity_check: pass"
  ],
  "latency_ms": 1404.79
}
```

### Response — Blocked
```json
{
  "response": "Sorry, I cannot process that request.",
  "blocked": true,
  "block_reason": "PII detected: credit_card.",
  "checks_performed": ["pii_check: BLOCKED (credit_card)"],
  "latency_ms": 0.0
}
```

---

## ⚙️ Configure Policies

Edit `config/policies.yaml` — no code changes needed:

```yaml
policies:
  block_pii:
    enabled: true

  require_json_output:
    enabled: false

  max_input_length:
    enabled: true
    value: 2000
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.12 | Core language |
| FastAPI | REST API framework |
| Groq + Llama 3.1 | Free LLM provider |
| PyYAML | Policy config engine |
| Pydantic | Request/response validation |
| Streamlit | Visual dashboard |

---

## 💼 Resume Description

> Built a production-grade LLM safety middleware in Python/FastAPI that intercepts every user message and AI response through a configurable 3-stage pipeline. Implemented PII detection, prompt injection blocking, and jailbreak prevention on input, and toxicity filtering with schema validation on output. All rules managed through a YAML policy engine. Includes a real-time Streamlit dashboard showing live pipeline visualization.

---

## 📈 Future Improvements

- [ ] Request logging to PostgreSQL database
- [ ] Metrics dashboard with charts
- [ ] Rate limiting per user
- [ ] Deploy to Railway + Streamlit Cloud
- [ ] Docker support

---

## 📄 License

MIT — free to use and include in your portfolio.