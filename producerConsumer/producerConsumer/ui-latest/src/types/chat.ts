// API Response Types
export interface ApiResponse {
    status: 'success' | 'error' | 'incomplete'
    message: string
    Intent?: string | null
    patient_id?: string | null
    payer?: any | null
    data?: any
    // Legacy fields for backward compatibility
    purpose?: 'pre_authorization' | 'other' | null
    name?: string | null
}

// Intent Detection Response from external API
export interface IntentDetectionResponse {
    status: 'success' | 'error' | 'incomplete'
    message: string
    Intent?: string | null
    patient_id?: string | null
    payer?: any | null
    data?: any
}

// Enhanced Message Interface
export interface ChatMessage {
    id: string
    content: string
    sender: 'user' | 'agent'
    timestamp: Date
    type?: 'text' | 'error' | 'success' | 'incomplete'
    apiResponse?: ApiResponse
}

// Chat Status
export type ChatStatus = 'idle' | 'typing' | 'processing' | 'error'
