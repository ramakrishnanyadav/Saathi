import { useUIStore } from './store';

const HOUSE_ID = 'h-demo';

export function getHeaders(): Record<string, string> {
  const memberId = useUIStore.getState().actingMemberId || 'm-1';
  return {
    'Content-Type': 'application/json',
    'X-House-Id': HOUSE_ID,
    'X-Member-Id': memberId,
  };
}

export async function apiFetch(path: string, options?: RequestInit) {
  const res = await fetch(path, {
    ...options,
    headers: {
      ...getHeaders(),
      ...(options?.headers || {}),
    },
  });
  return res;
}

export async function getAttention() {
  const res = await apiFetch('/api/v1/attention');
  if (!res.ok) throw new Error('Could not load attention items');
  return res.json();
}

export async function getHistory() {
  const res = await apiFetch('/api/v1/history');
  if (!res.ok) throw new Error('Could not load history');
  return res.json();
}

export async function getMembers() {
  const res = await apiFetch('/api/v1/house/members');
  if (!res.ok) throw new Error('Could not load house members');
  return res.json();
}

export async function getReflection() {
  const res = await apiFetch('/api/v1/reflection');
  if (!res.ok) throw new Error('Could not load weekly reflection');
  return res.json();
}

export async function getExpenses(status?: 'pending' | 'confirmed') {
  const query = status ? `?status=${status}` : '';
  const res = await apiFetch(`/api/v1/expenses${query}`);
  if (!res.ok) return { expenses: [], total: 0 };
  return res.json();
}

export async function getCommitment(id: string) {
  const res = await apiFetch(`/api/v1/commitments/${id}`);
  if (!res.ok) throw new Error('Could not load commitment details');
  return res.json();
}

export async function replyCommitment(id: string, intent: 'not_yet' | 'rescheduled' | 'done' | 'cancelled', newDue?: number | string) {
  const res = await apiFetch(`/api/v1/commitments/${id}/reply`, {
    method: 'POST',
    body: JSON.stringify({ intent, new_due: newDue }),
  });
  if (!res.ok) throw new Error('Failed to update commitment');
  return res.json();
}

export async function cancelCommitment(id: string) {
  const res = await apiFetch(`/api/v1/commitments/${id}/cancel`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error('Failed to cancel commitment');
  return res.json();
}

export async function markCommitmentDone(id: string) {
  const res = await apiFetch(`/api/v1/commitments/${id}/done`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error('Failed to mark commitment done');
  return res.json();
}

export async function snoozeCommitment(id: string, durationHours = 24) {
  const res = await apiFetch(`/api/v1/commitments/${id}/snooze`, {
    method: 'POST',
    body: JSON.stringify({ duration_hours: durationHours }),
  });
  if (!res.ok) throw new Error('Failed to snooze commitment');
  return res.json();
}

export async function rescheduleCommitment(id: string, newDueAt: number) {
  const res = await apiFetch(`/api/v1/commitments/${id}/reschedule`, {
    method: 'POST',
    body: JSON.stringify({ new_due_at: newDueAt }),
  });
  if (!res.ok) throw new Error('Failed to reschedule commitment');
  return res.json();
}

export async function sendMessage(text: string, dedupeKey: string) {
  const memberId = useUIStore.getState().actingMemberId || 'm-1';
  return apiFetch('/api/v1/messages', {
    method: 'POST',
    body: JSON.stringify({ text, author_id: memberId, dedupe_key: dedupeKey }),
  });
}

export async function sendVoiceMessage(file: Blob) {
  const memberId = useUIStore.getState().actingMemberId || 'm-1';
  const formData = new FormData();
  formData.append('file', file);
  formData.append('author_id', memberId);

  const res = await fetch('/api/v1/messages/voice', {
    method: 'POST',
    headers: {
      'X-House-Id': HOUSE_ID,
      'X-Member-Id': memberId,
    },
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Voice upload failed' }));
    throw new Error(err.detail || 'Voice upload failed');
  }
  return res.json();
}

export async function confirmExpense(payload: any) {
  return apiFetch('/api/v1/expenses/confirm', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function draftFollowup(commitmentId: string) {
  return apiFetch(`/api/v1/commitments/${commitmentId}/followup`, {
    method: 'POST',
  });
}

export async function markFollowupOpened(commitmentId: string) {
  return apiFetch(`/api/v1/followups/${commitmentId}/opened`, {
    method: 'POST',
  });
}

export async function markFollowupSent(commitmentId: string) {
  return apiFetch(`/api/v1/followups/${commitmentId}/sent`, {
    method: 'POST',
  });
}

export async function undoEvent(eventId: string) {
  return apiFetch(`/api/v1/events/${eventId}/undo`, {
    method: 'POST',
  });
}

export async function getClock() {
  const res = await apiFetch('/api/v1/clock');
  if (!res.ok) return { now_ms: Date.now(), simulated: false };
  return res.json();
}

export async function advanceDemoClock(hours: number) {
  return apiFetch('/api/v1/demo/clock/advance', {
    method: 'POST',
    body: JSON.stringify({ hours }),
  });
}

export async function getHealthz() {
  const res = await fetch('/healthz');
  return res.ok;
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
