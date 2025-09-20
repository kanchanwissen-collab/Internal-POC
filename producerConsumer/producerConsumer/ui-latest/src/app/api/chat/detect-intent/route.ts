import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/lib/auth'

export async function POST(request: NextRequest) {
    try {
        // Get the current session to extract user_id
        const session = await auth()

        if (!session || !session.user) {
            return NextResponse.json(
                { error: 'Unauthorized. Please login to continue.' },
                { status: 401 }
            )
        }

        const { message } = await request.json()

        if (!message || typeof message !== 'string') {
            return NextResponse.json(
                { error: 'Message is required and must be a string' },
                { status: 400 }
            )
        }

        // Extract user_id from session
        const user_id = session.user.userId

        if (!user_id) {
            return NextResponse.json(
                { error: 'User ID not found in session' },
                { status: 400 }
            )
        }

        // Call external intent detection API with both message and user_id
        const response = await fetch('http://localhost:8000/detect_intent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: message,
                user_id: user_id
            }),
        })

        if (!response.ok) {
            console.error(`External API error: ${response.status}`)
            return NextResponse.json({
                status: "error",
                message: "Failed to process intent detection. Please try again.",
                Intent: null,
                patient_id: null,
                payer: null,
                data: null
            })
        }

        const data = await response.json()

        // Return the response from the external API
        return NextResponse.json(data)

    } catch (error) {
        console.error('Intent detection API error:', error)
        return NextResponse.json({
            status: "error",
            message: "An error occurred while processing your request. Please try again.",
            Intent: null,
            patient_id: null,
            payer: null,
            data: null
        })
    }
}
