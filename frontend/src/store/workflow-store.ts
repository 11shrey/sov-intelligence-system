import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { SOVSession, MappingField, DQIssue, TransformationRule, AuditEventItem, SessionWorkflowStatus } from '@/types';

interface WorkflowStore {
  // Sessions
  sessions: SOVSession[];
  activeSessionId: string;
  getActiveSession: () => SOVSession;
  setActiveSessionId: (id: string) => void;

  // Selected Sheet
  selectedSheet: string;
  setSelectedSheet: (sheet: string) => void;

  // Mappings
  mappings: MappingField[];
  acceptMapping: (id: number) => void;
  rejectMapping: (id: number) => void;
  updateMappingTarget: (id: number, targetCanonical: string) => void;
  acceptAllHighConfidence: () => void;
  selectedMappingId: number;
  setSelectedMappingId: (id: number) => void;

  // Data Quality
  dqIssues: DQIssue[];
  resolveDqIssue: (id: number) => void;
  unresolveDqIssue: (id: number) => void;
  acceptAllRecommendedFixes: () => void;

  // Transformations
  transformations: TransformationRule[];

  // Workflow Actions (Human in the loop)
  submitSessionForReview: (sessionId: string) => void;
  managerApproveSession: (sessionId: string, managerName: string) => void;
  managerReturnSession: (sessionId: string, remarks: string, managerName: string) => void;
  setSessionStatus: (sessionId: string, status: SessionWorkflowStatus) => void;

  // Audit Log
  auditEvents: AuditEventItem[];
  addAuditEvent: (event: Omit<AuditEventItem, 'id'>) => void;
}

const INITIAL_SESSIONS: SOVSession[] = [
  {
    id: 'SOV-2026-1042',
    fileName: 'Property_SOV_Jan.xlsx',
    fileSize: '12.4 MB',
    sheetCount: 3,
    rowCount: 842,
    columnCount: 24,
    status: 'ready', // will transition to 'awaiting', 'approved', 'returned'
    workerName: 'Aarav Sharma',
    workerAvatar: 'AS',
    workerId: 'AS-90412',
    updatedAt: 'Today, 10:24 AM',
    targetSheet: 'Property_Schedule',
    confidence: 94,
    hash: 'sha256:7f9ba4e1...89c2',
  },
  {
    id: 'SOV-2026-1043',
    fileName: 'Portfolio_Buildings_Q1.xlsx',
    fileSize: '48.2 MB',
    sheetCount: 6,
    rowCount: 4120,
    columnCount: 30,
    status: 'processing',
    workerName: 'Riya Mehta',
    workerAvatar: 'RM',
    workerId: 'RM-20941',
    updatedAt: 'Today, 09:12 AM',
    targetSheet: 'Building_Schedule',
    confidence: 88,
    hash: 'sha256:1a84f09e...44b1',
  },
  {
    id: 'SOV-2026-1039',
    fileName: 'Insurance_Commercial_2025.xlsx',
    fileSize: '8.1 MB',
    sheetCount: 1,
    rowCount: 320,
    columnCount: 17,
    status: 'approved',
    workerName: 'Kabir Singh',
    workerAvatar: 'KS',
    workerId: 'KS-88124',
    updatedAt: 'Yesterday, 16:42',
    targetSheet: 'Master_SOV',
    confidence: 99,
    hash: 'sha256:3c9d81fe...7710',
    approvedAt: 'Yesterday, 17:15',
  },
  {
    id: 'SOV-2026-1038',
    fileName: 'Regional_Assets_Midwest.xlsx',
    fileSize: '19.3 MB',
    sheetCount: 4,
    rowCount: 1290,
    columnCount: 22,
    status: 'approved',
    workerName: 'Aarav Sharma',
    workerAvatar: 'AS',
    workerId: 'AS-90412',
    updatedAt: 'Yesterday, 14:21',
    targetSheet: 'Midwest_Properties',
    confidence: 97,
    hash: 'sha256:9f40e1b7...219c',
    approvedAt: 'Yesterday, 15:02',
  },
  {
    id: 'SOV-2026-1044',
    fileName: 'Commercial_Logistics_SOV_v2.xlsx',
    fileSize: '31.0 MB',
    sheetCount: 2,
    rowCount: 1840,
    columnCount: 26,
    status: 'processing',
    workerName: 'Alex Rivera',
    workerAvatar: 'AR',
    workerId: 'AR-70192',
    updatedAt: 'Today, 08:35 AM',
    targetSheet: 'Warehouse_Locations',
    confidence: 85,
    hash: 'sha256:6e10ac8b...5529',
  },
  {
    id: 'SOV-2026-1040',
    fileName: 'NorthPlant_SOV.xlsx',
    fileSize: '15.6 MB',
    sheetCount: 2,
    rowCount: 842,
    columnCount: 19,
    status: 'awaiting',
    workerName: 'Riya Mehta',
    workerAvatar: 'RM',
    workerId: 'RM-20941',
    updatedAt: 'Today, 09:18 AM',
    targetSheet: 'Plant_Schedule',
    confidence: 91,
    hash: 'sha256:4b917fa2...901e',
    submittedAt: 'Today, 09:18 AM',
  },
  {
    id: 'SOV-2026-1035',
    fileName: 'MetroAssets_SOV.xlsx',
    fileSize: '24.1 MB',
    sheetCount: 3,
    rowCount: 2104,
    columnCount: 21,
    status: 'returned',
    workerName: 'Kabir Singh',
    workerAvatar: 'KS',
    workerId: 'KS-88124',
    updatedAt: 'Today, 09:56 AM',
    targetSheet: 'Locations',
    confidence: 82,
    hash: 'sha256:889fc102...33b1',
    returnedAt: 'Today, 09:56 AM',
    returnRemarks: 'Replacement Cost variance requires secondary actuarial sign-off before final clearance.',
  },
];

