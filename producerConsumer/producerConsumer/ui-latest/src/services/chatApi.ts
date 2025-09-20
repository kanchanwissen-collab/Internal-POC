import { ApiResponse, IntentDetectionResponse } from '@/types/chat'

// API endpoints
const LEGACY_API_ENDPOINT = '/api/chat/process'
const INTENT_DETECTION_ENDPOINT = '/api/chat/detect-intent'

export async function sendChatMessage(message: string): Promise<ApiResponse> {
    try {
        const response = await fetch(INTENT_DETECTION_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data: IntentDetectionResponse = await response.json()

        // Transform the response to match ApiResponse interface
        const apiResponse: ApiResponse = {
            status: data.status,
            message: data.message,
            Intent: data.Intent,
            patient_id: data.patient_id,
            payer: data.payer,
            data: data.data,
            // Legacy fields for backward compatibility
            purpose: data.Intent === 'pre_authorization' ? 'pre_authorization' : 'other',
            name: data.patient_id
        }

        return apiResponse
    } catch (error) {
        console.error('Error sending chat message:', error)
        throw new Error('Failed to send message')
    }
}

// Legacy function for backward compatibility
export async function sendLegacyChatMessage(message: string): Promise<ApiResponse> {
    try {
        const response = await fetch(LEGACY_API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        return data
    } catch (error) {
        console.error('Error sending legacy chat message:', error)
        throw new Error('Failed to send message')
    }
}
