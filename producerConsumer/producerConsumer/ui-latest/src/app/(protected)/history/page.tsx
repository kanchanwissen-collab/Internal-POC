"use client"

import { useState, useEffect, useRef } from "react"
import { useSession } from "next-auth/react"
import toast from 'react-hot-toast'
import { ApiResponse, ApiRequest } from "@/types/api";
import { Suspense, useCallback } from "react"

// --- Live Log Modal Component ---
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
        <div className="bg-gray-900 text-white font-mono text-xs rounded-lg p-2 h-[50vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-2">
                <h2 className="text-lg font-bold">Logs for Session: <span className="text-green-400">{sessionId}</span></h2>
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

type SessionStatus = 'submitted' | 'queued' | 'expired' | 'running' | 'failed' | 'approved' | 'denied' | 'manual-action';

interface Session {
    id: string;
    sessionId: string;
    status: SessionStatus;
    createdAt: string;
    lastActivity: string;
    agentType: 'PRIOR_AUTH' | 'onboarding' | 'hr-leave' | 'finance' | 'general';
    vendor?: string;
    sequence_no?: string;
    request_id?: string;
    batch_id?: string;
    manual_actions?: any[];
    patientName?: string;
    dateOfBirth?: string;
    providerName?: string;
    serviceType?: string;
    memberId?: string;
    appointmentId?: string;
    // Add new fields:
    totalCount?: string;
    apiPatientName?: string;
    apiDob?: string;
    apiAppointmentId?: string;
}

const mockSessions: Session[] = [
    {
        id: "1",
        sessionId: "batch-001",
        request_id: "req-001",
        batch_id: "batch-001",
        sequence_no: "1",
        vendor: "Evicore",
        status: "running",
        createdAt: "2025-09-15T10:30:00Z",
        lastActivity: "2025-09-15T12:15:00Z",
        agentType: "PRIOR_AUTH",
        manual_actions: [],
        patientName: "John Smith",
        dateOfBirth: "1985-06-15",
        providerName: "City General Hospital",
        serviceType: "MRI Scan Authorization",
        memberId: "MEM12345",
        appointmentId: "APT98765",
    },
    {
        id: "2",
        sessionId: "batch-002",
        request_id: "req-002",
        batch_id: "batch-002",
        sequence_no: "1",
        vendor: "Evicore",
        status: "approved",
        createdAt: "2025-09-15T11:00:00Z",
        lastActivity: "2025-09-15T11:30:00Z",
        agentType: "PRIOR_AUTH",
        manual_actions: [],
        patientName: "Jane Doe",
        dateOfBirth: "1990-02-20",
        providerName: "Community Clinic",
        serviceType: "Physical Therapy",
        memberId: "MEM67890",
        appointmentId: "APT54321",
    },
    {
        id: "3",
        sessionId: "batch-003",
        request_id: "req-003",
        batch_id: "batch-003",
        sequence_no: "1",
        vendor: "Evicore",
        status: "denied",
        createdAt: "2025-09-14T09:00:00Z",
        lastActivity: "2025-09-14T09:45:00Z",
        agentType: "PRIOR_AUTH",
        manual_actions: [],
        patientName: "Peter Jones",
        dateOfBirth: "1975-11-10",
        providerName: "General Hospital",
        serviceType: "Surgery",
        memberId: "MEM11223",
        appointmentId: "APT99887",
    },
];

