// FICTIONAL design fixture ("Doe v. Example"). Invented content for layout work only.
// Not Sapini, not from Clio. Delete src/dev/ before 3 PM once live data flows.
import type { Citation, Dashboard, Fact } from '../api/types'

const cite = (
  source_id: string, source_title: string, quote: string,
  opts: Partial<Citation> = {},
): Citation => ({
  source_id, source_kind: 'document', source_title, quote, rects: [], verified: true, ...opts,
})

const fact = (id: string, label: string, value: string, citations: Citation[], extra: Partial<Fact> = {}): Fact => ({
  id, label, value, citations, verified: citations.every(c => c.verified), ...extra,
})

const police = (p: number, q: string) => cite('document:1', 'Police Report', q, { page: p, date: '2026-01-14' })
const er = (p: number, q: string) => cite('document:2', 'ER Record — Example General', q, { page: p, date: '2026-01-14' })
const mri = (p: number, q: string) => cite('document:3', 'MRI Lumbar Report', q, { page: p, date: '2026-02-20' })
const pt = (p: number, q: string) => cite('document:4', 'PT Ledger — Sample Rehab', q, { page: p })
const dec = (p: number, q: string) => cite('document:5', 'Declarations Page', q, { page: p })
const note = (id: string, title: string, date: string, q: string) =>
  cite(`note:${id}`, title, q, { source_kind: 'note', date })
const task = (id: string, title: string, q: string) => cite(`task:${id}`, title, q, { source_kind: 'task' })

