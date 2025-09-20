import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
    try {
        const { message } = await request.json()

        if (!message || typeof message !== 'string') {
            return NextResponse.json(
                { error: 'Message is required and must be a string' },
                { status: 400 }
            )
        }

        // Simulate processing delay
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000))

        const lowerMessage = message.toLowerCase()

        // Check if the user intent is related to pre-authorization
        if (!lowerMessage.includes('preauth') && 
            !lowerMessage.includes('pre-auth') && 
            !lowerMessage.includes('authorization') &&
            !lowerMessage.includes('pre auth') &&
            !lowerMessage.includes('preauthorization')) {
            
            return NextResponse.json({
                status: "error",
                message: "User intent is not related to pre-authorization.",
                purpose: "other",
                name: null,
                payer: null,
                data: null
            })
        }

        // Extract name - look for patterns like "name is John" or "patient John Doe"
        let extractedName = null
        const namePatterns = [
            /(?:name\s+is\s+|patient\s+(?:name\s+)?is\s+|for\s+patient\s+)([A-Za-z]+(?:\s+[A-Za-z]+)?)/i,
            /\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b/,
        ]
        
        for (const pattern of namePatterns) {
            const match = message.match(pattern)
            if (match) {
                extractedName = match[1].trim()
                break
            }
        }

        // Extract payer - look for insurance companies or "payer is X"
        let extractedPayer = null
        const payerPatterns = [
            /(?:payer\s+is\s+|insurance\s+is\s+|with\s+)([A-Za-z]+(?:\s+[A-Za-z]+)?)/i,
            /\b(aetna|cigna|cohere|blue\s+cross|united|humana|anthem|kaiser)\b/i,
        ]
        
        for (const pattern of payerPatterns) {
            const match = message.match(pattern)
            if (match) {
                extractedPayer = match[1].trim()
                break
            }
        }

        // Check if we have all required details
        if (extractedName && extractedPayer) {
            return NextResponse.json({
                status: "success",
                message: "All required details provided. Proceeding with automation.",
                purpose: "pre_authorization",
                name: extractedName,
                payer: extractedPayer,
                data: null
            })
        }

        // Determine what's missing
        const missing = []
        if (!extractedName) missing.push('patient name')
        if (!extractedPayer) missing.push('payer')

        return NextResponse.json({
            status: "incomplete",
            message: `Missing required details: ${missing.join(', ')}.`,
            purpose: "pre_authorization",
            name: extractedName,
            payer: extractedPayer,
            data: null
        })

    } catch (error) {
        console.error('Chat API error:', error)
        return NextResponse.json(
            { 
                status: "error",
                message: "Internal server error occurred while processing your request.",
                purpose: "other",
                name: null,
                payer: null,
                data: null
            },
            { status: 500 }
        )
    }
}
