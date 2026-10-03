import React, { useState } from 'react';

export default function App() {
  const [activeStep, setActiveStep] = useState(1);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('idle');

  const steps = [
    { id: 1, name: 'Upload & Sheet Intelligence', agent: 'Agent 1' },
    { id: 2, name: 'Schema Mapping (17 Fields)', agent: 'Agent 2' },
    { id: 3, name: 'Quality & Recommendations', agent: 'Agent 3' },
    { id: 4, name: 'Human Review Gate', agent: 'Human Review' },
    { id: 5, name: 'Transformation & Export', agent: 'Agent 4' },
  ];

  return (
    <div className="container">
      {/* Header */}
      <header style={{ marginBottom: '2.5rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: '2.25rem', marginBottom: '0.5rem', background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          SOV Intelligence & Cleansing System
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem' }}>
          Commercial Insurance Statement of Values (SOV) Multi-Agent Cleansing Pipeline
        </p>
      </header>

      {/* Stepper Navigation */}
      <nav style={{ display: 'flex', gap: '0.75rem', marginBottom: '2rem', flexWrap: 'wrap' }} aria-label="Pipeline Steps">
        {steps.map((step) => (
          <button
            key={step.id}
            id={`step-tab-${step.id}`}
            onClick={() => setActiveStep(step.id)}
            className={`btn ${activeStep === step.id ? 'btn-primary' : 'btn-secondary'}`}
            style={{ flex: 1, minWidth: '180px', padding: '0.85rem' }}
          >
            <span style={{ opacity: 0.75, fontSize: '0.8rem' }}>{step.agent}:</span>
            <span>{step.name}</span>
          </button>
        ))}
      </nav>

      {/* Main Content Area */}
      <main className="glass-card">
        {activeStep === 1 && (
          <section id="section-upload">
            <h2 style={{ marginBottom: '1rem' }}>Step 1: Upload SOV Workbook & Sheet Intelligence</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Upload an unstandardized property schedule (.xlsx, .xls). Agent 1 will analyze workbook sheets and detect table headers.
            </p>
            <div style={{ border: '2px dashed var(--border-color)', borderRadius: 'var(--radius-md)', padding: '3rem', textAlign: 'center' }}>
              <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>Drag and drop your SOV spreadsheet here, or browse files</p>
              <button id="btn-browse-file" className="btn btn-primary">Browse Files</button>
            </div>
          </section>
        )}

        {activeStep === 2 && (
          <section id="section-schema">
            <h2 style={{ marginBottom: '1rem' }}>Step 2: Schema Mapping (17 Canonical Fields)</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Agent 2 maps raw column headers to the 17 standard property insurance underwriting fields.
            </p>
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
              <p style={{ color: 'var(--text-muted)' }}>Schema mapping matrix will display here once file is ingested.</p>
            </div>
          </section>
        )}

        {activeStep === 3 && (
          <section id="section-quality">
            <h2 style={{ marginBottom: '1rem' }}>Step 3: Data Quality & Proposed Recommendations</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Agent 3 detects formatting anomalies, missing data, and invalid domain codes, generating value fixes.
            </p>
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
              <p style={{ color: 'var(--text-muted)' }}>Detected quality issues and actionable recommendations list will appear here.</p>
            </div>
          </section>
        )}

        {activeStep === 4 && (
          <section id="section-review">
            <h2 style={{ marginBottom: '1rem' }}>Step 4: Human-in-the-Loop Review Gate</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Underwriters and risk engineers review proposed fixes. Decisions supported: <strong>Approve</strong>, <strong>Reject</strong>, or <strong>Edit</strong>.
            </p>
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
              <p style={{ color: 'var(--text-muted)' }}>Interactive approval grid will appear here for human sign-off.</p>
            </div>
          </section>
        )}

        {activeStep === 5 && (
          <section id="section-transform">
            <h2 style={{ marginBottom: '1rem' }}>Step 5: Controlled Transformation & Audit Trail</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Agent 4 executes only approved changes, recording an immutable audit trail and generating the standardized SOV.
            </p>
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
              <p style={{ color: 'var(--text-muted)' }}>Download buttons and audit trail timeline will render here.</p>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
