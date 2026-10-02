// Mirror of backend/app/schemas.py. Change both in one `contract:` commit.

export type SourceKind =
  | 'note' | 'communication' | 'task' | 'calendar_entry' | 'expense'
  | 'document' | 'custom_field' | 'contact' | 'matter'

/** Normalized 0..1, top-left origin; page is 1-based. */
export interface Rect { page: number; x0: number; y0: number; x1: number; y1: number }

export interface Citation {
  source_id: string
  source_kind: SourceKind
  source_title: string
  date?: string | null
  page?: number | null
  quote: string
  char_start?: number | null
  char_end?: number | null
  rects: Rect[]
  verified: boolean
}

export interface Fact {
  id: string
  label: string
  value: string
  amount?: number | null
  date?: string | null
  citations: Citation[]
  verified: boolean
}

export interface TimelineEvent {
  date: string
  label: string
  kind: 'incident' | 'treatment' | 'legal' | 'communication' | 'deadline'
  is_future: boolean
  major?: boolean // one of the ~12 milestones worth showing on a compact strip
  citations: Citation[]
}

export interface ActionItem {
  title: string
  due_date?: string | null
  owner?: string | null
  status: 'overdue' | 'upcoming' | 'waiting'
  waiting_on?: string | null
  citations: Citation[]
}

export interface TreatmentLine {
  provider: string
  contact_id?: string | null
  first_visit?: string | null
  last_visit?: string | null
  last_visit_basis?: 'billed_through' | 'records' | null // billed_through: label it "Billed through"
  next_visit?: string | null // next scheduled appointment (treatment ongoing)
  visit_count?: number | null
  billed?: Fact | null
  citations: Citation[]
}

export interface MatterSummary {
  id: string
  display_number: string
  title: string
  client_name: string
  client_photo_url?: string | null
  status: string
  opened_date?: string | null
}

export interface Dashboard {
  matter: MatterSummary
  generated_at: string
  cost_usd: number
  models: string[]
  headline: { status_line: string; stage: string; bullets: Fact[]; status_citations?: Citation[] }
  timeline: TimelineEvent[]
  kpis: { specials?: Fact | null; coverage: Fact[]; case_value?: Fact | null; firm_spent?: Fact | null; liens?: Fact[] }
  actions: ActionItem[]
  last_client_contact?: Fact | null
  injuries: Fact[]
  treatment: TreatmentLine[]
  recent: Fact[]
}

export interface SourceDetail {
  id: string
  kind: SourceKind
  title: string
  date?: string | null
  author?: string | null
  text: string
  page_count?: number | null
  has_file: boolean
  pages: { page_no: number; width: number; height: number; ocr: boolean }[]
}

export interface Passage { citation: Citation; score: number; snippet: string }

/** [n] markers in answer_markdown index citations, 1-based. */
export interface Answer { answer_markdown: string; citations: Citation[] }

export interface Provider { contact_id: string; name: string; role?: string | null }

export interface ShareSections {
  status: boolean
  coverage: boolean
  treatment: boolean
  requests: boolean
  timeline: boolean
  documents: boolean
}

export interface ShareSettings {
  contact_id: string
  sections: ShareSections
  source_ids: string[]
  token?: string | null
  last_viewed_at?: string | null
}

export interface ProviderView {
  matter_title: string
  client_name: string
  provider_name: string
  stage: string
  status_line: string
  case_active: boolean
  last_activity_date?: string | null
  coverage?: Fact[] | null
  requests?: ActionItem[] | null
  treatment?: TreatmentLine[] | null
  liens?: Fact[] | null
  updates?: TimelineEvent[] | null
  updates_since?: string | null
  timeline?: TimelineEvent[] | null
  documents?: { source_id: string; title: string }[] | null
}

// Mirrors firm/aiDraft.ts AiDraftRequest. Template is a structural hint only, never a fact source.
export interface DraftRequest {
  kind?: 'overdue' | 'upcoming' | 'waiting' | 'client' | null
  title?: string | null
  why?: string | null
  owner?: string | null
  waiting_on?: string | null
  date?: string | null
  audience?: string | null
  source_ids?: string[]
  template_subject?: string | null
  template_body?: string | null
  action_index?: number | null
}

export interface DraftSegment {
  text: string
  kind: 'fact' | 'ask' | 'courtesy'
  citations: Citation[]
  verified: boolean
}

// AI draft for attorney review; never sent by the app. Segments join verbatim (text carries its own spacing).
export interface Draft {
  subject: string
  segments: DraftSegment[]
  unverified: string[]
}

// --- Cases page (portfolio) ---
export interface NextDeadline { date: string; label: string }

/** One row on the Cases landing page, sorted by attention_score (desc). */
export interface CaseRow {
  id: string                  // Clio matter id; sample rows use "sample:<n>"
  display_number: string
  title: string
  client_name: string
  stage?: string | null
  sample: boolean             // fictional demo row, NOT from Clio; never clickable
  digested: boolean
  attention_score: number
  attention_reasons: string[]
  overdue_count: number
  waiting_count: number
  next_deadline?: NextDeadline | null
  last_client_contact?: string | null
  specials?: Fact | null
  coverage: Fact[]
  case_value?: Fact | null
  firm_spent?: Fact | null
}

// --- Ask-the-case chat with deeplinks ---
export interface ChatTurn { role: 'user' | 'assistant'; content: string }
export interface ChatRequest { messages: ChatTurn[] }

export type PageSection = 'timeline' | 'next-steps' | 'status' | 'kpis' | 'injuries' | 'treatment' | 'recent'

export interface DeepLink {
  label: string
  kind: 'section' | 'source' | 'timeline' | 'share' | 'route'
  section?: PageSection | null
  citation?: Citation | null
  date?: string | null
  contact_id?: string | null
  path?: string | null
}

/** [n] markers in answer_markdown index citations, 1-based. */
export interface ChatResponse { answer_markdown: string; citations: Citation[]; links: DeepLink[] }

// --- Blind spots: agentic whole-case review ---
export type ReviewCategory = 'conflict' | 'gap' | 'stale' | 'risk' | 'inconsistency' | 'opportunity'

export interface ReviewFinding {
  id: string
  category: ReviewCategory
  severity: 'high' | 'medium' | 'low'
  title: string
  why_it_matters: string
  suggested_next_step: string
  citations: Citation[]
  verified: boolean
}

export interface CaseReview {
  matter_id: string
  generated_at: string
  cost_usd: number
  model: string
  findings: ReviewFinding[]
  /** Present while a new review runs in the background; findings are the last completed review. */
  run?: RunProgress | null
}

// --- Progress for long background jobs (Blind spots review, built-in audit) ---
export interface RunProgress {
  status: 'queued' | 'running' | 'done' | 'failed'
  stage: string
  pct: number
  started_at?: string | null
  finished_at?: string | null
  error?: string | null
}

// --- Built-in audit: runs automatically on every new dashboard or review ---
export interface AuditFlag {
  target: 'dashboard' | 'review'
  item_id: string
  section: string
  severity: 'critical' | 'major' | 'minor'
  check: string
  note: string
  citations: Citation[]
}

export interface AuditReport {
  matter_id: string
  target: 'dashboard' | 'review'
  target_hash: string
  run: RunProgress
  items_checked: number
  flags: AuditFlag[]
  cost_usd: number
}
