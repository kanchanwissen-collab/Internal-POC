"use client"

import { useParams, useSearchParams } from 'next/navigation'
import { useEffect, useState, Suspense, useRef } from 'react';

const LogViewer = ({ sessionId }: { sessionId: string }) => {
    const [logs, setLogs] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const logsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    useEffect(() => {
        setIsLoading(true);
        const eventSource = new EventSource(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/stream-logs/${sessionId}`);

        eventSource.addEventListener(sessionId, (event) => {
            setLogs(prevLogs => [...prevLogs, event.data]);
        });

        eventSource.onopen = () => {
            setIsLoading(false);
        };

        eventSource.onerror = () => {
            setIsLoading(false);
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [sessionId]);

    return (
        <div className="bg-gray-900 text-white font-mono text-sm rounded-lg p-4 h-[50vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Logs for Session: <span className="text-green-400">{sessionId}</span></h2>
                {isLoading && <div className="text-gray-400">Loading...</div>}
            </div>
            <div className="space-y-1">
                {logs.map((log, index) => (
                    <div key={index}>{log}</div>
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

    return (
        <div className="max-w-7xl mx-auto space-y-6 p-4">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Session Details</h1>
            <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div><strong>Session ID:</strong> {sessionId}</div>
                    <div><strong>Status:</strong> {status}</div>
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