export const fixture: Dashboard = {
  matter: {
    id: 'demo-1',
    display_number: '00042-Doe',
    title: 'Doe v. Example Freight LLC',
    client_name: 'Jordan Doe',
    client_photo_url: null,
    status: 'Open',
    opened_date: '2026-01-20',
  },
  generated_at: '2026-10-02T10:42:00-07:00',
  cost_usd: 1.84,
  models: ['claude-opus-5-5', 'claude-sonnet-5-5', 'claude-haiku-4-5'],
  headline: {
    stage: 'Pre-demand',
    status_line:
      'Treatment is winding down; the demand package is blocked on two outstanding provider bills and the final PT discharge summary.',
    bullets: [
      fact('h1', 'Liability', 'Defendant driver cited for unsafe lane change; rear-impact collision.', [police(2, 'Driver of Vehicle 2 cited for unsafe lane change')]),
      fact('h2', 'Treatment', 'Client completed 18 of 24 prescribed PT visits; MRI shows L4–L5 disc protrusion.', [pt(1, 'Visits completed: 18'), mri(1, 'L4-L5 broad-based disc protrusion')]),
      fact('h3', 'Coverage', 'Defendant carrier limits are $250,000; UIM not yet confirmed.', [dec(1, 'Bodily Injury Each Person $250,000')]),
      fact('h4', 'Client', 'Client reports ongoing low-back pain at last check-in.', [note('n7', 'Client call', '2026-09-24', 'still having lower back pain most days')], { verified: false }),
    ],
  },
  timeline: [
    { date: '2026-01-14', label: 'Collision', kind: 'incident', is_future: false, citations: [police(1, 'Date of crash: 01/14/2026')] },
    { date: '2026-01-14', label: 'ER visit', kind: 'treatment', is_future: false, citations: [er(1, 'Arrived via EMS')] },
    { date: '2026-01-20', label: 'Retained', kind: 'legal', is_future: false, citations: [note('n1', 'Intake', '2026-01-20', 'Signed retainer')] },
    { date: '2026-02-20', label: 'MRI lumbar', kind: 'treatment', is_future: false, citations: [mri(1, 'MRI lumbar spine without contrast')] },
    { date: '2026-03-02', label: 'PT starts', kind: 'treatment', is_future: false, citations: [pt(1, 'Initial evaluation 03/02/2026')] },
    { date: '2026-05-11', label: 'LOR to carrier', kind: 'communication', is_future: false, citations: [note('n3', 'Letter of representation', '2026-05-11', 'letter of representation sent')] },
    { date: '2026-09-24', label: 'Client check-in', kind: 'communication', is_future: false, citations: [note('n7', 'Client call', '2026-09-24', 'still having lower back pain')] },
    { date: '2026-10-15', label: 'PT discharge', kind: 'treatment', is_future: true, citations: [task('t4', 'Follow up PT discharge', 'Expected discharge 10/15')] },
    { date: '2026-11-30', label: 'Demand target', kind: 'deadline', is_future: true, citations: [task('t5', 'Send demand', 'Target 11/30')] },
    { date: '2028-01-14', label: 'SOL', kind: 'deadline', is_future: true, citations: [note('n1', 'Intake', '2026-01-20', 'SOL 01/14/2028')] },
  ],
  kpis: {
    specials: fact('k1', 'Medical specials', '$48,620', [er(3, 'Total charges $6,410.00'), pt(2, 'Balance $14,210.00')], { amount: 48620 }),
    coverage: [
      fact('k2', 'Defendant BI limits', '$250,000 / $500,000', [dec(1, 'Bodily Injury $250,000 / $500,000')], { amount: 250000 }),
      fact('k3', 'Client UIM', 'Unconfirmed', [note('n4', 'UIM inquiry', '2026-06-02', 'awaiting UIM dec page')], { verified: false }),
    ],
    case_value: fact('k4', 'Case value (draft)', '$140k – $210k', [er(3, 'Total charges'), dec(1, 'Bodily Injury')], { verified: false }),
    firm_spent: fact('k5', 'Firm costs advanced', '$2,315', [cite('expense:9', 'Records fees', 'Records retrieval', { source_kind: 'expense' })], { amount: 2315 }),
  },
  actions: [
    { title: 'Request itemized bill from Sample Rehab', due_date: '2026-09-28', owner: 'Paralegal', status: 'overdue', citations: [task('t2', 'Itemized bill request', 'Request itemized bill')] },
    { title: 'Calendar: client deposition prep', due_date: '2026-10-09', owner: 'Attorney', status: 'upcoming', citations: [task('t3', 'Depo prep', 'prep session')] },
    { title: 'PT discharge summary', due_date: '2026-10-15', status: 'upcoming', citations: [task('t4', 'Follow up PT discharge', 'Expected discharge 10/15')] },
    { title: 'Records from Example Ortho', status: 'waiting', waiting_on: 'Example Ortho', due_date: '2026-09-10', citations: [task('t6', 'Ortho records', 'records requested 09/10')] },
    { title: 'UIM declarations page', status: 'waiting', waiting_on: 'Client carrier', citations: [note('n4', 'UIM inquiry', '2026-06-02', 'awaiting UIM dec page')] },
  ],
  last_client_contact: fact('c1', 'Last client contact', 'Phone call · 8 days ago', [note('n7', 'Client call', '2026-09-24', 'still having lower back pain most days')], { date: '2026-09-24' }),
  injuries: [
    fact('i1', 'Lumbar', 'L4–L5 disc protrusion', [mri(1, 'L4-L5 broad-based disc protrusion')]),
    fact('i2', 'Cervical', 'Cervical strain', [er(2, 'Dx: cervical strain')]),
    fact('i3', 'Shoulder', 'Left shoulder contusion', [er(2, 'contusion of left shoulder')]),
    fact('i4', 'Headaches', 'Post-traumatic headaches', [note('n5', 'Client call', '2026-04-02', 'headaches since the crash')], { verified: false }),
  ],
  treatment: [
    { provider: 'Example General ER', first_visit: '2026-01-14', last_visit: '2026-01-14', visit_count: 1,
      billed: fact('b1', 'Billed', '$6,410', [er(3, 'Total charges $6,410.00')], { amount: 6410 }), citations: [er(1, 'Arrived via EMS')] },
    { provider: 'Example Imaging', first_visit: '2026-02-20', last_visit: '2026-02-20', visit_count: 1,
      billed: fact('b2', 'Billed', '$3,200', [mri(2, 'Amount due $3,200.00')], { amount: 3200 }), citations: [mri(1, 'MRI lumbar spine')] },
    { provider: 'Sample Rehab (PT)', first_visit: '2026-03-02', last_visit: '2026-09-26', visit_count: 18,
      billed: fact('b3', 'Billed', '$14,210', [pt(2, 'Balance $14,210.00')], { amount: 14210 }), citations: [pt(1, 'Visits completed: 18')] },
    { provider: 'Example Ortho', first_visit: '2026-04-15', last_visit: '2026-08-19', visit_count: 4,
      billed: null, citations: [note('n6', 'Ortho visit', '2026-04-15', 'ortho consult')] },
  ],
  recent: [],
}
