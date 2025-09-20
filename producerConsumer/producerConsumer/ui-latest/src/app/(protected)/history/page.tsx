"use client"

import { useState, useEffect, useRef } from "react"
import { useSession } from "next-auth/react"
import toast from 'react-hot-toast'

type SessionStatus = 'submitted' | 'queued' | 'expired' | 'running' | 'failed' | 'approved' | 'denied' | 'manual-action';

// New type for the API response
interface DashboardApiItem {
    created_at: string;
    current_step: string | null;
    last_updated: string;
    patient_name: string;
    payer_id: string;
    request_id: string;
    status: string;
    user_actions_pending: number;
}

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

    // Simulate loading sessions data
    useEffect(() => {
        const fetchSessions = async () => {
            setIsLoading(true)
            toast.dismiss('agent-sessions-loaded')

            try {
                // Fetch data from dashboard endpoint only
                console.log('Fetching from dashboard endpoint...');
                const dashboardResponse = await fetch('http://localhost:8001/api/dashboard/requests');
                console.log('Dashboard Response status:', dashboardResponse.status);
                
                if (!dashboardResponse.ok) {
                    throw new Error(`Dashboard API failed: ${dashboardResponse.status}`);
                }
                
                const dashboardData: DashboardApiItem[] = await dashboardResponse.json();
                console.log('Dashboard API Response:', dashboardData);
                
                // Map data from dashboard API
                const formattedSessions: Session[] = dashboardData.map((req: DashboardApiItem) => {
                    
                    return {
                        id: req.request_id,
                        sessionId: req.request_id, // Use request_id as sessionId since batch_id doesn't exist
                        status: (req.status as SessionStatus) || 'queued',
                        createdAt: req.created_at || new Date().toISOString(),
                        lastActivity: req.last_updated || req.created_at || new Date().toISOString(),
                        patientName: req.patient_name || "Unknown",
                        dateOfBirth: "-",
                        providerName: "-",
                        serviceType: "-",
                        memberId: "-",
                        appointmentId: "-",
                        agentType: 'PRIOR_AUTH',
                        vendor: req.payer_id || "Unknown",
                        sequence_no: "1", // Default sequence number
                        request_id: req.request_id,
                        batch_id: req.request_id, // Use request_id as batch_id fallback
                        manual_actions: [], // Empty array as fallback
                    };
                });
                
                console.log('Final merged sessions:', formattedSessions);

                setSessions(formattedSessions);
            } catch (error) {
                console.error("Failed to fetch sessions:", error);
                toast.error("Failed to fetch sessions, using fallback data.");
                setSessions(mockSessions);
            } finally {
                setIsLoading(false);
            }

            // Show success message when sessions are loaded (only once)
            if (!toastShownRef.current) {
                const runningCount = sessions.filter(session => session.status === 'running').length
                toast.success(`📊 Loaded ${sessions.length} history sessions (${runningCount} running)`, {
                    duration: 3000,
                    id: 'history-sessions-loaded'
                })
                toastShownRef.current = true
            }
        }

        fetchSessions()
    }, [])

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
        const query = new URLSearchParams({
            status: sessionItem.status,
            patientName: sessionItem.patientName || 'N/A',
            providerName: sessionItem.providerName || 'N/A',
            serviceType: sessionItem.serviceType || 'N/A',
            agentType: getAgentTypeLabel(sessionItem.agentType),
            createdAt: sessionItem.createdAt,
            lastActivity: sessionItem.lastActivity,
        }).toString();

        const logUrl = `/logs/${sessionItem.sessionId}?${query}`;
        window.open(logUrl, '_blank');
    };

    const handleNoVNCConnect = (sessionItem: Session) => {
        if (sessionItem.status !== 'manual-action' && sessionItem.status !== 'expired') {
            toast.error(`Cannot connect to ${sessionItem.status} session`)
            return
        }

        if (sessionItem.status === 'manual-action') {
            toast(`⚠️ Session requires manual action - connecting anyway`, {
                icon: '👨‍💼',
                duration: 4000,
                style: {
                    background: '#FEF3C7',
                    color: '#92400E',
                }
            })
        }

        setConnectingSession(sessionItem.id)
        toast.loading(`Connecting to session ${sessionItem.sessionId}...`, {
            id: `connect-${sessionItem.id}`,
            duration: 2000
        })

        // Simulate connection process
        setTimeout(() => {
            // In a real application, this would open the noVNC viewer
            // For now, we'll just simulate opening a new window
            const noVncUrl = `https://novnc.example.com/vnc.html?host=session-${sessionItem.id}&port=5900&autoconnect=true`

            try {
                window.open(noVncUrl, '_blank', 'width=1024,height=768,resizable=yes,scrollbars=yes')
                toast.success(`Successfully connected to session ${sessionItem.sessionId}`, {
                    id: `connect-${sessionItem.id}`,
                    duration: 3000
                })
            } catch (_error) {
                toast.error(`Failed to open noVNC connection`, {
                    id: `connect-${sessionItem.id}`,
                    duration: 4000
                })
            }

            setConnectingSession(null)
        }, 2000)
    }

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
        <div className="container-fluid px-4 space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 w-full">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white">History</h1>
                    <p className="text-gray-600 dark:text-gray-300 mt-2">
                        Monitor and review sessions across different departments
                    </p>
                </div>
                <div className="flex items-center space-x-4 mt-4 sm:mt-0">
                    {/* Date Filter */}
                    <div className="flex items-center space-x-2">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Filter by Date:</label>
                        <select
                            value={dateFilter}
                            onChange={(e) => setDateFilter(e.target.value as 'all' | 'today' | 'week' | 'month')}
                            className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 w-full">
                {/* <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4"> Categories</h3> */}
                <div className="flex flex-wrap gap-3 w-full">
                    <button
                        onClick={() => setAgentTypeFilter('all')}
                        className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${agentTypeFilter === 'all'
                            ? 'bg-indigo-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                    >
                        <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" clipRule="evenodd" />
                        </svg>
                        All  ({sessions.length})
                    </button>

                    <button
                        onClick={() => setAgentTypeFilter('PRIOR_AUTH')}
                        className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${agentTypeFilter === 'PRIOR_AUTH'
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
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-8 gap-2 w-full">
                {/* Total */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-3 hover:shadow-lg hover:scale-105 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-300 cursor-pointer">
                    <div className="flex flex-col items-center text-center">
                        <div className="flex-shrink-0">
                            <div className="w-6 h-6 bg-gray-100 dark:bg-gray-700 rounded-md flex items-center justify-center">
                                <svg className="w-4 h-4 text-gray-600 dark:text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" clipRule="evenodd" />
                                </svg>
                            </div>
                        </div>
                        <div className="mt-2 min-w-0 flex-1">
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 truncate">Total</p>
                            <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                {agentFilteredSessions.length}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Queued */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-3 hover:shadow-lg hover:scale-105 hover:bg-purple-50 dark:hover:bg-purple-900 transition-all duration-300 cursor-pointer">
                    <div className="flex flex-col items-center text-center">
                        <div className="flex-shrink-0">
                            <div className="w-6 h-6 bg-purple-100 dark:bg-purple-900 rounded-md flex items-center justify-center">
                                <svg className="w-4 h-4 text-purple-600 dark:text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                                </svg>
                            </div>
                        </div>
                        <div className="mt-2 min-w-0 flex-1">
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 truncate">Queued</p>
                            <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                {agentFilteredSessions.filter(session => session.status === 'queued').length}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Running */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-3 hover:shadow-lg hover:scale-105 hover:bg-green-50 dark:hover:bg-green-900 transition-all duration-300 cursor-pointer">
                    <div className="flex flex-col items-center text-center">
                        <div className="flex-shrink-0">
                            <div className="w-6 h-6 bg-green-100 dark:bg-green-900 rounded-md flex items-center justify-center">
                                <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                            </div>
                        </div>
                        <div className="mt-2 min-w-0 flex-1">
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 truncate">Running</p>
                            <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                {agentFilteredSessions.filter(session => session.status === 'running').length}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Approved */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-3 hover:shadow-lg hover:scale-105 hover:bg-green-50 dark:hover:bg-green-900 transition-all duration-300 cursor-pointer">
                    <div className="flex flex-col items-center text-center">
                        <div className="flex-shrink-0">
                            <div className="w-6 h-6 bg-green-100 dark:bg-green-900 rounded-md flex items-center justify-center">
                                <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                            </div>
                        </div>
                        <div className="mt-2 min-w-0 flex-1">
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 truncate">Approved</p>
                            <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                {agentFilteredSessions.filter(session => session.status === 'approved').length}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Denied */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-3 hover:shadow-lg hover:scale-105 hover:bg-red-50 dark:hover:bg-red-900 transition-all duration-300 cursor-pointer">
                    <div className="flex flex-col items-center text-center">
                        <div className="flex-shrink-0">
                            <div className="w-6 h-6 bg-red-100 dark:bg-red-900 rounded-md flex items-center justify-center">
                                <svg className="w-4 h-4 text-red-600 dark:text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                            </div>
                        </div>
                        <div className="mt-2 min-w-0 flex-1">
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 truncate">Denied</p>
                            <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                {agentFilteredSessions.filter(session => session.status === 'denied').length}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Failed */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-3 hover:shadow-lg hover:scale-105 hover:bg-red-50 dark:hover:bg-red-900 transition-all duration-300 cursor-pointer">
                    <div className="flex flex-col items-center text-center">
                        <div className="flex-shrink-0">
                            <div className="w-6 h-6 bg-red-100 dark:bg-red-900 rounded-md flex items-center justify-center">
                                <svg className="w-4 h-4 text-red-600 dark:text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                            </div>
                        </div>
                        <div className="mt-2 min-w-0 flex-1">
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 truncate">Failed</p>
                            <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                {agentFilteredSessions.filter(session => session.status === 'failed').length}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Manual Action */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-3 hover:shadow-lg hover:scale-105 hover:bg-orange-50 dark:hover:bg-orange-900 transition-all duration-300 cursor-pointer">
                    <div className="flex flex-col items-center text-center">
                        <div className="flex-shrink-0">
                            <div className="w-6 h-6 bg-orange-100 dark:bg-orange-900 rounded-md flex items-center justify-center">
                                <svg className="w-4 h-4 text-orange-600 dark:text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-5.5-2.5a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zM10 12a5.99 5.99 0 00-4.793 2.39A6.483 6.483 0 0010 16.5a6.483 6.483 0 004.793-2.11A5.99 5.99 0 0010 12z" clipRule="evenodd" />
                                </svg>
                            </div>
                        </div>
                        <div className="mt-2 min-w-0 flex-1">
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 truncate">Manual</p>
                            <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                {agentFilteredSessions.filter(session => session.status === 'manual-action').length}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Expired */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-3 hover:shadow-lg hover:scale-105 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-300 cursor-pointer">
                    <div className="flex flex-col items-center text-center">
                        <div className="flex-shrink-0">
                            <div className="w-6 h-6 bg-gray-100 dark:bg-gray-900 rounded-md flex items-center justify-center">
                                <svg className="w-4 h-4 text-gray-600 dark:text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-8a1 1 0 012 0v3a1 1 0 01-2 0v-3zm1-4a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                                </svg>
                            </div>
                        </div>
                        <div className="mt-2 min-w-0 flex-1">
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 truncate">Expired</p>
                            <p className="text-lg font-semibold text-gray-900 dark:text-white">
                                {agentFilteredSessions.filter(session => session.status === 'expired').length}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Sessions Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden w-full">
                <div className="px-6 py-4 border-b border-gray-200">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <h2 className="text-lg font-semibold text-gray-900">
                            {agentTypeFilter === 'all' ? 'All Requests' : `${getAgentTypeLabel(agentTypeFilter)} Requests`}
                        </h2>
                        <div className="flex flex-wrap gap-2">
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
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Request ID
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Batch ID
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Sequence No
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Vendor
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Agent Type
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Created
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Last Activity
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Status
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Logs
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {filteredSessions.length === 0 ? (
                                <tr>
                                    <td colSpan={10} className="px-6 py-12 text-center">
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
                                        <td className="px-6 py-2 whitespace-nowrap">
                                            <span className="text-sm font-mono text-gray-900">
                                                {sessionItem.request_id || '-'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-2 whitespace-nowrap">
                                            <span className="text-sm font-mono text-gray-900">
                                                {sessionItem.batch_id || '-'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-2 whitespace-nowrap text-sm text-gray-900">
                                            {sessionItem.sequence_no || '-'}
                                        </td>
                                        <td className="px-6 py-2 whitespace-nowrap text-sm text-gray-900">
                                            {sessionItem.vendor || '-'}
                                        </td>
                                        <td className="px-6 py-2 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="flex-shrink-0 h-6 w-6 text-gray-500">
                                                    {getAgentTypeIcon(sessionItem.agentType)}
                                                </div>
                                                <div className="ml-2">
                                                    <span className="text-sm font-medium text-gray-900">
                                                        {getAgentTypeLabel(sessionItem.agentType)}
                                                    </span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-2 whitespace-nowrap text-sm text-gray-500">
                                            {formatDate(sessionItem.createdAt)}
                                        </td>
                                        <td className="px-6 py-2 whitespace-nowrap text-sm text-gray-500">
                                            {formatDate(sessionItem.lastActivity)}
                                        </td>
                                        <td className="px-6 py-2 whitespace-nowrap">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(sessionItem.status)}`}>
                                                {getStatusIcon(sessionItem.status)}
                                                <span className="ml-1 capitalize">
                                                    {sessionItem.status}
                                                </span>
                                            </span>
                                        </td>
                                        <td className="px-6 py-2 whitespace-nowrap text-sm font-medium">
                                            <button
                                                onClick={() => handleLogView(sessionItem)}
                                                disabled={sessionItem.status !== 'running'}
                                                className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md transition-colors disabled:opacity-50 ${sessionItem.status === 'running'
                                                    ? 'text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
                                                    : 'text-gray-400 bg-gray-100 cursor-not-allowed'
                                                    }`}
                                            >
                                                {sessionItem.status === 'running' ? 'Live Logs' : 'Logs'}
                                            </button>
                                        </td>
                                        <td className="px-6 py-2 whitespace-nowrap text-sm font-medium">
                                            <button
                                                onClick={() => handleNoVNCConnect(sessionItem)}
                                                disabled={connectingSession === sessionItem.id || (sessionItem.status !== 'manual-action' && sessionItem.status !== 'expired')}
                                                className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md transition-colors disabled:opacity-50 ${sessionItem.status === 'manual-action'
                                                    ? 'text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'
                                                    : sessionItem.status === 'expired'
                                                        ? 'text-white bg-orange-500 hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500'
                                                        : 'text-gray-400 bg-gray-100 cursor-not-allowed'
                                                    }`}
                                            >
                                                {connectingSession === sessionItem.id ? (
                                                    <>
                                                        <svg className="w-4 h-4 mr-2 animate-spin" fill="currentColor" viewBox="0 0 20 20">
                                                            <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                                        </svg>
                                                        Connecting...
                                                    </>
                                                ) : (
                                                    <>
                                                        <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                                            <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" clipRule="evenodd" />
                                                        </svg>
                                                        {sessionItem.status === 'expired' ? 'Re-Trigger' : 'Take Action'}
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
