// Shared TypeScript types for SAATH frontend

export interface AttentionItem {
  id: string;
  title: string;
  responsible_party?: string;
  tracked_by?: string;
  due_at?: number | null;
  is_overdue?: boolean;
  issue_id?: string | null;
  next_action?: {
    kind: string;
    label?: string;
    whatsapp_url?: string | null;
  } | null;
}

export interface HouseMember {
  id: string;
  name: string;
  phone?: string | null;
  role?: string;
  aliases?: string[];
}

export interface ReflectionMember {
  member_id: string;
  member_name: string;
  coordination_count: number;
  physical_count: number;
  total_actions: number;
}

export interface ErrorState {
  status: number;
  title: string;
  message: string;
  retryable: boolean;
}

export interface ConfirmationCardState {
  rawText: string;
  eventsCreated: any[];
  commitments?: any[];
  pendingConfirmations: any[];
  nextAction?: any | null;
}

export interface HistoryEvent {
  id: string;
  type: string;
  occurred_at: number;
  actor_id: string;
  payload: Record<string, any>;
}

export interface ExpenseShare {
  member_id: string;
  share_paise: number;
}
