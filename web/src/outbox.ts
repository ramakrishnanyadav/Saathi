/**
 * Offline-first IndexedDB Outbox Manager for SAATH.
 * Persists messages locally when network is unavailable and synchronizes atomically on reconnect.
 */

export interface OutboxItem {
  client_uuid: string;
  text: string;
  author_id: string;
  house_id: string;
  created_at: number;
}

const DB_NAME = 'saath_offline_db';
const STORE_NAME = 'outbox_queue';
const DB_VERSION = 1;

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.indexedDB) {
      reject(new Error('IndexedDB not supported'));
      return;
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'client_uuid' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function queueOfflineMessage(item: OutboxItem): Promise<void> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const req = store.put(item);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  } catch (err) {
    console.warn('Failed to queue offline message in IndexedDB:', err);
  }
}

export async function getPendingOutboxItems(): Promise<OutboxItem[]> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result as OutboxItem[]);
      req.onerror = () => reject(req.error);
    });
  } catch (err) {
    console.warn('Failed to read outbox items:', err);
    return [];
  }
}

export async function clearOutboxItem(client_uuid: string): Promise<void> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const req = store.delete(client_uuid);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  } catch (err) {
    console.warn('Failed to clear outbox item:', err);
  }
}

export async function flushOutbox(houseId: string): Promise<number> {
  const items = await getPendingOutboxItems();
  if (items.length === 0) return 0;

  const houseItems = items.filter((i) => i.house_id === houseId);
  if (houseItems.length === 0) return 0;

  try {
    const payload = {
      items: houseItems.map((i) => ({
        client_uuid: i.client_uuid,
        text: i.text,
        author_id: i.author_id,
        created_at: i.created_at,
      })),
    };

    const res = await fetch('/api/v1/sync/outbox', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-House-Id': houseId,
      },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      const data = await res.json();
      let appliedCount = 0;
      if (data.items && Array.isArray(data.items)) {
        for (const resItem of data.items) {
          if (resItem.status === 'applied' || resItem.status === 'duplicate') {
            await clearOutboxItem(resItem.client_uuid);
            if (resItem.status === 'applied') appliedCount++;
          } else if (resItem.status === 'failed') {
            // Retain failed items for retry or user resolution
            console.warn(`Outbox item ${resItem.client_uuid} failed on server:`, resItem.error);
          }
        }
        return appliedCount;
      }
    }
  } catch (err) {
    console.warn('Outbox flush failed, will retry on next reconnect:', err);
  }
  return 0;
}
