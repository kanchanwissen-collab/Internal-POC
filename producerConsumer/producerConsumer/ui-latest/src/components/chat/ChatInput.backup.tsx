"use client"

import { useState, useEffect } from "react"
import { useRouter, usePathname, useSearchParams } from "next/navigation"
import toast from "react-hot-toast"

interface ChatInputProps {
    onSubmit?: (message: string) => void
    isLoading?: boolean
}

interface NavigationMessage {
    id: string
    content: string
    sender: 'user' | 'assistant'
    timestamp: Date
    actions?: NavigationAction[]
}

interface NavigationAction {
    text: string
    type: 'navigate' | 'filter' | 'external'
    href?: string
    onClick?: () => void
}

export default function ChatInput({ onSubmit }: ChatInputProps) {
    const [message, setMessage] = useState("")
    const [messages, setMessages] = useState<NavigationMessage[]>([])
    const [isProcessing, setIsProcessing] = useState(false)
    const router = useRouter()
    const pathname = usePathname()
    const searchParams = useSearchParams()

    const navigationOptions = [
        {
            title: "Show My Tasks",
            description: "View all your current tasks and sessions",
            icon: "📋",
            category: "navigation"
        },
        {
            title: "Filter Tasks",
            description: "Filter tasks by status, type, or date",
            icon: "�",
            category: "filter"
        },
        {
            title: "Quick Actions",
            description: "Access common actions and workflows",
            icon: "⚡",
            category: "actions"
        },
        {
            title: "Help & Navigation",
            description: "Get help navigating the application",
            icon: "❓",
            category: "help"
        }
    ]

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!message.trim() || isLoading || chatStatus === 'processing') return

        const userMessage = message.trim()
        setMessage("")

        // Add user message to chat
        const userChatMessage: ChatMessage = {
            id: Date.now().toString(),
            content: userMessage,
            sender: 'user',
            timestamp: new Date(),
            type: 'text'
        }
        setMessages(prev => [...prev, userChatMessage])

        // Call legacy onSubmit if provided
        onSubmit?.(userMessage)

        // Set typing status
        setChatStatus('typing')

        try {
            // Call API
            const apiResponse = await sendChatMessage(userMessage)

            // Create agent response message
            const agentMessage: ChatMessage = {
                id: (Date.now() + 1).toString(),
                content: apiResponse.message,
                sender: 'agent',
                timestamp: new Date(),
                type: apiResponse.status === 'success' ? 'success' :
                    apiResponse.status === 'error' ? 'error' : 'incomplete',
                apiResponse
            }

            setMessages(prev => [...prev, agentMessage])
            setChatStatus('idle')

            // Call onApiResponse callback if provided
            onApiResponse?.(apiResponse, userMessage)

            // Show appropriate toast
            if (apiResponse.status === 'success') {
                toast.success('Request processed successfully!')
            } else if (apiResponse.status === 'incomplete') {
                toast.error(apiResponse.message)
            } else {
                toast.error(apiResponse.message)
            }

        } catch (error) {
            setChatStatus('error')
            const errorMessage: ChatMessage = {
                id: (Date.now() + 2).toString(),
                content: 'Sorry, I encountered an error while processing your request. Please try again.',
                sender: 'agent',
                timestamp: new Date(),
                type: 'error'
            }
            setMessages(prev => [...prev, errorMessage])
            toast.error('Failed to process request')

            setTimeout(() => setChatStatus('idle'), 2000)
        }
    }

    const handleSuggestionClick = async (suggestion: typeof suggestions[0]) => {
        const suggestionText = `${suggestion.title}: ${suggestion.description}`
        setMessage(suggestionText)

        // Auto-submit the suggestion
        const fakeEvent = { preventDefault: () => { } } as React.FormEvent
        await handleSubmit(fakeEvent)
    }

    return (
        <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
            {/* Chat Messages Area */}
            {messages.length > 0 && (
                <div className="flex-1 overflow-y-auto p-6 max-h-96">
                    <div className="max-w-4xl mx-auto space-y-4">
                        {messages.map((msg) => (
                            <div
                                key={msg.id}
                                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div
                                    className={`max-w-[80%] rounded-lg px-4 py-2 ${msg.sender === 'user'
                                        ? 'bg-blue-600 text-white'
                                        : msg.type === 'success'
                                            ? 'bg-green-50 text-green-800 border border-green-200'
                                            : msg.type === 'error'
                                                ? 'bg-red-50 text-red-800 border border-red-200'
                                                : msg.type === 'incomplete'
                                                    ? 'bg-yellow-50 text-yellow-800 border border-yellow-200'
                                                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
                                        }`}
                                >
                                    <p className="text-sm">{msg.content}</p>
                                    {msg.apiResponse && (msg.apiResponse.patient_id || msg.apiResponse.payer || (msg.apiResponse.Intent && msg.apiResponse.Intent !== 'greetings')) && (
                                        <div className="mt-2 text-xs opacity-75">
                                            {msg.apiResponse.Intent && msg.apiResponse.Intent !== 'greetings' && <div>Intent: {msg.apiResponse.Intent}</div>}
                                            {msg.apiResponse.patient_id && <div>Patient ID: {msg.apiResponse.patient_id}</div>}
                                            {msg.apiResponse.payer && <div>Payer: {typeof msg.apiResponse.payer === 'string' ? msg.apiResponse.payer : JSON.stringify(msg.apiResponse.payer)}</div>}
                                        </div>
                                    )}
                                    <div className="text-xs opacity-60 mt-1">
                                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>
                                </div>
                            </div>
                        ))}

                        {/* Typing Indicator */}
                        {chatStatus === 'typing' && (
                            <div className="flex justify-start">
                                <div className="bg-white dark:bg-gray-800 rounded-lg px-4 py-2 border border-gray-200 dark:border-gray-700">
                                    <div className="flex items-center space-x-2">
                                        <div className="flex space-x-1">
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                        </div>
                                        <span className="text-sm text-gray-500">Medical Assistant is typing...</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Suggestions (only show when no messages) */}
            {messages.length === 0 && (
                <div className="flex-1 p-6">
                    <div className="max-w-4xl mx-auto">
                        <div className="text-center mb-8">
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                                How can I help you today?
                            </h2>
                            <p className="text-gray-600 dark:text-gray-400">
                                Choose a suggestion below or type your own request
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                            {suggestions.map((suggestion, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleSuggestionClick(suggestion)}
                                    disabled={chatStatus === 'processing'}
                                    className="p-4 text-left bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-md transition-all duration-200 group disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <div className="flex items-start space-x-3">
                                        <span className="text-2xl">{suggestion.icon}</span>
                                        <div>
                                            <h3 className="font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
                                                {suggestion.title}
                                            </h3>
                                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                                {suggestion.description}
                                            </p>
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Chat Input */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-6 bg-white dark:bg-gray-800">
                <div className="max-w-4xl mx-auto">
                    <form onSubmit={handleSubmit} className="flex space-x-4">
                        <div className="flex-1 relative">
                            <textarea
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                placeholder={
                                    chatStatus === 'typing' ? "Medical Assistant is typing..." :
                                        chatStatus === 'processing' ? "Processing..." :
                                            "Type your message here..."
                                }
                                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 resize-none"
                                rows={3}
                                disabled={isLoading || chatStatus === 'typing' || chatStatus === 'processing'}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault()
                                        handleSubmit(e)
                                    }
                                }}
                            />
                            <div className="absolute bottom-2 right-2 text-xs text-gray-400 dark:text-gray-500">
                                Press Enter to send, Shift+Enter for new line
                            </div>
                        </div>
                        <button
                            type="submit"
                            disabled={!message.trim() || isLoading || chatStatus === 'typing' || chatStatus === 'processing'}
                            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center space-x-2 disabled:cursor-not-allowed"
                        >
                            {isLoading || chatStatus === 'typing' || chatStatus === 'processing' ? (
                                <>
                                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    <span>
                                        {chatStatus === 'typing' ? 'Typing...' :
                                            chatStatus === 'processing' ? 'Processing...' : 'Sending...'}
                                    </span>
                                </>
                            ) : (
                                <>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                    </svg>
                                    <span>Send</span>
                                </>
                            )}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    )
}
