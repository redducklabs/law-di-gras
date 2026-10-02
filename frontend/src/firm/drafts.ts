// One-click drafts for a Next step. Generic templates filled from the step + matter; nothing is
// sent and nothing is written to Clio. The attorney edits, then copies or opens in their mail app.
import type { Dashboard } from '../api/types'
import { chipLabel, daysFromToday, fmtDate, parseDate } from '../components'
import type { Step } from './stepRules'

export interface Draft {
  action: string        // button label
  audience: string      // who it is for, shown in the drawer
  subject: string
  body: string
}

const firstName = (full: string) => {
  const s = full.includes(',') ? full.split(',')[1] : full
  return s.trim().split(/\s+/)[0] ?? full
}

const sourceLine = (s: Step) => (s.citations[0] ? `Ref: ${chipLabel(s.citations[0])}` : '')

export function draftFor(s: Step, d: Dashboard): Draft {
  const m = d.matter
  const re = `${m.title} (${m.display_number})`
  const n = daysFromToday(s.date)

  if (s.kind === 'waiting') {
    const since = s.date && n != null
      ? n < 0 ? ` Our file shows this outstanding since ${fmtDate(s.date, true)}.` : ` It is due ${fmtDate(s.date, true)}.`
      : ''
    return {
      action: 'Draft follow-up',
      audience: s.waitingOn ?? 'Outside party',
      subject: `Follow-up: ${s.title} — ${m.client_name}`,
      body: [
        `Hello${s.waitingOn ? ` ${s.waitingOn}` : ''},`,
        '',
        `We represent ${m.client_name} and are following up on the item below.${since}`,
        '',
        `  • ${s.title}`,
        '',
        'Please send it at your earliest convenience, or reply with the date we can expect it. If you need anything from our office (authorization, payment, or a records request form), let us know.',
        '',
        'Thank you,',
        '[Your name]',
        '[Firm] · [Phone]',
      ].join('\n'),
    }
  }

  if (s.kind === 'client') {
    return {
      action: 'Draft client check-in',
      audience: m.client_name,
      subject: `Checking in on your case`,
      body: [
        `Hi ${firstName(m.client_name)},`,
        '',
        'Checking in to see how you are feeling and how treatment is going.',
        '',
        'Could you let us know:',
        '  • Any new doctors, therapists, or appointments since we last spoke',
        '  • Any new bills, letters, or calls from insurance companies',
        '  • How you are doing day to day (work, sleep, activities)',
        '',
        'Reply here or call us any time at [Phone].',
        '',
        '[Your name]',
      ].join('\n'),
    }
  }

  // overdue / upcoming → internal reminder to the owner
  const status = s.kind === 'overdue' ? 'Overdue' : `Due ${fmtDate(s.date)}`
  return {
    action: 'Draft reminder',
    audience: s.owner ? `${s.owner} (internal)` : 'Case team (internal)',
    subject: `${status}: ${s.title} — ${re}`,
    body: [
      `${s.owner ? `${s.owner}, q` : 'Q'}uick reminder on ${re}:`,
      '',
      `  • ${s.title} — ${s.why.toLowerCase()}`,
      ...(sourceLine(s) ? [`    ${sourceLine(s)}`] : []),
      '',
      s.kind === 'overdue'
        ? 'Can you confirm where this stands and the new target date?'
        : 'Can you confirm this is on track?',
      '',
      'Thanks',
    ].join('\n'),
  }
}

export const mailtoHref = (dr: Draft) =>
  `mailto:?subject=${encodeURIComponent(dr.subject)}&body=${encodeURIComponent(dr.body)}`

/** All-day calendar file for a step dated today or later. Built locally; the browser saves it. */
export function icsFor(s: Step, d: Dashboard): string | null {
  const date = parseDate(s.date)
  if (!date || (daysFromToday(s.date) ?? -1) < 0) return null
  const ymd = (x: Date) => `${x.getFullYear()}${String(x.getMonth() + 1).padStart(2, '0')}${String(x.getDate()).padStart(2, '0')}`
  const next = new Date(date.getTime() + 86_400_000)
  const esc = (t: string) => t.replace(/[\\,;]/g, m => `\\${m}`).replace(/\n/g, '\\n')
  return [
    'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Case Brief//EN', 'BEGIN:VEVENT',
    `UID:${ymd(date)}-${Math.abs(hash(s.title + d.matter.id))}@casebrief`,
    `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, '').slice(0, 15)}Z`,
    `DTSTART;VALUE=DATE:${ymd(date)}`, `DTEND;VALUE=DATE:${ymd(next)}`,
    `SUMMARY:${esc(`${s.title} — ${d.matter.display_number}`)}`,
    `DESCRIPTION:${esc(`${d.matter.title}\n${s.why}\n${sourceLine(s)}`)}`,
    'END:VEVENT', 'END:VCALENDAR',
  ].join('\r\n')
}

function hash(t: string) {
  let h = 0
  for (let i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) | 0
  return h
}
