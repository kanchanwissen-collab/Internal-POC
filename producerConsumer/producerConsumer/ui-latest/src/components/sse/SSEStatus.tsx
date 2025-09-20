"use client"

import React, { useState } from 'react';
import { useSSE } from '@/hooks/useSSE';

interface SSEStatusProps {
    className?: string;
}

export default function SSEStatus({ className = "" }: SSEStatusProps) {
    const { isConnected, connectionStatus, sendMessage, getStatus } = useSSE();
    const [message, setMessage] = useState('');
    const [messageType, setMessageType] = useState('info');
    const [isLoading, setIsLoading] = useState(false);

    const handleSendMessage = async () => {
        if (!message.trim()) return;

        setIsLoading(true);
        try {
            await sendMessage(message, messageType);
            setMessage('');
        } catch (error) {
            console.error('Failed to send message:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleGetStatus = async () => {
        try {
            const status = await getStatus();
            console.log('Server status:', status);
        } catch (error) {
            console.error('Failed to get status:', error);
        }
    };

    const getStatusColor = () => {
        switch (connectionStatus) {
            case 'connected':
                return 'text-green-600 bg-green-100';
            case 'connecting':
                return 'text-yellow-600 bg-yellow-100';
            case 'error':
                return 'text-red-600 bg-red-100';
            case 'disconnected':
            default:
                return 'text-gray-600 bg-gray-100';
        }
    };

    return (
        <div className={`p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm border ${className}`}>
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    SSE Connection
                </h3>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor()}`}>
                    <span className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                        {connectionStatus}
                    </span>
                </div>
            </div>

            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Send Message
                    </label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="Enter message..."
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                        />
                        <select
                            value={messageType}
                            onChange={(e) => setMessageType(e.target.value)}
                            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="info">Info</option>
                            <option value="success">Success</option>
                            <option value="warning">Warning</option>
                            <option value="error">Error</option>
                        </select>
                        <button
                            onClick={handleSendMessage}
                            disabled={!message.trim() || isLoading || !isConnected}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? 'Sending...' : 'Send'}
                        </button>
                    </div>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={handleGetStatus}
                        disabled={!isConnected}
                        className="px-4 py-2 bg-gray-600 text-white rounded-md text-sm font-medium hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Get Server Status
                    </button>
                </div>
            </div>
        </div>
    );
}

// Simple connection indicator component
export function SSEConnectionIndicator() {
    const { isConnected, connectionStatus } = useSSE();

    return (
        <div className="flex items-center gap-2 text-sm">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-gray-600 dark:text-gray-400">
                SSE: {connectionStatus}
            </span>
        </div>
    );
}
