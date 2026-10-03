// API helper — all calls go through here
// SQLite is authoritative; React state is presentation only.

const HOUSE_ID = 'h-demo';
const MEMBER_ID = 'm-1';

function headers(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-House-Id': HOUSE_ID,
    'X-Member-Id': MEMBER_ID,
  };
}

export async function apiFetch(path: string, options?: RequestInit) {
  const res = await fetch(path, {
    ...options,
    headers: {
      ...headers(),
      ...(options?.headers || {}),
    },
  });
  return res;
}

export async function getAttention() {
  const res = await apiFetch('/api/v1/attention');
  if (!res.ok) throw new Error('Could not load items needing attention');
  return res.json();
}

export async function getHistory() {
  const res = await apiFetch('/api/v1/history');
  if (!res.ok) throw new Error('Could not load household history');
  return res.json();
}

export async function getMembers() {
  const res = await apiFetch('/api/v1/house/members');
  if (!res.ok) throw new Error('Could not load household members');
  return res.json();
}

export async function getReflection() {
  const res = await apiFetch('/api/v1/reflection');
  if (!res.ok) throw new Error('Could not load weekly summary');
  return res.json();
}

export async function sendMessage(text: string, dedupeKey: string) {
  const res = await apiFetch('/api/v1/messages', {
    method: 'POST',
    body: JSON.stringify({ text, author_id: MEMBER_ID, dedupe_key: dedupeKey }),
  });
  return res;
}

export async function confirmExpense(payload: any) {
  const res = await apiFetch('/api/v1/expenses/confirm', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  return res;
}

export async function draftFollowup(commitmentId: string) {
  const res = await apiFetch(`/api/v1/commitments/${commitmentId}/followup`, {
    method: 'POST',
  });
  return res;
}

export async function markFollowupOpened(commitmentId: string) {
  return apiFetch(`/api/v1/followups/${commitmentId}/opened`, { method: 'POST' });
}

export async function markFollowupSent(commitmentId: string) {
  return apiFetch(`/api/v1/followups/${commitmentId}/sent`, { method: 'POST' });
}

export async function undoEvent(eventId: string) {
  return apiFetch(`/api/v1/events/${eventId}/undo`, { method: 'POST' });
}

export async function advanceDemoClock(hours: number) {
  return apiFetch('/api/v1/demo/clock/advance', {
    method: 'POST',
    body: JSON.stringify({ hours }),
  });
}

export function formatRupees(paise: number): string {
  const rs = paise / 100;
  return '₹' + rs.toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

export function formatDate(ms?: number | null): string {
  if (!ms) return '';
  const d = new Date(ms);
  const now = new Date();
  const diff = d.getTime() - now.getTime();
  const days = Math.round(diff / 86400000);
  if (days === 0) return 'Today';
  if (days === 1) return 'Tomorrow';
  if (days === -1) return 'Yesterday';
  if (days > 1 && days <= 7) return `In ${days} days`;
  if (days < -1 && days >= -7) return `${Math.abs(days)} days ago`;
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

export function timeAgo(ms: number): string {
  const diff = Date.now() - ms;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days === 1) return 'Yesterday';
  if (days < 7) return `${days} days ago`;
  return new Date(ms).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

export function eventTypeToHuman(type: string): string {
  const map: Record<string, string> = {
    commitment_created:  'Promise made',
    commitment_updated:  'Promise updated',
    issue_reported:      'Problem reported',
    expense_created:     'Expense recorded',
    expense_confirmed:   'Expense confirmed',
    supply_depleted:     'Running low',
    supply_restocked:    'Restocked',
    action_taken:        'Action taken',
    followup_drafted:    'Check-in drafted',
    followup_opened:     'Reached out',
    followup_sent:       'Check-in sent',
    note_recorded:       'Note added',
    event_superseded:    'Undone',
  };
  return map[type] || type.replace(/_/g, ' ');
}

export { HOUSE_ID, MEMBER_ID };
