import { openDB, DBSchema } from 'idb';
import { getHeaders } from './api';

export interface OutboxItem {
  client_uuid: string;
  kind: string;
  payload: any;
  text: string;
  status: 'queued' | 'syncing' | 'done' | 'failed';
  error?: string;
  timestamp: number;
}

interface OutboxDB extends DBSchema {
  outbox: {
    key: string;
    value: OutboxItem;
  };
}

const DB_NAME = 'saath-outbox-v7-db';

export async function getOutboxDB() {
  return openDB<OutboxDB>(DB_NAME, 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains('outbox')) {
        db.createObjectStore('outbox', { keyPath: 'client_uuid' });
      }
    },
  });
}

export async function queueOfflineMessage(text: string, kind = 'message', payload: any = {}): Promise<string> {
  const db = await getOutboxDB();
  const client_uuid = `msg-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
  const item: OutboxItem = {
    client_uuid,
    kind,
    payload,
    text,
    status: 'queued',
    timestamp: Date.now(),
  };
  await db.put('outbox', item);
  return client_uuid;
}

export async function getQueuedItems(): Promise<OutboxItem[]> {
  const db = await getOutboxDB();
  return db.getAll('outbox');
}

export async function clearOutboxItem(client_uuid: string) {
  const db = await getOutboxDB();
  return db.delete('outbox', client_uuid);
}

export async function flushOutbox(): Promise<{ synced: number; total: number }> {
  const items = await getQueuedItems();
  const queued = items.filter((i) => i.status === 'queued' || i.status === 'failed');
  if (queued.length === 0) return { synced: 0, total: items.length };

  const db = await getOutboxDB();
  for (const item of queued) {
    item.status = 'syncing';
    await db.put('outbox', item);
  }

  try {
    const payloadItems = queued.map((i) => ({
      client_uuid: i.client_uuid,
      text: i.text,
      occurred_at: i.timestamp,
    }));

    const res = await fetch('/api/v1/sync/outbox', {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ items: payloadItems }),
    });

    if (res.ok) {
      const data = await res.json();
      const resultsMap = new Map<string, any>();
      for (const r of data.items || []) {
        resultsMap.set(r.client_uuid, r);
      }

      let synced = 0;
      for (const item of queued) {
        const result = resultsMap.get(item.client_uuid);
        if (result && (result.status === 'applied' || result.status === 'duplicate')) {
          await clearOutboxItem(item.client_uuid);
          synced++;
        } else {
          item.status = 'failed';
          item.error = result?.error || 'Sync failed';
          await db.put('outbox', item);
        }
      }
      return { synced, total: queued.length };
    } else {
      for (const item of queued) {
        item.status = 'failed';
        item.error = `HTTP ${res.status}`;
        await db.put('outbox', item);
      }
      return { synced: 0, total: queued.length };
    }
  } catch (err: any) {
    for (const item of queued) {
      item.status = 'failed';
      item.error = err?.message || 'Network error';
      await db.put('outbox', item);
    }
    return { synced: 0, total: queued.length };
  }
}

