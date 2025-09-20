import { useNotifications } from '@/providers/NotificationProvider';

export { useNotifications };

// Re-export for convenience
export type { SSEMessage, SSEError, ConnectionStatus } from '@/services/SSEClient';
