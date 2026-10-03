# Frontend - Agentic SOV Cleansing and Intelligence System

React + Vite frontend web application for the SOV Cleansing pipeline.

---

## 🎨 User Interface Workflow

1. **Step 1: Upload & Sheet Intelligence:** Drag-and-drop SOV workbook, preview sheets, inspect detected candidate tabs and confidence scores.
2. **Step 2: Schema Mapping:** Inspect and override source column mappings to the 17 Standard SOV Fields.
3. **Step 3: Quality & Recommendations:** View detected anomalies, missing data flags, and proposed value fixes.
4. **Step 4: Human Review Gate:** Reviewers can `Approve`, `Reject`, or `Edit` individual cell recommendations.
5. **Step 5: Transformation & Audit:** Execute approved transformations, view real-time audit trail, and download the cleaned standard SOV spreadsheet.

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or pnpm

### Installation & Development
```bash
# 1. Install dependencies
npm install

# 2. Start local Vite dev server
npm run dev
```

The frontend will run at `http://localhost:3000` and proxy API calls to `http://localhost:8000`.