const INITIAL_MAPPINGS: MappingField[] = [
  {
    id: 1,
    sourceField: 'Prop ID',
    targetCanonical: 'Property ID',
    confidence: 98,
    status: 'proposed',
    sampleValues: ['PR-001', 'PR-002', 'PR-003'],
    dataType: 'String / Unique Identifier',
    reasoning: 'Matched token "Prop ID" to canonical Property ID based on distinct sequential values.',
  },
  {
    id: 2,
    sourceField: 'Bldg Repl Cost',
    targetCanonical: 'Building Replacement Cost',
    confidence: 94,
    status: 'proposed',
    sampleValues: ['$1,450,000', '$22,800,000', '-$1,450,000 (negative anomaly detected)', '$5,750,000'],
    dataType: 'Currency / Monitored Float (USD)',
    reasoning: 'LLM Schema Agent matched "Bldg Repl Cost" with 94% certainty based on token n-grams ("Repl Cost" → "Replacement Cost") and distribution of non-zero monetary values across 842 properties.',
  },
  {
    id: 3,
    sourceField: 'Yr Built',
    targetCanonical: 'Year Built',
    confidence: 91,
    status: 'proposed',
    sampleValues: ['1998', '2014', '2005', '2021'],
    dataType: 'Integer / Year (YYYY)',
    reasoning: 'Token "Yr Built" matches canonical Year Built. Discrete 4-digit calendar values observed.',
  },
  {
    id: 4,
    sourceField: 'No. Floors',
    targetCanonical: 'Stories / Levels',
    confidence: 74,
    status: 'needs_review',
    sampleValues: ['3 floors', '12', 'B+4', '2'],
    dataType: 'Mixed String / Numeric',
    reasoning: 'Confidence 74%. Natural language phrases detected ("3 floors"). Rule needed to extract leading integer.',
  },
  {
    id: 5,
    sourceField: 'Aux_Val',
    targetCanonical: '[Select Target Field...]',
    confidence: 42,
    status: 'unmapped',
    sampleValues: ['TIER-B', 'TIER-A', 'CUSTOM-1'],
    dataType: 'String / Categorical',
    reasoning: 'Low confidence (42%). Does not match any core canonical actuarial field with certainty.',
  },
  {
    id: 6,
    sourceField: 'Street Address 1',
    targetCanonical: 'Street Address',
    confidence: 99,
    status: 'accepted',
    sampleValues: ['104 Commercial Blvd', '42 Main St', '88 Industry Way'],
    dataType: 'String / Postal Address',
    reasoning: 'Exact lexical match to canonical Street Address schema.',
  },
  {
    id: 7,
    sourceField: 'City_Loc',
    targetCanonical: 'City',
    confidence: 97,
    status: 'accepted',
    sampleValues: ['Chicago', 'Dallas', 'Atlanta'],
    dataType: 'String / Municipality',
    reasoning: 'Matches standard US municipal naming directory with 97% confidence.',
  },
  {
    id: 8,
    sourceField: 'State_Prov',
    targetCanonical: 'State',
    confidence: 96,
    status: 'accepted',
    sampleValues: ['IL', 'TX', 'GA'],
    dataType: 'Char(2) / Jurisdiction',
    reasoning: 'Standard 2-letter postal abbreviation match.',
  },
  {
    id: 9,
    sourceField: 'ZIP_Postal',
    targetCanonical: 'Postal Code',
    confidence: 98,
    status: 'accepted',
    sampleValues: ['60601', '75201', '30303'],
    dataType: 'ZIP / Postal Code',
    reasoning: '5-digit US ZIP format with 98% validity.',
  },
  {
    id: 10,
    sourceField: 'Occupancy_Class',
    targetCanonical: 'Occupancy Type',
    confidence: 88,
    status: 'proposed',
    sampleValues: ['Commercial Office', 'Light Industrial', 'Retail Mall'],
    dataType: 'Categorical / Industry Standard',
    reasoning: 'Lexical alignment with ISO commercial occupancy table.',
  },
  {
    id: 11,
    sourceField: 'ISO_Const_Code',
    targetCanonical: 'Construction Class',
    confidence: 92,
    status: 'proposed',
    sampleValues: ['NC-3', '3 - Masonry Non-Combustible', 'ISO 4'],
    dataType: 'String / ISO Code',
    reasoning: 'Standard ISO commercial construction classes 1 through 6.',
  },
  {
    id: 12,
    sourceField: 'TIV_Total',
    targetCanonical: 'Total Insurable Value',
    confidence: 99,
    status: 'accepted',
    sampleValues: ['$3,250,000', '$45,000,000', '$12,100,000'],
    dataType: 'Currency / Monitored Float (USD)',
    reasoning: 'Matches aggregate financial limits definitions.',
  },
];

