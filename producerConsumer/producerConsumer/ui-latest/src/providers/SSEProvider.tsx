"use client"

import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import SSEClient, { SSEMessage, SSEError, ConnectionStatus } from '@/services/SSEClient';
import { useNotifications } from '@/providers/NotificationProvider';
import { useSession } from 'next-auth/react';

interface SSEContextType {
    client: SSEClient | null;
    isConnected: boolean;
    connectionStatus: ConnectionStatus;
    sendMessage: (message: string, type?: string) => Promise<any>;
    getStatus: () => Promise<any>;
}

const SSEContext = createContext<SSEContextType | undefined>(undefined);

interface SSEProviderProps {
    children: React.ReactNode;
    serverUrl?: string;
    showToastNotifications?: boolean;
}

export function SSEProvider({
    children,
    serverUrl = `${process.env.NEXT_PUBLIC_API_URL}/api/v1`, // External backend server
    showToastNotifications = true
}: SSEProviderProps) {
    const [isConnected, setIsConnected] = useState(false);
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
    const clientRef = useRef<SSEClient | null>(null);
    const { addNotification } = useNotifications();
    const { data: session } = useSession();

    useEffect(() => {
        // Only connect if user is authenticated and has a userId
        if (!session?.user?.userId) {
            console.log('No authenticated user with userId, skipping SSE connection');
            return;
        }

        // Create common SSE endpoint for external backend
        const commonSseUrl = `${serverUrl}`;
        console.log('Connecting to common SSE endpoint:', commonSseUrl);
        console.log('Will listen for events with name:', session.user.userId);

        // Initialize SSE client with common endpoint and user ID as event name
        const client = new SSEClient(commonSseUrl, session.user.userId);
        clientRef.current = client;

        // Subscribe to messages
        const unsubscribeMessages = client.onMessage((data: SSEMessage) => {
            console.log('SSE Message received:', data);

            // Log message type for debugging
            if (data.isGlobalMessage) {
                console.log('Global message for all users');
            } else if (data.isUserSpecific) {
                console.log(`User-specific message for user: ${data.userId}`);
            }

            // Add to notifications list
            addNotification(data);

            if (showToastNotifications) {
                // Show toast notification for incoming messages
                const messageText = data.message || 'New message received';
                const messageType = data.type || 'info';

                // Add message source indicator
                const messageSource = data.isGlobalMessage ? ' (Global)' :
                    data.isUserSpecific ? ' (Personal)' : '';

                switch (messageType.toLowerCase()) {
                    case 'success':
                        toast.success(messageText + messageSource);
                        break;
                    case 'error':
                        toast.error(messageText + messageSource);
                        break;
                    case 'warning':
                        toast(messageText + messageSource, {
                            icon: '⚠️',
                            style: {
                                background: '#fef3cd',
                                color: '#856404',
                                border: '1px solid #ffeaa7',
                            },
                        });
                        break;
                    case 'info':
                    default:
                        toast(messageText + messageSource, {
                            icon: data.isGlobalMessage ? '📢' : data.isUserSpecific ? '👤' : 'ℹ️',
                            style: {
                                background: data.isUserSpecific ? '#e8f5e8' : '#d1ecf1',
                                color: data.isUserSpecific ? '#155724' : '#0c5460',
                                border: data.isUserSpecific ? '1px solid #c3e6cb' : '1px solid #bee5eb',
                            },
                        });
                        break;
                }
            }
        });

        // Subscribe to connection status changes
        const unsubscribeStatus = client.onStatusChange((status: ConnectionStatus, connected: boolean) => {
            console.log('SSE Connection status:', status, connected);
            setConnectionStatus(status);
            setIsConnected(connected);

            if (showToastNotifications) {
                switch (status) {
                    case 'connected':
                        toast.success(`Connected to server, listening for events: ${session?.user?.userId}`, { duration: 2000 });
                        break;
                    case 'disconnected':
                        toast('Disconnected from server', {
                            icon: '🔌',
                            duration: 2000,
                            style: {
                                background: '#f8f9fa',
                                color: '#6c757d',
                            }
                        });
                        break;
                    case 'error':
                        toast.error('Connection error', { duration: 3000 });
                        break;
                    case 'connecting':
                        toast('Connecting to server...', {
                            icon: '🔄',
                            duration: 2000,
                            style: {
                                background: '#e3f2fd',
                                color: '#1565c0',
                            }
                        });
                        break;
                }
            }
        });

        // Subscribe to errors
        const unsubscribeErrors = client.onError((errorData: SSEError) => {
            console.error('SSE Error:', errorData);

            if (showToastNotifications) {
                let errorMessage = 'An error occurred';

                switch (errorData.type) {
                    case 'connection_error':
                        errorMessage = 'Failed to connect to server';
                        break;
                    case 'parse_error':
                        errorMessage = 'Failed to parse server message';
                        break;
                    case 'send_error':
                        errorMessage = 'Failed to send message';
                        break;
                }

                toast.error(errorMessage, { duration: 4000 });
            }
        });

        // Connect to the server
        client.connect();

        // Cleanup function
        return () => {
            client.disconnect();
            unsubscribeMessages();
            unsubscribeStatus();
            unsubscribeErrors();
            clientRef.current = null;
        };
    }, [serverUrl, showToastNotifications, session?.user?.userId]); // Added userId dependency

    // Handle page unload
    useEffect(() => {
        const handleBeforeUnload = () => {
            if (clientRef.current) {
                clientRef.current.disconnect();
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, []);

    const sendMessage = async (message: string, type: string = 'frontend') => {
        if (!clientRef.current) {
            throw new Error('SSE client not initialized');
        }
        return await clientRef.current.sendMessage(message, type);
    };

    const getStatus = async () => {
        if (!clientRef.current) {
            throw new Error('SSE client not initialized');
        }
        return await clientRef.current.getStatus();
    };

    const contextValue: SSEContextType = {
        client: clientRef.current,
        isConnected,
        connectionStatus,
        sendMessage,
        getStatus,
    };

    return (
        <SSEContext.Provider value={contextValue}>
            {children}
        </SSEContext.Provider>
    );
}

export function useSSE(): SSEContextType {
    const context = useContext(SSEContext);
    if (context === undefined) {
        throw new Error('useSSE must be used within an SSEProvider');
    }
    return context;
}

export default SSEProvider;
