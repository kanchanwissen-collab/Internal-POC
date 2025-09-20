/**
 * SSE Client for connecting to FastAPI SSE server
 * TypeScript implementation for Next.js
 * 
 * Supports dual listening:
 * 1. Default messages (onmessage) - Global events for all users
 * 2. User-specific events (addEventListener) - Events with user ID as event name
 * 
 * Server should send:
 * - Global: data: {"message": "Hello everyone", "type": "info"}\n\n
 * - User-specific: event: user123\ndata: {"message": "Hello user123", "type": "personal"}\n\n
 */

export interface SSEMessage {
    message: string;
    type: string;
    timestamp?: string;
    isGlobalMessage?: boolean;    // True if this is a default/global message for all users
    isUserSpecific?: boolean;     // True if this is a user-specific message
    userId?: string;              // The user ID if this is a user-specific message
    [key: string]: any;
}

export interface SSEError {
    type: 'parse_error' | 'connection_error' | 'send_error';
    message?: string;
    error?: any;
    event?: Event;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'error' | 'connecting';

export class SSEClient {
    private serverUrl: string;
    private eventSource: EventSource | null = null;
    private isConnected: boolean = false;
    private messageCallbacks: ((data: SSEMessage) => void)[] = [];
    private statusCallbacks: ((status: ConnectionStatus, isConnected: boolean) => void)[] = [];
    private errorCallbacks: ((errorData: SSEError) => void)[] = [];
    private eventName: string | null = null;

    constructor(serverUrl: string = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`, eventName?: string) {
        this.serverUrl = serverUrl;
        this.eventName = eventName || null;
    }

    /**
     * Connect to the SSE server
     */
    connect(): void {
        console.log('Connecting to SSE server:', this.serverUrl);
        if (this.eventName) {
            console.log('Listening for events with name:', this.eventName);
        }

        this.notifyStatusCallbacks('connecting');
        this.eventSource = new EventSource(`${this.serverUrl}/events`);

        this.eventSource.onopen = (event) => {
            console.log('SSE connection opened');
            this.isConnected = true;
            this.notifyStatusCallbacks('connected');
        };

        // Listen to default messages (global events for all users)
        // Note: onmessage only fires for messages without an event type
        this.eventSource.onmessage = (event) => {
            console.log('SSE default message received:', event.data);

            // Check if this looks like raw SSE format (shouldn't happen for proper default messages)
            if (event.data.includes('event:') || event.data.includes('data:')) {
                console.warn('Received raw SSE format in onmessage - this might indicate server formatting issues');
                console.warn('Raw data:', event.data);
                return; // Skip processing malformed data
            }

            try {
                const data: SSEMessage = JSON.parse(event.data);
                // Add a flag to indicate this is a default/global message
                data.isGlobalMessage = true;
                this.notifyMessageCallbacks(data);
            } catch (error) {
                console.error('Error parsing SSE default message:', error);
                console.error('Raw data that failed to parse:', event.data);
                this.notifyErrorCallbacks({
                    type: 'parse_error',
                    message: event.data,
                    error
                });
            }
        };

        // If we have a specific event name (user ID), listen for user-specific events
        if (this.eventName) {
            this.eventSource.addEventListener(this.eventName, (event) => {
                console.log(`SSE user-specific event '${this.eventName}' received:`, event.data);
                console.log('Event object:', event);

                try {
                    const data: SSEMessage = JSON.parse(event.data);
                    // Add a flag to indicate this is a user-specific message
                    data.isUserSpecific = true;
                    if (this.eventName) {
                        data.userId = this.eventName;
                    }
                    this.notifyMessageCallbacks(data);
                } catch (error) {
                    console.error('Error parsing SSE user-specific event message:', error);
                    console.error('Raw event data that failed to parse:', event.data);
                    this.notifyErrorCallbacks({
                        type: 'parse_error',
                        message: event.data,
                        error
                    });
                }
            });
        }

        this.eventSource.onerror = (event) => {
            console.log('SSE connection error');
            this.isConnected = false;
            this.notifyStatusCallbacks('error');
            this.notifyErrorCallbacks({
                type: 'connection_error',
                event
            });
        };
    }

    /**
     * Send a message to the server (via HTTP POST)
     */
    async sendMessage(message: string, type: string = 'frontend'): Promise<any> {
        try {
            const response = await fetch(`${this.serverUrl}/send-message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    type: type
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Message sent successfully:', result);
                return result;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.notifyErrorCallbacks({
                type: 'send_error',
                error
            });
            throw error;
        }
    }