const INITIAL_DQ_ISSUES: DQIssue[] = [
  {
    id: 1,
    title: 'Negative Replacement Cost Values in Bldg_Repl_Cost_USD',
    description: 'Building replacement value cannot be less than zero in actuarial catastrophe modeling datasets.',
    severity: 'critical',
    status: 'pending',
    affectedRows: '2 rows affected (Row 142, Row 689)',
    category: 'Negative/Impossible Values',
    suggestedFix: 'Invert negative sign using Math.abs() per actuarial replacement cost policy.',
  },
  {
    id: 2,
    title: 'Postal Code & State Inconsistency in Midwest Region',
    description: 'ZIP code 60601 belongs to Illinois (IL), but state field was submitted as "IN" (Indiana).',
    severity: 'critical',
    status: 'pending',
    affectedRows: '1 row affected (Row 204)',
    category: 'Cross-Field Inconsistencies',
    suggestedFix: 'Re-align state to "IL" using authoritative USPS geocoder directory.',
  },
  {
    id: 3,
    title: 'Mixed Construction Code Nomenclature (NC-3 vs ISO 3)',
    description: '41 rows contain mixed broker terminology "NC-3" instead of canonical "3 - Non-Combustible".',
    severity: 'warning',
    status: 'pending',
    affectedRows: '41 rows affected',
    category: 'Inconsistent Values',
    suggestedFix: 'Standardize to ISO Construction Class 3.',
  },
  {
    id: 4,
    title: 'Future Year Built Flag (> 2025)',
    description: '5 records indicate construction years in 2026-2028 (Under Construction / Builder Risk).',
    severity: 'warning',
    status: 'pending',
    affectedRows: '5 rows affected (Rows 88, 92, 114, 302, 518)',
    category: 'Outliers',
    suggestedFix: 'Retain builder-risk status note without dropping value; pass to raw archive.',
  },
  {
    id: 5,
    title: 'Trailing Whitespace and Inconsistent Casing in Street Addresses',
    description: 'Street strings contain double-spaces and inconsistent title-casing (e.g., "STREET" vs "St.").',
    severity: 'info',
    status: 'pending',
    affectedRows: '12 rows affected',
    category: 'Invalid Formats',
    suggestedFix: 'Apply standard USPS capitalization and trim leading/trailing spaces.',
  },
];

