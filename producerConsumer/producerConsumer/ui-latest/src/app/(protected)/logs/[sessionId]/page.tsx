"use client"

import { useParams, useSearchParams } from 'next/navigation'
import { useEffect, useState, Suspense, useRef } from 'react';

const LogViewer = ({ sessionId }: { sessionId: string }) => {
    const [logs, setLogs] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isLive, setIsLive] = useState(false);
    const logsEndRef = useRef<HTMLDivElement>(null);
    const searchParams = useSearchParams();

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    useEffect(() => {
        setIsLoading(true);
        
        // Check if this is a request_id (for live logs) or batch_id/sessionId (for historical logs)
        const status = searchParams.get('status');
        const requestId = searchParams.get('request_id');
        
        // Use request_id endpoint for running status with valid request_id, fallback to sessionId
        const isLiveSession = status === 'running';
        const effectiveRequestId = (requestId && requestId !== '') ? requestId : sessionId;
        setIsLive(!!isLiveSession);
        
        // Choose the appropriate SSE endpoint
        const sseUrl = isLiveSession 
            ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1/stream-logs/request/${effectiveRequestId}`
            : `${process.env.NEXT_PUBLIC_API_URL}/api/v1/stream-logs/${sessionId}`;
        
        console.log(`Connecting to SSE: ${sseUrl} (Live: ${isLiveSession})`);
        
        const eventSource = new EventSource(sseUrl);

        if (isLiveSession) {
            // Handle request_id-based SSE (structured JSON messages)
            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    switch(data.type) {
                        case 'connected':
                            setLogs(prevLogs => [...prevLogs, `🔗 ${data.message}`]);
                            break;
                            
                        case 'log':
                            const logData = data.data || {};
                            const message = logData.message || 'No message';
                            const source = logData.source || 'unknown';
                            const timestamp = new Date().toLocaleTimeString();
                            
                            setLogs(prevLogs => [...prevLogs, `[${timestamp}] [${source}] ${message}`]);
                            break;
                            
                        case 'heartbeat':
                            // Optional: show heartbeat or ignore
                            // setLogs(prevLogs => [...prevLogs, '💓 Heartbeat']);
                            break;
                            
                        case 'error':
                            setLogs(prevLogs => [...prevLogs, `❌ Error: ${data.message}`]);
                            break;
                            
                        default:
                            setLogs(prevLogs => [...prevLogs, `📤 ${data.type}: ${JSON.stringify(data)}`]);
                    }
                } catch (_error) {
                    // Handle plain text messages as fallback
                    setLogs(prevLogs => [...prevLogs, event.data]);
                }
            };
        } else {
            // Handle batch_id-based SSE (legacy format)
            eventSource.addEventListener(sessionId, (event) => {
                setLogs(prevLogs => [...prevLogs, event.data]);
            });
        }

        eventSource.onopen = () => {
            setIsLoading(false);
            console.log(`SSE connection opened for ${isLiveSession ? 'live logs' : 'historical logs'}`);
        };

        eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            setIsLoading(false);
            setLogs(prevLogs => [...prevLogs, `❌ Connection error - retrying...`]);
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [sessionId, searchParams]);

    return (
        <div className="bg-gray-900 text-white font-mono text-sm rounded-lg p-4 h-[50vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
                <div className="flex items-center space-x-2">
                    <h2 className="text-xl font-bold">
                        {isLive ? 'Live Logs' : 'Logs'} for Session: <span className="text-green-400">{sessionId}</span>
                    </h2>
                    {isLive && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <span className="w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse"></span>
                            LIVE
                        </span>
                    )}
                </div>
                {isLoading && <div className="text-gray-400">Loading...</div>}
            </div>
            <div className="space-y-1">
                {logs.map((log, index) => (
                    <div key={index} className="break-words">{log}</div>
                ))}
                <div ref={logsEndRef} />
            </div>
        </div>
    );
};

const LogPageContent = () => {
    const params = useParams();
    const searchParams = useSearchParams();
    const sessionId = Array.isArray(params.sessionId) ? params.sessionId[0] : params.sessionId;

    const status = searchParams.get('status');
    const patientName = searchParams.get('patientName');
    const providerName = searchParams.get('providerName');
    const serviceType = searchParams.get('serviceType');
    const agentType = searchParams.get('agentType');
    const createdAt = searchParams.get('createdAt');
    const lastActivity = searchParams.get('lastActivity');
    const requestId = searchParams.get('request_id');
    const batchId = searchParams.get('batch_id');

    return (
        <div className="max-w-7xl mx-auto space-y-6 p-4">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Session Details</h1>
            <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div><strong>Session ID:</strong> {sessionId}</div>
                    <div><strong>Status:</strong> {status}</div>
                    {requestId && <div><strong>Request ID:</strong> {requestId}</div>}
                    {batchId && <div><strong>Batch ID:</strong> {batchId}</div>}
                    <div><strong>Patient:</strong> {patientName}</div>
                    <div><strong>Provider:</strong> {providerName}</div>
                    <div><strong>Service:</strong> {serviceType}</div>
                    <div><strong>Agent Type:</strong> {agentType}</div>
                    <div><strong>Created At:</strong> {createdAt ? new Date(createdAt).toLocaleString() : 'N/A'}</div>
                    <div><strong>Last Activity:</strong> {lastActivity ? new Date(lastActivity).toLocaleString() : 'N/A'}</div>
                </div>
            </div>
            {sessionId ? <LogViewer sessionId={sessionId} /> : <p>Session ID not found.</p>}
        </div>
    );
}

export default function LogPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <LogPageContent />
        </Suspense>
    );
}