    /**
     * Get server status
     */
    async getStatus(): Promise<any> {
        try {
            const response = await fetch(`${this.serverUrl}/status`);
            return await response.json();
        } catch (error) {
            console.error('Error getting server status:', error);
            throw error;
        }
    }

    /**
     * Subscribe to messages
     */
    onMessage(callback: (data: SSEMessage) => void): () => void {
        this.messageCallbacks.push(callback);
        return () => this.removeMessageCallback(callback);
    }

    /**
     * Subscribe to connection status changes
     */
    onStatusChange(callback: (status: ConnectionStatus, isConnected: boolean) => void): () => void {
        this.statusCallbacks.push(callback);
        return () => this.removeStatusCallback(callback);
    }

    /**
     * Subscribe to errors
     */
    onError(callback: (errorData: SSEError) => void): () => void {
        this.errorCallbacks.push(callback);
        return () => this.removeErrorCallback(callback);
    }

    /**
     * Disconnect from the SSE server
     */
    disconnect(): void {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            this.isConnected = false;
            this.notifyStatusCallbacks('disconnected');
            console.log('SSE connection closed');
        }
    }

    /**
     * Get connection status
     */
    getConnectionStatus(): { isConnected: boolean; status: ConnectionStatus } {
        return {
            isConnected: this.isConnected,
            status: this.isConnected ? 'connected' : 'disconnected'
        };
    }

    /**
     * Get the current event name being listened to
     */
    getEventName(): string | null {
        return this.eventName;
    }

    /**
     * Set a new event name (requires reconnection to take effect)
     */
    setEventName(eventName: string | null): void {
        this.eventName = eventName;
    }

    /**
     * Subscribe to global messages only
     */
    onGlobalMessage(callback: (data: SSEMessage) => void): () => void {
        const wrappedCallback = (data: SSEMessage) => {
            if (data.isGlobalMessage) {
                callback(data);
            }
        };
        this.messageCallbacks.push(wrappedCallback);
        return () => this.removeMessageCallback(wrappedCallback);
    }

    /**
     * Subscribe to user-specific messages only
     */
    onUserMessage(callback: (data: SSEMessage) => void): () => void {
        const wrappedCallback = (data: SSEMessage) => {
            if (data.isUserSpecific) {
                callback(data);
            }
        };
        this.messageCallbacks.push(wrappedCallback);
        return () => this.removeMessageCallback(wrappedCallback);
    }

    // Private methods
    private notifyMessageCallbacks(data: SSEMessage): void {
        this.messageCallbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('Error in message callback:', error);
            }
        });
    }

    private notifyStatusCallbacks(status: ConnectionStatus): void {
        this.statusCallbacks.forEach(callback => {
            try {
                callback(status, this.isConnected);
            } catch (error) {
                console.error('Error in status callback:', error);
            }
        });
    }

    private notifyErrorCallbacks(errorData: SSEError): void {
        this.errorCallbacks.forEach(callback => {
            try {
                callback(errorData);
            } catch (error) {
                console.error('Error in error callback:', error);
            }
        });
    }

    private removeMessageCallback(callback: (data: SSEMessage) => void): void {
        const index = this.messageCallbacks.indexOf(callback);
        if (index > -1) {
            this.messageCallbacks.splice(index, 1);
        }
    }

    private removeStatusCallback(callback: (status: ConnectionStatus, isConnected: boolean) => void): void {
        const index = this.statusCallbacks.indexOf(callback);
        if (index > -1) {
            this.statusCallbacks.splice(index, 1);
        }
    }

    private removeErrorCallback(callback: (errorData: SSEError) => void): void {
        const index = this.errorCallbacks.indexOf(callback);
        if (index > -1) {
            this.errorCallbacks.splice(index, 1);
        }
    }
}

export default SSEClient;
