export type Role = 'worker' | 'manager';

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  avatar: string;
  title: string;
}

export type SessionWorkflowStatus = 'processing' | 'ready' | 'awaiting' | 'approved' | 'returned';

export interface SOVSession {
  id: string;
  fileName: string;
  fileSize: string;
  sheetCount: number;
  rowCount: number;
  columnCount: number;
  status: SessionWorkflowStatus;
  workerName: string;
  workerAvatar: string;
  workerId: string;
  updatedAt: string;
  submittedAt?: string;
  approvedAt?: string;
  returnedAt?: string;
  returnRemarks?: string;
  targetSheet: string;
  confidence: number;
  hash: string;
}

export interface MappingField {
  id: number;
  sourceField: string;
  targetCanonical: string;
  confidence: number;
  status: 'accepted' | 'proposed' | 'needs_review' | 'low_confidence' | 'unmapped';
  sampleValues: string[];
  dataType: string;
  reasoning: string;
}

export interface DQIssue {
  id: number;
  title: string;
  description: string;
  severity: 'critical' | 'warning' | 'info';
  status: 'pending' | 'resolved' | 'dismissed';
  affectedRows: string;
  category: string;
  suggestedFix: string;
  resolution?: string;
}

export interface TransformationRule {
  id: number;
  title: string;
  ruleCode: string;
  description: string;
  applied: boolean;
  decision: string;
}

export interface AuditEventItem {
  id: string;
  timestamp: string;
  date: string;
  actor: string;
  actorType: 'ai' | 'worker' | 'manager';
  actorTitle: string;
  action: string;
  targetScope: string;
  sessionFile: string;
  sessionId: string;
  status: 'approved' | 'awaiting' | 'flagged' | 'applied' | 'returned' | 'signed';
  evidenceHash: string;
  aiRecommendation?: string;
  humanDecision?: string;
  resultingRule?: string;
  nonce?: string;
}