export default function HistoryPage() {
    const { data: _session } = useSession()
    const [sessions, setSessions] = useState<Session[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [connectingSession, setConnectingSession] = useState<string | null>(null)
    const [statusFilter, setStatusFilter] = useState<Session['status'] | 'all'>('all')
    const [agentTypeFilter, setAgentTypeFilter] = useState<Session['agentType'] | 'all'>('all')
    const [dateFilter, setDateFilter] = useState<'all' | 'today' | 'week' | 'month'>('all')
    const toastShownRef = useRef(false)
    const [noVncModal, setNoVncModal] = useState<{ open: boolean, session: Session | null }>({ open: false, session: null })
    const [liveLogModal, setLiveLogModal] = useState<{ open: boolean, session: Session | null }>({ open: false, session: null });

    // Simulate loading sessions data
    useEffect(() => {
        const fetchSessions = async () => {
            setIsLoading(true)
            toast.dismiss('agent-sessions-loaded')

            try {
                const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/agentic-platform/prior-auths/requests`);
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                const result: ApiResponse = await response.json();

                const formattedSessions: Session[] = result.data.map((req: ApiRequest) => ({
                    id: req.request_id,
                    sessionId: req.batch_id,
                    status: req.status || req.status_data?.status || "-",
                    createdAt: req.manual_actions?.[0]?.action_at || new Date().toISOString(),
                    lastActivity: req.manual_actions?.[0]?.action_at || new Date().toISOString(),
                    patientName: req.patient_name || "-",
                    dateOfBirth: req.dob || "-",
                    providerName: "-", // update if available
                    serviceType: "-",  // update if available
                    memberId: req.person_no || "-", // <-- NEW FIELD
                    appointmentId: req.appointment_id || "-",
                    agentType: req.agent_type?.toUpperCase() === "PRIOR_AUTH" ? "PRIOR_AUTH" : "general",
                    vendor: req.vendor,
                    sequence_no: req.sequence_no,
                    request_id: req.request_id,
                    batch_id: req.batch_id,
                    manual_actions: req.manual_actions,
                    // new fields
                    totalCount: req.total_count || "-",
                    apiPatientName: req.patient_name || "-",
                    apiDob: req.dob || "-",
                    apiAppointmentId: req.appointment_id || "-",
                    dateOfService: req.date_of_service || "-", // <-- NEW FIELD
                    visitReason: req.visit_reason || "-",      // <-- NEW FIELD
                    specialty: req.specialty || "-",
                }));

                setSessions(formattedSessions);
            } catch (error) {
                console.error("Failed to fetch sessions:", error);
                toast.error("Failed to fetch sessions, using fallback data.");
                setSessions(mockSessions);
            } finally {
                setIsLoading(false);
            }

            // ...existing code...
        }

        fetchSessions();

        // Poll every 10 seconds
        const intervalId = setInterval(fetchSessions, 10000);

        return () => {
            clearInterval(intervalId);
        };
    }, []);

    const getStatusColor = (status: Session['status']) => {
        switch (status) {
            case 'submitted':
                return 'bg-blue-100 text-blue-800'
            case 'queued':
                return 'bg-purple-100 text-purple-800'
            case 'expired':
                return 'bg-gray-100 text-gray-800'
            case 'running':
                return 'bg-green-100 text-green-800'
            case 'failed':
                return 'bg-red-100 text-red-800'
            case 'approved':
                return 'bg-green-100 text-green-800'
            case 'denied':
                return 'bg-red-100 text-red-800'
            case 'manual-action':
                return 'bg-orange-100 text-orange-800'
            default:
                return 'bg-gray-100 text-gray-800'
        }
    }

    const getRowBackgroundColor = (status: Session['status']) => {
        switch (status) {
            case 'submitted':
                return 'bg-blue-50 hover:bg-blue-100'
            case 'queued':
                return 'bg-purple-50 hover:bg-purple-100'
            case 'expired':
                return 'bg-gray-50 hover:bg-gray-100'
            case 'running':
                return 'bg-green-50 hover:bg-green-100'
            case 'failed':
                return 'bg-red-50 hover:bg-red-100'
            case 'approved':
                return 'bg-green-50 hover:bg-green-100'
            case 'denied':
                return 'bg-red-50 hover:bg-red-100'
            case 'manual-action':
                return 'bg-orange-50 hover:bg-orange-100'
            default:
                return 'bg-gray-50 hover:bg-gray-100'
        }
    }

    const getStatusIcon = (status: Session['status']) => {
        switch (status) {
            case 'submitted':
                return (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zM4 4h3a3 3 0 006 0h3a2 2 0 012 2v9a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2zm2.5 7a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm2.45 4a2.5 2.5 0 10-4.9 0h4.9zM12 9a1 1 0 100 2h3a1 1 0 100-2h-3zm-1 4a1 1 0 011-1h2a1 1 0 110 2h-2a1 1 0 01-1-1z" clipRule="evenodd" />
                    </svg>
                )
            case 'queued':
                return (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                    </svg>
                )
            case 'expired':
                return (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-8a1 1 0 012 0v3a1 1 0 01-2 0v-3zm1-4a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                    </svg>
                )
            case 'running':
                return (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                )
            case 'approved':
                return (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                )
            case 'denied':
                return (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                )
            case 'manual-action':
                return (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-5.5-2.5a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zM10 12a5.99 5.99 0 00-4.793 2.39A6.483 6.483 0 0010 16.5a6.483 6.483 0 004.793-2.11A5.99 5.99 0 0010 12z" clipRule="evenodd" />
                    </svg>
                )
            case 'failed':
                return (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                )
            default:
                return null
        }
    }

    const handleLogView = (sessionItem: Session) => {
        // Convert all values to string for URLSearchParams
        // const params: Record<string, string> = {};
        // Object.entries(sessionItem).forEach(([key, value]) => {
        //     if (value !== undefined && value !== null) {
        //         params[key] = String(value);
        //     }
        // });
        // const query = new URLSearchParams(params).toString();
        // const logUrl = `/logs/${sessionItem.request_id}?${query}`;
        // window.open(logUrl, '_blank');
        setLiveLogModal({ open: true, session: sessionItem });
    };

    const closeLiveLogModal = useCallback(() => setLiveLogModal({ open: false, session: null }), []);

    const handleNoVNCConnect = (sessionItem: Session) => {
        if (sessionItem.status !== 'manual-action' && sessionItem.status !== 'expired') {
            toast.error(`Cannot connect to ${sessionItem.status} session`)
            return
        }
        setNoVncModal({ open: true, session: sessionItem })
    }

    const closeNoVncModal = () => setNoVncModal({ open: false, session: null })

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString()
    }

    const filterSessionsByDate = (sessions: Session[]) => {
        const now = new Date()
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

        switch (dateFilter) {
            case 'today':
                return sessions.filter(session => {
                    const sessionDate = new Date(session.createdAt)
                    const sessionDay = new Date(sessionDate.getFullYear(), sessionDate.getMonth(), sessionDate.getDate())
                    return sessionDay.getTime() === today.getTime()
                })
            case 'week':
                const weekAgo = new Date(today)
                weekAgo.setDate(weekAgo.getDate() - 7)
                return sessions.filter(session => {
                    const sessionDate = new Date(session.createdAt)
                    return sessionDate >= weekAgo
                })
            case 'month':
                const monthAgo = new Date(today)
                monthAgo.setMonth(monthAgo.getMonth() - 1)
                return sessions.filter(session => {
                    const sessionDate = new Date(session.createdAt)
                    return sessionDate >= monthAgo
                })
            default:
                return sessions
        }
    }

    const getAgentTypeLabel = (agentType: Session['agentType']) => {
        switch (agentType) {
            case 'PRIOR_AUTH':
                return 'PRIOR_AUTH'
            case 'onboarding':
                return 'Client Onboarding'
            case 'hr-leave':
                return 'HR & Leave'
            case 'finance':
                return 'Finance'
            case 'general':
                return 'General'
            default:
                return 'Unknown'
        }
    }

    const getAgentTypeIcon = (agentType: Session['agentType']) => {
        switch (agentType) {
            case 'PRIOR_AUTH':
                return (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                )
            case 'onboarding':
                return (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z" />
                    </svg>
                )
            case 'hr-leave':
                return (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                    </svg>
                )
            case 'finance':
                return (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zM14 6a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2V8a2 2 0 012-2h8zM6 10a2 2 0 114 0 2 2 0 01-4 0zM1.394 14.192a8 8 0 01-.682-3.192 8 8 0 01.682-3.192 2 2 0 00-.682 3.192z" />
                    </svg>
                )
            case 'general':
                return (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                    </svg>
                )
            default:
                return null
        }
    }

    const filteredSessions = filterSessionsByDate(sessions).filter(sessionItem => {
        const matchesStatus = statusFilter === 'all' || sessionItem.status === statusFilter
        const matchesAgentType = agentTypeFilter === 'all' || sessionItem.agentType === agentTypeFilter
        return matchesStatus && matchesAgentType
    })

    // Get sessions filtered only by agent type and date (for statistics)
    const agentFilteredSessions = filterSessionsByDate(
        agentTypeFilter === 'all'
            ? sessions
            : sessions.filter(sessionItem => sessionItem.agentType === agentTypeFilter)
    )

    const getFilterButtonClass = (filterStatus: Session['status'] | 'all') => {
        const isActive = statusFilter === filterStatus
        const baseClass = "px-4 py-2 text-sm font-medium rounded-md transition-colors"

        if (isActive) {
            switch (filterStatus) {
                case 'all':
                    return `${baseClass} bg-indigo-600 text-white`
                case 'submitted':
                    return `${baseClass} bg-blue-600 text-white`
                case 'queued':
                    return `${baseClass} bg-purple-600 text-white`
                case 'expired':
                    return `${baseClass} bg-gray-600 text-white`
                case 'running':
                    return `${baseClass} bg-green-600 text-white`
                case 'failed':
                    return `${baseClass} bg-red-600 text-white`
                case 'approved':
                    return `${baseClass} bg-green-600 text-white`
                case 'denied':
                    return `${baseClass} bg-red-600 text-white`
                case 'manual-action':
                    return `${baseClass} bg-orange-600 text-white`
                default:
                    return `${baseClass} bg-gray-600 text-white`
            }
        } else {
            return `${baseClass} bg-white text-gray-700 border border-gray-300 hover:bg-gray-50`
        }
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-gray-600 dark:text-gray-300">Loading sessions...</span>
                </div>
            </div>
        )
    }

    return (
        <div className="container-fluid px-1 py-1 space-y-2">
            {/* Live Log Modal */}
            {liveLogModal.open && liveLogModal.session && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-transparent"
                    onClick={closeLiveLogModal}
                >
                    <div
                        className="relative bg-white dark:bg-gray-900 rounded-lg shadow-lg w-full max-w-4xl mx-auto p-4"
                        onClick={e => e.stopPropagation()}
                    >
                        <div className="flex justify-between items-center mb-2">
                            <h1 className="text-xl font-bold text-gray-900 dark:text-white">Session Details</h1>
                            <button
                                className="text-gray-400 hover:text-gray-700 text-xl"
                                onClick={closeLiveLogModal}
                                title="Close"
                            >
                                ×
                            </button>
                        </div>
                        <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-2 mb-2">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
                                <div><strong>Patient Name:</strong> {liveLogModal.session.patientName}</div>
                                <div><strong>Date of Birth:</strong> {liveLogModal.session.dateOfBirth}</div>
                                <div><strong>Provider Name:</strong> {liveLogModal.session.providerName}</div>
                                <div><strong>Request ID:</strong> {liveLogModal.session.request_id}</div>
                                <div><strong>Service Type:</strong> {liveLogModal.session.serviceType}</div>
                                <div><strong>Member ID:</strong> {liveLogModal.session.memberId}</div>
                                <div><strong>Appointment ID:</strong> {liveLogModal.session.appointmentId}</div>
                                <div><strong>Status:</strong> {liveLogModal.session.status}</div>
                                <div><strong>Agent Type:</strong> {liveLogModal.session.agentType}</div>
                                <div><strong>Vendor:</strong> {liveLogModal.session.vendor}</div>
                                <div><strong>Batch ID:</strong> {liveLogModal.session.batch_id}</div>
                                {/* <div><strong>Manual Actions:</strong> {JSON.stringify(liveLogModal.session.manual_actions)}</div> */}
                                <div><strong>Created At:</strong> {liveLogModal.session.createdAt ? new Date(liveLogModal.session.createdAt).toLocaleString() : 'N/A'}</div>
                                <div><strong>Last Activity:</strong> {liveLogModal.session.lastActivity ? new Date(liveLogModal.session.lastActivity).toLocaleString() : 'N/A'}</div>
                            </div>
                        </div>
                        <Suspense fallback={<div>Loading logs...</div>}>
                            <LogViewer sessionId={liveLogModal.session.request_id} />
                        </Suspense>
                    </div>
                </div>
            )}
            {/* Modal for noVNC */}
            {noVncModal.open && noVncModal.session && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-transparent backdrop-blur-sm"
                    onClick={closeNoVncModal}
                >
                    <div
                        className="relative bg-white rounded-lg shadow-lg w-full max-w-5xl mx-auto"
                        onClick={e => e.stopPropagation()}
                    >         {/* Warning Banner */}
                        <div className="w-full bg-yellow-200 text-yellow-900 px-4 py-2 flex items-center whitespace-nowrap overflow-hidden rounded-t-lg">
                            {/* Better warning icon */}
                            <svg className="w-5 h-5 mr-2 text-yellow-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 19a2 2 0 01-1.73 1H4.73A2 2 0 013 19l7.29-12.29a2 2 0 013.42 0L21 19z" />
                            </svg>
                            <div className="font-semibold text-xs">
                                After filling details, <b>Click the Submit Button on the top-right</b> and <b>not the continue button in the below screen</b>.
                            </div>
                        </div>
                        {/* Header with session details and Submit button */}
                        <div className="flex justify-between items-start px-4 py-3 border-b border-gray-200">
                            <div className="w-full">
                                <div className="font-bold text-lg text-gray-900">Session Details</div>
                                <div className="text-xs text-gray-600 mt-1">
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                                        <div><b>Patient:</b> {noVncModal.session.apiPatientName}</div>
                                        <div><b>DOB:</b> {noVncModal.session.apiDob}</div>
                                        <div><b>Vendor:</b> {noVncModal.session.vendor}</div>
                                        <div><b>Request ID:</b> {noVncModal.session.request_id}</div>
                                        <div><b>Appointment ID:</b> {noVncModal.session.appointmentId}</div>
                                        <div><b>Session ID:</b> {noVncModal.session.sessionId}</div>
                                        <div><b>Status:</b> {noVncModal.session.status}</div>
                                        <div><b>Agent Type:</b> {noVncModal.session.agentType}</div>
                                        <div><b>Sequence No:</b> {noVncModal.session.sequence_no}</div>
                                        <div><b>Batch ID:</b> {noVncModal.session.batch_id}</div>
                                        <div><b>Patient Name:</b> {noVncModal.session.patientName}</div>
                                        <div><b>Date of Birth:</b> {noVncModal.session.dateOfBirth}</div>
                                        <div><b>Provider Name:</b> {noVncModal.session.providerName}</div>
                                        <div><b>Service Type:</b> {noVncModal.session.serviceType}</div>
                                        <div><b>Member ID:</b> {noVncModal.session.memberId}</div>
                                        <div><b>Total Count:</b> {noVncModal.session.totalCount}</div>
                                        <div><b>API Patient Name:</b> {noVncModal.session.apiPatientName}</div>
                                        <div><b>API DOB:</b> {noVncModal.session.apiDob}</div>
                                        <div><b>API Appointment ID:</b> {noVncModal.session.apiAppointmentId}</div>
                                        <div><b>Created At:</b> {noVncModal.session.createdAt ? new Date(noVncModal.session.createdAt).toLocaleString() : 'N/A'}</div>
                                        <div><b>Last Activity:</b> {noVncModal.session.lastActivity ? new Date(noVncModal.session.lastActivity).toLocaleString() : 'N/A'}</div>
                                    </div>
                                </div>
                            </div>
                            <div className="flex flex-col items-end gap-2">
                                <div className="flex gap-2">
                                    <button
                                        className="px-4 py-1 bg-indigo-600 text-white rounded font-semibold hover:bg-indigo-700 transition"
                                        onClick={() => {
                                            toast.success("Submitted!");
                                            closeNoVncModal();
                                        }}
                                    >
                                        Submit
                                    </button>
                                    <button
                                        className="px-4 py-1 bg-red-500 text-white rounded font-semibold hover:bg-red-600 transition"
                                        onClick={() => {
                                            toast("Discarded", { icon: "🗑️" });
                                            closeNoVncModal();
                                        }}
                                    >
                                        Discard
                                    </button>
                                </div>
                                <button
                                    className="text-gray-400 hover:text-gray-700 text-xl"
                                    onClick={closeNoVncModal}
                                    title="Close"
                                >
                                    ×
                                </button>
                            </div>
                        </div>
                        {/* noVNC Screen Placeholder */}
                        <div className="p-4">
                            <div className="w-full h-[32rem] bg-gray-100 rounded flex items-center justify-center text-gray-400 border border-dashed border-gray-300">
                                {/* Replace this with actual noVNC iframe or component */}
                                <span className="text-lg">[noVNC Screen Here]</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 w-full">
                <div>
                    <h1 className="text-lg font-bold text-gray-900 dark:text-white">History</h1>
                    <p className="text-xs text-gray-600 dark:text-gray-300 mt-1">
                        Monitor and review sessions across different departments
                    </p>
                </div>
                <div className="flex items-center space-x-2 mt-2 sm:mt-0">
                    {/* Date Filter */}
                    <div className="flex items-center space-x-1">
                        <label className="text-xs font-medium text-gray-700 dark:text-gray-300">Filter by Date:</label>
                        <select
                            value={dateFilter}
                            onChange={(e) => setDateFilter(e.target.value as 'all' | 'today' | 'week' | 'month')}
                            className="px-2 py-0.5 text-xs border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        >
                            <option value="all">All Time</option>
                            <option value="today">Today</option>
                            <option value="week">Last 7 Days</option>
                            <option value="month">Last 30 Days</option>
                        </select>
                    </div>

                </div>
            </div>

            {/* Agent Type Navigation */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-2 w-full">
                {/* <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4"> Categories</h3> */}
                <div className="flex flex-wrap gap-1 w-full">
                    <button
                        onClick={() => setAgentTypeFilter('all')}
                        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium transition-colors ${agentTypeFilter === 'all'
                            ? 'bg-indigo-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" clipRule="evenodd" />
                        </svg>
                        All  ({sessions.length})
                    </button>

                    <button
                        onClick={() => setAgentTypeFilter('PRIOR_AUTH')}
                        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium transition-colors ${agentTypeFilter === 'PRIOR_AUTH'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        {getAgentTypeIcon('PRIOR_AUTH')}
                        <span className="ml-2">PRIOR_AUTH ({sessions.filter(s => s.agentType === 'PRIOR_AUTH').length})</span>
                    </button>
                    {/* 
                    <button
                        onClick={() => setAgentTypeFilter('onboarding')}
                        className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${agentTypeFilter === 'onboarding'
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        {getAgentTypeIcon('onboarding')}
                        <span className="ml-2">Client Onboarding ({sessions.filter(s => s.agentType === 'onboarding').length})</span>
                    </button>

                    <button
                        onClick={() => setAgentTypeFilter('hr-leave')}
                        className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${agentTypeFilter === 'hr-leave'
                            ? 'bg-yellow-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        {getAgentTypeIcon('hr-leave')}
                        <span className="ml-2">HR & Leave ({sessions.filter(s => s.agentType === 'hr-leave').length})</span>
                    </button>

                    <button
                        onClick={() => setAgentTypeFilter('finance')}
                        className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${agentTypeFilter === 'finance'
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        {getAgentTypeIcon('finance')}
                        <span className="ml-2">Finance ({sessions.filter(s => s.agentType === 'finance').length})</span>
                    </button>

                    <button
                        onClick={() => setAgentTypeFilter('general')}
                        className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${agentTypeFilter === 'general'
                            ? 'bg-gray-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        {getAgentTypeIcon('general')}
                        <span className="ml-2">General ({sessions.filter(s => s.agentType === 'general').length})</span>
                    </button> */}
                </div>
            </div>

            {/* Statistics Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 w-full">
                {/* Total */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-2 flex items-center justify-between hover:shadow-lg hover:scale-105 transition-all duration-300 cursor-pointer">
                    <div className="flex items-center space-x-2">
                        <div className="w-7 h-7 bg-gray-100 dark:bg-gray-700 rounded-md flex items-center justify-center">
                            <svg className="w-4 h-4 text-gray-600 dark:text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Total</span>
                    </div>
                    <span className="text-base font-semibold text-gray-900 dark:text-white">{agentFilteredSessions.length}</span>
                </div>
                {/* Queued */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-2 flex items-center justify-between hover:shadow-lg hover:scale-105 hover:bg-purple-50 dark:hover:bg-purple-900 transition-all duration-300 cursor-pointer">
                    <div className="flex items-center space-x-2">
                        <div className="w-7 h-7 bg-purple-100 dark:bg-purple-900 rounded-md flex items-center justify-center">
                            <svg className="w-4 h-4 text-purple-600 dark:text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Queued</span>
                    </div>
                    <span className="text-base font-semibold text-gray-900 dark:text-white">{agentFilteredSessions.filter(session => session.status === 'queued').length}</span>
                </div>
                {/* Running */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-2 flex items-center justify-between hover:shadow-lg hover:scale-105 hover:bg-green-50 dark:hover:bg-green-900 transition-all duration-300 cursor-pointer">
                    <div className="flex items-center space-x-2">
                        <div className="w-7 h-7 bg-green-100 dark:bg-green-900 rounded-md flex items-center justify-center">
                            <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Running</span>
                    </div>
                    <span className="text-base font-semibold text-gray-900 dark:text-white">{agentFilteredSessions.filter(session => session.status === 'running').length}</span>
                </div>
                {/* Approved */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-2 flex items-center justify-between hover:shadow-lg hover:scale-105 hover:bg-green-50 dark:hover:bg-green-900 transition-all duration-300 cursor-pointer">
                    <div className="flex items-center space-x-2">
                        <div className="w-7 h-7 bg-green-100 dark:bg-green-900 rounded-md flex items-center justify-center">
                            <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Approved</span>
                    </div>
                    <span className="text-base font-semibold text-gray-900 dark:text-white">{agentFilteredSessions.filter(session => session.status === 'approved').length}</span>
                </div>
                {/* Denied */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-2 flex items-center justify-between hover:shadow-lg hover:scale-105 hover:bg-red-50 dark:hover:bg-red-900 transition-all duration-300 cursor-pointer">
                    <div className="flex items-center space-x-2">
                        <div className="w-7 h-7 bg-red-100 dark:bg-red-900 rounded-md flex items-center justify-center">
                            <svg className="w-4 h-4 text-red-600 dark:text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Denied</span>
                    </div>
                    <span className="text-base font-semibold text-gray-900 dark:text-white">{agentFilteredSessions.filter(session => session.status === 'denied').length}</span>
                </div>
                {/* Failed */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-2 flex items-center justify-between hover:shadow-lg hover:scale-105 hover:bg-red-50 dark:hover:bg-red-900 transition-all duration-300 cursor-pointer">
                    <div className="flex items-center space-x-2">
                        <div className="w-7 h-7 bg-red-100 dark:bg-red-900 rounded-md flex items-center justify-center">
                            <svg className="w-4 h-4 text-red-600 dark:text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Failed</span>
                    </div>
                    <span className="text-base font-semibold text-gray-900 dark:text-white">{agentFilteredSessions.filter(session => session.status === 'failed').length}</span>
                </div>
                {/* Manual Action */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-2 flex items-center justify-between hover:shadow-lg hover:scale-105 hover:bg-orange-50 dark:hover:bg-orange-900 transition-all duration-300 cursor-pointer">
                    <div className="flex items-center space-x-2">
                        <div className="w-7 h-7 bg-orange-100 dark:bg-orange-900 rounded-md flex items-center justify-center">
                            <svg className="w-4 h-4 text-orange-600 dark:text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-5.5-2.5a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zM10 12a5.99 5.99 0 00-4.793 2.39A6.483 6.483 0 0010 16.5a6.483 6.483 0 004.793-2.11A5.99 5.99 0 0010 12z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Manual</span>
                    </div>
                    <span className="text-base font-semibold text-gray-900 dark:text-white">{agentFilteredSessions.filter(session => session.status === 'manual-action').length}</span>
                </div>
                {/* Expired */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-2 flex items-center justify-between hover:shadow-lg hover:scale-105 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-300 cursor-pointer">
                    <div className="flex items-center space-x-2">
                        <div className="w-7 h-7 bg-gray-100 dark:bg-gray-900 rounded-md flex items-center justify-center">
                            <svg className="w-4 h-4 text-gray-600 dark:text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-8a1 1 0 012 0v3a1 1 0 01-2 0v-3zm1-4a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Expired</span>
                    </div>
                    <span className="text-base font-semibold text-gray-900 dark:text-white">{agentFilteredSessions.filter(session => session.status === 'expired').length}</span>
                </div>
            </div>

            {/* Sessions Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden w-full">
                <div className="px-2 py-2 border-b border-gray-200">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                        <h2 className="text-base font-semibold text-gray-900">
                            {agentTypeFilter === 'all' ? 'All Requests' : `${getAgentTypeLabel(agentTypeFilter)} Requests`}
                        </h2>
                        <div className="flex flex-wrap gap-1">
                            <button
                                onClick={() => setStatusFilter('all')}
                                className={getFilterButtonClass('all')}
                            >
                                All
                            </button>
                            <button
                                onClick={() => setStatusFilter('submitted')}
                                className={getFilterButtonClass('submitted')}
                            >
                                Submitted
                            </button>
                            <button
                                onClick={() => setStatusFilter('queued')}
                                className={getFilterButtonClass('queued')}
                            >
                                Queued
                            </button>
                            <button
                                onClick={() => setStatusFilter('expired')}
                                className={getFilterButtonClass('expired')}
                            >
                                Expired
                            </button>
                            <button
                                onClick={() => setStatusFilter('running')}
                                className={getFilterButtonClass('running')}
                            >
                                Running
                            </button>
                            <button
                                onClick={() => setStatusFilter('approved')}
                                className={getFilterButtonClass('approved')}
                            >
                                Approved
                            </button>
                            <button
                                onClick={() => setStatusFilter('denied')}
                                className={getFilterButtonClass('denied')}
                            >
                                Denied
                            </button>
                            <button
                                onClick={() => setStatusFilter('manual-action')}
                                className={getFilterButtonClass('manual-action')}
                            >
                                Manual Action
                            </button>
                            <button
                                onClick={() => setStatusFilter('failed')}
                                className={getFilterButtonClass('failed')}
                            >
                                Failed
                            </button>
                        </div>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 text-xs">
                        <thead className="bg-gray-50">
                            <tr>
                                {/* <th className="px-2 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Request ID
                                </th>
                                <th className="px-2 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Batch ID
                                </th>
                                <th className="px-2 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Sequence No
                                </th> */}

                                {/* <th className="px-2 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Total Count
                                </th> */}
                                <th className="px-1 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Appointment ID
                                </th>
                                <th className="px-1 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Patient Name
                                </th>
                                <th className="px-1 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    DOB
                                </th>

                                <th className="px-1 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Date of Service
                                </th>

                                <th className="px-1 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Visit Reason
                                </th>
                                <th className="px-1 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Payer
                                </th>

                                <th className="px-1 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Specialty
                                </th>
                                <th className="px-1 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Status
                                </th>
                                <th className="px-1 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Logs
                                </th>
                                <th className="px-1 py-1 text-left text-[10px] font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {filteredSessions.length === 0 ? (
                                <tr>
                                    <td colSpan={10} className="px-2 py-6 text-center">
                                        <div className="text-gray-500">
                                            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                            </svg>
                                            <h3 className="mt-2 text-sm font-medium text-gray-900">No sessions found</h3>
                                            <p className="mt-1 text-sm text-gray-500">
                                                {agentTypeFilter === 'all' && statusFilter === 'all'
                                                    ? 'No sessions are currently available.'
                                                    : `No sessions found for the selected filters.`}
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                filteredSessions.map((sessionItem) => (
                                    <tr key={sessionItem.id} className={`${getRowBackgroundColor(sessionItem.status)}`}>
                                        {/* <td className="px-2 py-1 whitespace-nowrap">
                                            <span className="text-xs font-mono text-gray-900">
                                                {sessionItem.request_id || '-'}
                                            </span>
                                        </td>
                                        <td className="px-2 py-1 whitespace-nowrap">
                                            <span className="text-xs font-mono text-gray-900">
                                                {sessionItem.batch_id || '-'}
                                            </span>
                                        </td>
                                        <td className="px-2 py-1 whitespace-nowrap text-xs text-gray-900">
                                            {sessionItem.sequence_no || '-'}
                                        </td> */}

                                        {/* <td className="px-2 py-1 whitespace-nowrap text-xs text-gray-900">
                                            {sessionItem.totalCount || '-'}
                                        </td> */}
                                        <td className="px-1 py-1 whitespace-nowrap text-xs text-gray-900">
                                            {sessionItem.apiAppointmentId || '-'}
                                        </td>
                                        {/* Patient Name */}
                                        <td className="px-1 py-1 whitespace-nowrap text-xs text-gray-900">
                                            {sessionItem.apiPatientName || '-'}
                                        </td>
                                        {/* DOB */}
                                        <td className="px-1 py-1 whitespace-nowrap text-xs text-gray-900">
                                            {sessionItem.apiDob || '-'}
                                        </td>
                                        {/* Date of Service */}
                                        <td className="px-1 py-1 whitespace-nowrap text-xs text-gray-900">
                                            {sessionItem.dateOfService || '-'}
                                        </td>
                                        {/* Visit Reason */}
                                        <td className="px-1 py-1 whitespace-nowrap text-xs text-gray-900">
                                            {sessionItem.visitReason || 'Office Visit'}
                                        </td>
                                        {/* Payer (Vendor) */}
                                        <td className="px-1 py-1 whitespace-nowrap text-xs text-gray-900">
                                            {sessionItem.vendor || '-'}
                                        </td>
                                        {/* Specialty */}
                                        <td className="px-1 py-1 whitespace-nowrap text-xs text-gray-900">
                                            {sessionItem.specialty || '-'}
                                        </td>
                                        <td className="px-1 py-1 whitespace-nowrap">
                                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(sessionItem.status)}`}>
                                                {getStatusIcon(sessionItem.status)}
                                                <span className="ml-1 capitalize">
                                                    {sessionItem.status}
                                                </span>
                                            </span>
                                        </td>
                                        <td className="px-1 py-1 whitespace-nowrap text-xs font-medium">

                                            <button
                                                onClick={() => handleLogView(sessionItem)}
                                                className={`inline-flex items-center px-2 py-1 border border-transparent text-xs leading-4 font-medium rounded-md transition-colors disabled:opacity-50 ${sessionItem.status === 'running'
                                                    ? 'text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                                                    : 'text-gray-400 bg-gray-100 cursor-not-allowed'
                                                    }`}
                                            >
                                                {sessionItem.status === 'running' ? 'Live Logs' : 'Logs'}
                                            </button>


                                        </td>
                                        <td className="px-1 py-1 whitespace-nowrap text-xs font-medium">
                                            <button
                                                onClick={() => handleNoVNCConnect(sessionItem)}
                                                disabled={connectingSession === sessionItem.id || (sessionItem.status !== 'manual-action' && sessionItem.status !== 'expired')}
                                                className={`inline-flex items-center px-2 py-1 border border-transparent text-xs leading-4 font-medium rounded-md transition-colors disabled:opacity-50 ${sessionItem.status === 'manual-action'
                                                    ? 'text-white bg-orange-500 hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500'
                                                    : sessionItem.status === 'expired'
                                                        ? 'text-white bg-orange-500 hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500'
                                                        : 'text-gray-400 bg-gray-100 cursor-not-allowed'
                                                    }`}
                                            >
                                                {connectingSession === sessionItem.id ? (
                                                    <>
                                                        <svg className="w-3 h-3 mr-1 animate-spin" fill="currentColor" viewBox="0 0 20 20">
                                                            <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                                        </svg>
                                                        Connecting...
                                                    </>
                                                ) : (
                                                    <>
                                                        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                                            <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" clipRule="evenodd" />
                                                        </svg>
                                                        {sessionItem.status === 'expired'
                                                            ? 'Re-Trigger'
                                                            : sessionItem.status === 'manual-action'
                                                                ? 'Review'
                                                                : 'Review'}
                                                    </>
                                                )}
                                            </button>
                                        </td>
                                    </tr>
                                )))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
