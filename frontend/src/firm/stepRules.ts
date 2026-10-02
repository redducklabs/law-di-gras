// Turn the Dashboard's actions into one ranked, explained list: what to do next and why.
// Rules only (no case content): overdue first, then soonest due, then stale client contact,
// then things we are waiting on others for.
import type { ActionItem, Citation, Dashboard } from '../api/types'
import { daysFromToday, fmtDate, relDays, type Tone } from '../components'

export interface Step {
  title: string
  why: string
  tone: Tone
  group: 'do' | 'waiting'
  owner?: string | null
  date?: string | null
  citations: Citation[]
}

/** Client contact older than this many days becomes a step. */
export const CLIENT_CONTACT_STALE_DAYS = 30

function fromAction(a: ActionItem): Step & { sort: number } {
  const n = daysFromToday(a.due_date)
  const base = { title: a.title, owner: a.owner, date: a.due_date, citations: a.citations }
  if (a.status === 'overdue') {
    const late = n != null && n < 0 ? -n : null
    return { ...base, group: 'do', tone: 'danger', sort: -1000 + (n ?? 0),
      why: late ? `Overdue by ${late} day${late === 1 ? '' : 's'}` : 'Overdue' }
  }
  if (a.status === 'upcoming') {
    return { ...base, group: 'do', tone: n != null && n <= 7 ? 'warn' : 'brand', sort: n ?? 500,
      why: n == null ? 'Upcoming' : `Due ${relDays(n)}` }
  }
  const who = a.waiting_on ? `Waiting on ${a.waiting_on}` : 'Waiting on others'
  return { ...base, group: 'waiting', tone: 'neutral', sort: 2000 + (n ?? 0),
    why: a.due_date ? `${who} · ${fmtDate(a.due_date)}${n != null ? ` (${relDays(n)})` : ''}` : who }
}

export function buildNextSteps(d: Dashboard): Step[] {
  const steps = d.actions.map(fromAction)
  const c = d.last_client_contact
  const age = c?.date ? daysFromToday(c.date) : null
  if (c && age != null && -age >= CLIENT_CONTACT_STALE_DAYS) {
    steps.push({ title: 'Check in with the client', group: 'do', tone: 'warn', sort: 400,
      why: `No client contact in ${-age} days`, date: c.date, citations: c.citations })
  }
  return steps.sort((a, b) => a.sort - b.sort).map(({ sort: _s, ...s }) => s)
}
