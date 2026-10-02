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
  headline: { status_line: string; stage: string; bullets: Fact[] }
  timeline: TimelineEvent[]
  kpis: { specials?: Fact | null; coverage: Fact[]; case_value?: Fact | null; firm_spent?: Fact | null }
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
  timeline?: TimelineEvent[] | null
  documents?: { source_id: string; title: string }[] | null
}
