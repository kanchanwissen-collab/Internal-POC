import { useSSE } from '@/providers/SSEProvider';

export { useSSE };

// Re-export types for convenience
export type { SSEMessage, SSEError, ConnectionStatus } from '@/services/SSEClient';
