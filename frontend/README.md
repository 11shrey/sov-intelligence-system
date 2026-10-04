# Frontend — SOVIA (Statement of Values Intelligence & Cleansing)

Next.js 16 + React 19 web application for the autonomous multi-agent Statement of Values (SOV) cleansing and risk intelligence pipeline.

---

## 🎨 User Interface & Workflow Architecture

The application provides dedicated role-based workflows for **Workers** and **Managers**:

### 1. Worker Workflow (5 Pipeline Stages)
1. **Upload & Sheet Intelligence:** Drag-and-drop SOV workbook (.xlsx, .xls), preview sheets, inspect detected candidate tabs, headers, and confidence scores.
2. **Schema Mapping (17 Canonical Fields):** Inspect and override source column mappings to the 17 Standard SOV Fields with confidence indicators.
3. **Data Quality & Anomaly Detection:** Review detected formatting anomalies, missing data flags, and proposed value fixes.
4. **Human Review Gate & Transformation:** Reviewers can `Approve`, `Reject`, or `Edit` individual cell recommendations and execute approved transformations.
5. **Output & Audit Trail:** Download cleaned standard SOV spreadsheets and inspect the tamper-evident cryptographic audit trail.

### 2. Manager Workflow
- **Overview & Metrics:** Operational dashboard with portfolio health, processing velocity, and anomaly distribution.
- **Queue Management:** Prioritized queue of SOV submissions awaiting managerial sign-off.
- **Session Review:** Granular verification of worker transformations and recommendations.
- **Team Governance:** Worker throughput and review activity tracking.
- **Organization Audit Log:** Immutable event log tracking all AI and human actions across sessions.

---

## 🔐 Demo Credentials

Role-gated authentication is available on `/signin`:
- **Worker Demo:** `worker123@ex.com` / `123456`
- **Manager Demo:** `manager123@ex.com` / `123456`

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or pnpm

### Installation & Development
```bash
# 1. Enter the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start local Next.js dev server
npm run dev

# 4. Build for production
npm run build

# 5. Run linting
npm run lint
```

The frontend will run at `http://localhost:3000`.

---

## 🔌 Backend Integration

- **Backend Target:** FastAPI backend service running at `http://localhost:8000/api`.
- **Environment Configuration:** Configure `NEXT_PUBLIC_API_URL` in `.env.local` (see `.env.example`).