const INITIAL_TRANSFORMATIONS: TransformationRule[] = [
  {
    id: 1,
    title: 'Bldg_Repl_Cost_USD Sign Inversion',
    ruleCode: 'Math.abs()',
    description: 'Row 142 & Row 689 inverted negative values ($1.45M, $320K) to positive replacement costs per actuarial sign validation.',
    applied: true,
    decision: 'Approved',
  },
  {
    id: 2,
    title: 'Postal Code & State Harmonization',
    ruleCode: 'USPS Geo-match',
    description: 'Re-aligned ZIP 60601 to "IL" from broker-submitted "IN". Canonical centroid index updated accordingly.',
    applied: true,
    decision: 'Approved',
  },
  {
    id: 3,
    title: 'ISO Construction Code Normalization',
    ruleCode: 'ISO-1 to ISO-6',
    description: 'Re-mapped "NC-3" and "3 - Masonry Non-Combustible" across 41 policy rows to Canonical Standard Code "3".',
    applied: true,
    decision: 'Approved',
  },
  {
    id: 4,
    title: 'TIV Currency Normalization',
    ruleCode: 'Regex Strip & Cast',
    description: 'Stripped mixed "$" and "USD" text tokens to numeric canonical DECIMAL(14,2) representation.',
    applied: true,
    decision: 'Approved',
  },
  {
    id: 5,
    title: 'Address Casing Standardization',
    ruleCode: 'USPS Casing',
    description: 'Capitalized proper street titles, standard abbreviations (ST, AVE, BLVD), and stripped trailing whitespace across 12 rows.',
    applied: true,
    decision: 'Approved',
  },
];

const INITIAL_AUDIT_EVENTS: AuditEventItem[] = [
  {
    id: 'EVT-4093',
    timestamp: 'Today 10:48:12 AM',
    date: 'Oct 2, 2026',
    actor: 'S. Reynolds',
    actorType: 'manager',
    actorTitle: 'Manager, Risk Underwriting',
    action: 'Approved transformation & signed ledger hash',
    targetScope: 'Session: Property_SOV_Jan.xlsx',
    sessionFile: 'Property_SOV_Jan.xlsx',
    sessionId: 'SOV-2026-1042',
    status: 'approved',
    evidenceHash: 'sha256:7f99b0c2...e81a',
    aiRecommendation: 'Map Yr Built → Year Built (96% Match)',
    humanDecision: 'S. Reynolds verified against policy ledger #UW-48992',
    resultingRule: 'Target: Year Built, Type: INTEGER (YYYY)',
    nonce: '0x93FA910B',
  },
  {
    id: 'EVT-4092',
    timestamp: 'Today 10:42:15 AM',
    date: 'Oct 2, 2026',
    actor: 'Aarav Sharma',
    actorType: 'worker',
    actorTitle: 'Risk Ops Worker',
    action: 'Submitted session for review',
    targetScope: 'Session: Property_SOV_Jan.xlsx',
    sessionFile: 'Property_SOV_Jan.xlsx',
    sessionId: 'SOV-2026-1042',
    status: 'awaiting',
    evidenceHash: 'sha256:8f4a99c2...4110',
    nonce: '0x10B49F88',
  },
  {
    id: 'EVT-4091',
    timestamp: 'Today 10:38:00 AM',
    date: 'Oct 2, 2026',
    actor: 'Aarav Sharma',
    actorType: 'worker',
    actorTitle: 'Risk Ops Worker',
    action: 'Resolved data quality issue: Inverted negative replacement cost',
    targetScope: 'Field: Bldg_Repl_Cost_USD',
    sessionFile: 'Property_SOV_Jan.xlsx',
    sessionId: 'SOV-2026-1042',
    status: 'signed',
    evidenceHash: 'sha256:6e10ac8b...5529',
    aiRecommendation: 'Flagged -$1,450,000 as impossible negative replacement cost',
    humanDecision: 'Human signed fix: Applied Math.abs() on Row 142 & 689',
    resultingRule: 'Enforce positive float for all Bldg_Repl_Cost',
    nonce: '0x932F11CA',
  },
  {
    id: 'EVT-4090',
    timestamp: 'Today 10:24:18 AM',
    date: 'Oct 2, 2026',
    actor: 'Data Quality Agent',
    actorType: 'ai',
    actorTitle: 'SOVIA Core AI',
    action: 'Detected 3 data-quality issues',
    targetScope: 'Field: "Yr Built", "Bldg_Repl_Cost"',
    sessionFile: 'Property_SOV_Jan.xlsx',
    sessionId: 'SOV-2026-1042',
    status: 'flagged',
    evidenceHash: 'sha256:3c9d81fe...7710',
    nonce: '0x44F019AB',
  },
  {
    id: 'EVT-4089',
    timestamp: 'Today 10:18:04 AM',
    date: 'Oct 2, 2026',
    actor: 'Schema Agent',
    actorType: 'ai',
    actorTitle: 'SOVIA Core AI',
    action: 'Generated 15/17 canonical field bindings',
    targetScope: 'Workbook: Property_SOV_Jan.xlsx',
    sessionFile: 'Property_SOV_Jan.xlsx',
    sessionId: 'SOV-2026-1042',
    status: 'applied',
    evidenceHash: 'sha256:1a84f09e...44b1',
    nonce: '0x55E90212',
  },
];

