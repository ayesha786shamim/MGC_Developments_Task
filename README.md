# MGC Sales Assistant

Take-home for **MGC Developments** (Islamabad).

Sales staff waste time re-answering the same PDF questions, and get more leads than they can call. This project covers that problem in four parts:

| Part | What it does |
|------|----------------|
| 1 | Document Q&A grounded in real MGC docs (with sources) |
| 2 | SQL schema + queries for messy CRM leads |
| 3 | Baseline model that scores conversion likelihood |
| 4 | Minimal web UI that wires Parts 1 and 3 together |

**Stack:** Python FastAPI · Next.js · scikit-learn · Gemini API

---

## 1. How to run

### Requirements

- Python 3.10+
- Node.js 18+
- Gemini API key

### Step A — API key

```bash
cp .env.example .env
```

Put your key in `.env`:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash
```

### Step B — Backend

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r Backend/requirements.txt
cd Backend
python train_model.py
uvicorn main:app --reload --port 8000
```

- API: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  

### Step C — Frontend

Open a **second** terminal:

```bash
cd Frontend
npm install
npm run dev
```

Open **http://localhost:3000**

You should see **Document Q&A** and **Lead score**.

---

## 2. Part 1 — Document Q&A (hard cases)

### How it works

1. Load and chunk the three files in `docs/`
2. Retrieve the most relevant passages (TF-IDF)
3. Send those passages to **Gemini**
4. Return the answer **with the source shown**

Code: `Backend/rag/` (`loader.py`, `embeddings.py`, `qa.py`)

### Source documents

| File | Contents |
|------|----------|
| `docs/01_mgc_aurora_heights_brochure.md` | Project overview, units, amenities, unconfirmed anchor |
| `docs/02_price_list_payment_plan.md` | Base prices, premiums, payment plan, transfer fee **2%** |
| `docs/03_booking_policy_faq.md` | Booking/refunds, transfer fee **2.5%**, rental yield refusal |

### Hard cases (what reviewers check)

| Question | Expected behaviour |
|----------|--------------------|
| What's the base price of a 2-bed in Block B? | **Grounded lookup** — Block B 2-Bed Standard **PKR 22,425,000** |
| What's the total for a Margalla-facing corner unit on floor 15, 2-bed Block B? | Base + **stacked premiums** (+4% +3% +6% = +13%) |
| What's the transfer fee? | **Conflict** — price list **2%** vs FAQ **2.5%**. Show both; do not pick one |
| What's the rental yield on a 1-bed? | **Refusal** — not published; escalate to marketing manager |
| Who is the anchor tenant? | **Unconfirmed** — discussions ongoing; no name |

These matter more than polish: a confident wrong answer costs a sale; “I don’t have that” does not.

---

## 3. Part 2 — Database (schema sense)

Files:

- `Backend/database/schema.sql`
- `Backend/database/queries.sql`

### Schema choices

- One table: `leads` (matches `leads.csv`)
- **Keys**
  - `id` — primary key
  - `lead_id` — unique business id
  - `crm_record_hash` — **UNIQUE** (stops the same person being entered twice by different agents)
- **Types**
  - `TEXT` for ids / categories / timestamps
  - `REAL` for money and continuous numbers
  - `INTEGER` for counts and 0/1 flags (`converted`, `is_overseas`, etc.)

### Duplicate logic

- **Find duplicates (query 2):** `GROUP BY crm_record_hash` with `HAVING COUNT(*) > 1`
- **Prevent at schema level:** `UNIQUE (crm_record_hash)` so a second insert of the same CRM person fails

### Query 1

Conversion rate by `source`, only sources with **200+** leads, best rate first.

---

## 4. Part 3 — ML decisions (honest baseline)

Data: `leads.csv`  
Target: `converted`  
Class balance: about **93% not converted / 7% converted**

### Dropped (and why)

| Column | Why dropped |
|--------|-------------|
| `lead_id` | Identifier — not useful for scoring a new lead |
| `crm_record_hash` | Identifier — same reason |
| `token_amount_received_pkr` | **Leakage** — token money usually means they are already serious / mid-booking |
| `created_at` | Raw timestamp skipped in this baseline (needs careful time features) |

### Kept

- Profile: `source`, `city`, `area`, `property_type`, `budget_pkr_lac`, `bedrooms`
- Engagement: `first_response_minutes`, `calls_made`, `total_call_seconds`, `whatsapp_replies`, `site_visits`
- Flags: `agent_experience_years`, `is_overseas`, `referred_by_existing_client`, `has_financing_approved`

### Cleaning

- Missing numbers → median
- Missing categories → most frequent
- Categories → one-hot
- Numbers → scaled
- City **casing** normalized (`ISLAMABAD` → `Islamabad`); short forms like `ISB` / `Rwp` left as-is
- Duplicate rows **not** removed before training (schema handles prevention)

### Model

- Logistic regression, `class_weight="balanced"`
- No tuning
- Train: `cd Backend && python train_model.py`
- Saved: `Backend/models/conversion_model.joblib`

### Metric (one honest number)

| Metric | Value | Why this metric |
|--------|-------|-----------------|
| **Average Precision (PR-AUC)** | **≈ 0.33** | Only ~7% convert. Accuracy would look good while missing converters. PR-AUC better matches “who to call first”. |

---

## 5. Part 4 — Web UI

One page, two modes:

1. **Document Q&A** — question → answer + source  
2. **Lead score** — lead fields → conversion %  

Frontend: `Frontend/` (Next.js)  
Backend API: `POST /api/ask`, `POST /api/score`

---

## Project layout

```text
docs/                 brochure, price list, booking FAQ
leads.csv
.env.example
README.md

Backend/
  main.py             FastAPI entry
  train_model.py
  requirements.txt
  rag/                Part 1 — retrieve + Gemini
  ml/                 Part 3 — preprocess + train/score
  database/           Part 2 — schema.sql, queries.sql
  models/             conversion_model.joblib

Frontend/             Part 4 — Sales Desk UI
```

---

## Known limits

- Part 1 needs a valid `GEMINI_API_KEY`. Free-tier Gemini can return **429** if you ask too often — wait and retry.
- Retrieval is TF-IDF (not embeddings). Fine for this doc set.
- No auth, tests, or deployment (out of scope for the brief).
- Optional screen recording not included.

---

*MGC Developments · Near Al-Jannat Mall, GT Road, Islamabad*