export const useWorkflowStore = create<WorkflowStore>()(persist((set, get) => ({
  sessions: INITIAL_SESSIONS,
  activeSessionId: 'SOV-2026-1042',
  selectedSheet: 'Property_Schedule',

  getActiveSession: () => {
    const s = get().sessions.find((s) => s.id === get().activeSessionId);
    return s || get().sessions[0];
  },

  setActiveSessionId: (id: string) => {
    set({ activeSessionId: id });
  },

  setSelectedSheet: (sheet: string) => {
    set({ selectedSheet: sheet });
  },

  mappings: INITIAL_MAPPINGS,
  selectedMappingId: 2,

  setSelectedMappingId: (id: number) => {
    set({ selectedMappingId: id });
  },

  acceptMapping: (id: number) => {
    set((state) => ({
      mappings: state.mappings.map((m) => (m.id === id ? { ...m, status: 'accepted' } : m)),
    }));
  },

  rejectMapping: (id: number) => {
    set((state) => ({
      mappings: state.mappings.map((m) => (m.id === id ? { ...m, status: 'unmapped' } : m)),
    }));
  },

  updateMappingTarget: (id: number, targetCanonical: string) => {
    set((state) => ({
      mappings: state.mappings.map((m) =>
        m.id === id
          ? {
              ...m,
              targetCanonical,
              status: targetCanonical.includes('[Select') ? 'unmapped' : 'accepted',
              confidence: targetCanonical.includes('[Select') ? 0 : Math.max(m.confidence, 88),
            }
          : m
      ),
    }));
  },

  acceptAllHighConfidence: () => {
    set((state) => ({
      mappings: state.mappings.map((m) => (m.confidence >= 90 ? { ...m, status: 'accepted' } : m)),
    }));
  },

  dqIssues: INITIAL_DQ_ISSUES,

  resolveDqIssue: (id: number) => {
    set((state) => ({
      dqIssues: state.dqIssues.map((issue) => (issue.id === id ? { ...issue, status: 'resolved' } : issue)),
    }));
  },

  unresolveDqIssue: (id: number) => {
    set((state) => ({
      dqIssues: state.dqIssues.map((issue) => (issue.id === id ? { ...issue, status: 'pending' } : issue)),
    }));
  },

  acceptAllRecommendedFixes: () => {
    set((state) => ({
      dqIssues: state.dqIssues.map((issue) => (issue.severity !== 'critical' ? { ...issue, status: 'resolved' } : issue)),
    }));
  },

  transformations: INITIAL_TRANSFORMATIONS,

  submitSessionForReview: (sessionId: string) => {
    set((state) => {
      const updated = state.sessions.map((s) =>
        s.id === sessionId
          ? {
              ...s,
              status: 'awaiting' as SessionWorkflowStatus,
              submittedAt: 'Today, 10:14 AM',
            }
          : s
      );

      const session = state.sessions.find((s) => s.id === sessionId);
      const newEvent: AuditEventItem = {
        id: `EVT-${Date.now().toString().slice(-4)}`,
        timestamp: 'Today, 10:14 AM',
        date: 'Oct 2, 2026',
        actor: session?.workerName || 'A. Sharma',
        actorType: 'worker',
        actorTitle: 'Risk Ops Worker',
        action: 'Submitted session to Manager for dual-authorization',
        targetScope: `Session: ${session?.fileName || 'Property_SOV_Jan.xlsx'}`,
        sessionFile: session?.fileName || 'Property_SOV_Jan.xlsx',
        sessionId: sessionId,
        status: 'awaiting',
        evidenceHash: 'sha256:7f9ba4e1...89c2',
        nonce: `0x${Math.floor(Math.random() * 0xffffff).toString(16)}`,
      };

      return {
        sessions: updated,
        auditEvents: [newEvent, ...state.auditEvents],
      };
    });
  },

  managerApproveSession: (sessionId: string, managerName: string) => {
    set((state) => {
      const updated = state.sessions.map((s) =>
        s.id === sessionId
          ? {
              ...s,
              status: 'approved' as SessionWorkflowStatus,
              approvedAt: 'Today, 10:47 AM',
            }
          : s
      );

      const session = state.sessions.find((s) => s.id === sessionId);
      const newEvent: AuditEventItem = {
        id: `EVT-${Date.now().toString().slice(-4)}`,
        timestamp: 'Today, 10:47 AM',
        date: 'Oct 2, 2026',
        actor: managerName || 'S. Reynolds',
        actorType: 'manager',
        actorTitle: 'Manager, Risk Underwriting',
        action: 'Authorized & Approved session export',
        targetScope: `Session: ${session?.fileName || 'Property_SOV_Jan.xlsx'}`,
        sessionFile: session?.fileName || 'Property_SOV_Jan.xlsx',
        sessionId: sessionId,
        status: 'approved',
        evidenceHash: 'sha256:8f4a99c2...4110',
        humanDecision: `${managerName || 'S. Reynolds'} verified all 17 schema transformations and approved file release.`,
        resultingRule: 'Cleaned SOV export unlocked (.xlsx / .csv)',
        nonce: `0x${Math.floor(Math.random() * 0xffffff).toString(16)}`,
      };

      return {
        sessions: updated,
        auditEvents: [newEvent, ...state.auditEvents],
      };
    });
  },

  managerReturnSession: (sessionId: string, remarks: string, managerName: string) => {
    set((state) => {
      const updated = state.sessions.map((s) =>
        s.id === sessionId
          ? {
              ...s,
              status: 'returned' as SessionWorkflowStatus,
              returnedAt: 'Today, 10:48 AM',
              returnRemarks: remarks || 'Storeys reconciliation required on Row 142. Please verify with municipal permit filings.',
            }
          : s
      );

      const session = state.sessions.find((s) => s.id === sessionId);
      const newEvent: AuditEventItem = {
        id: `EVT-${Date.now().toString().slice(-4)}`,
        timestamp: 'Today, 10:48 AM',
        date: 'Oct 2, 2026',
        actor: managerName || 'S. Reynolds',
        actorType: 'manager',
        actorTitle: 'Manager, Risk Underwriting',
        action: `Returned session for worker revision: "${remarks || 'Reconciliation required'}"`,
        targetScope: `Session: ${session?.fileName || 'Property_SOV_Jan.xlsx'}`,
        sessionFile: session?.fileName || 'Property_SOV_Jan.xlsx',
        sessionId: sessionId,
        status: 'returned',
        evidenceHash: 'sha256:9f40e1b7...219c',
        humanDecision: `Returned to ${session?.workerName || 'Aarav Sharma'} for correction.`,
        nonce: `0x${Math.floor(Math.random() * 0xffffff).toString(16)}`,
      };

      return {
        sessions: updated,
        auditEvents: [newEvent, ...state.auditEvents],
      };
    });
  },

  setSessionStatus: (sessionId: string, status: SessionWorkflowStatus) => {
    set((state) => ({
      sessions: state.sessions.map((s) => (s.id === sessionId ? { ...s, status } : s)),
    }));
  },

  auditEvents: INITIAL_AUDIT_EVENTS,

  addAuditEvent: (event: Omit<AuditEventItem, 'id'>) => {
    const newEvent: AuditEventItem = {
      ...event,
      id: `EVT-${Date.now().toString().slice(-4)}`,
    };
    set((state) => ({
      auditEvents: [newEvent, ...state.auditEvents],
    }));
  },
}), {
  name: 'sovia-demo-workflow',
  partialize: (state) => ({
    sessions: state.sessions,
    activeSessionId: state.activeSessionId,
    selectedSheet: state.selectedSheet,
    mappings: state.mappings,
    selectedMappingId: state.selectedMappingId,
    dqIssues: state.dqIssues,
    transformations: state.transformations,
    auditEvents: state.auditEvents,
  }),
}));
