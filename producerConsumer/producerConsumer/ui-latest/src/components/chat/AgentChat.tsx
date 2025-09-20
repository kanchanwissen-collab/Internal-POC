"use client"

import { useState, useRef, useEffect } from "react"
import toast from "react-hot-toast"
import { ChatMessage, ChatStatus, ApiResponse } from "@/types/chat"
import { sendChatMessage } from "@/services/chatApi"

interface AgentChatProps {
    messages?: ChatMessage[]
    onSendMessage?: (message: string) => void
    isLoading?: boolean
    isCollapsed?: boolean
    onToggleCollapse?: () => void
    onApiResponse?: (response: ApiResponse, userMessage: string) => void
}

export default function AgentChat({
    messages: externalMessages = [],
    onSendMessage,
    isLoading = false,
    isCollapsed = false,
    onToggleCollapse,
    onApiResponse
}: AgentChatProps) {
    const [newMessage, setNewMessage] = useState("")
    const [internalMessages, setInternalMessages] = useState<ChatMessage[]>([])
    const [chatStatus, setChatStatus] = useState<ChatStatus>('idle')
    const messagesEndRef = useRef<HTMLDivElement>(null)

    // Use external messages if provided, otherwise use internal state
    const messages = externalMessages.length > 0 ? externalMessages : internalMessages

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!newMessage.trim() || isLoading || chatStatus === 'typing' || chatStatus === 'processing') return

        const userMessage = newMessage.trim()
        setNewMessage("")

        // Create user message
        const userChatMessage: ChatMessage = {
            id: Date.now().toString(),
            content: userMessage,
            sender: 'user',
            timestamp: new Date(),
            type: 'text'
        }

        // Add to internal messages if using internal state
        if (externalMessages.length === 0) {
            setInternalMessages(prev => [...prev, userChatMessage])
        }

        // Call external handler if provided
        onSendMessage?.(userMessage)

        // Only handle API calls if using internal message state
        if (externalMessages.length === 0) {
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

                setInternalMessages(prev => [...prev, agentMessage])
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
                setInternalMessages(prev => [...prev, errorMessage])
                toast.error('Failed to process request')

                setTimeout(() => setChatStatus('idle'), 2000)
            }
        }
    }

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                <div className="flex items-center space-x-3">
                    <div className="relative">
                        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                        </div>
                        <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white dark:border-gray-900 ${isLoading || chatStatus === 'typing' ? 'bg-yellow-400' :
                            chatStatus === 'error' ? 'bg-red-400' : 'bg-green-400'
                            }`}></div>
                    </div>
                    <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">AI Assistant</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                            {isLoading || chatStatus === 'typing' ? 'Typing...' :
                                chatStatus === 'error' ? 'Error' : 'Online'}
                        </p>
                    </div>
                </div>
                <div className="flex items-center">
                    {onToggleCollapse && (
                        <button
                            onClick={onToggleCollapse}
                            className="p-2 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                            aria-label={isCollapsed ? 'Expand AI Assistant' : 'Collapse AI Assistant'}
                        >
                            <svg
                                className={`w-5 h-5 text-gray-600 dark:text-gray-400 transition-transform duration-200 ${isCollapsed ? 'rotate-180' : ''
                                    }`}
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                            </svg>
                        </button>
                    )}
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                    <div className="flex items-center justify-center h-full">
                        <div className="text-center text-gray-500 dark:text-gray-400">
                            <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                            <p>No messages yet</p>
                            <p className="text-sm">Start a conversation with the AI assistant</p>
                        </div>
                    </div>
                ) : (
                    messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${message.sender === 'user'
                                    ? 'bg-blue-600 text-white'
                                    : message.type === 'success'
                                        ? 'bg-green-50 text-green-800 border border-green-200'
                                        : message.type === 'error'
                                            ? 'bg-red-50 text-red-800 border border-red-200'
                                            : message.type === 'incomplete'
                                                ? 'bg-yellow-50 text-yellow-800 border border-yellow-200'
                                                : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                                    }`}
                            >
                                <p className="text-sm">{message.content}</p>
                                {message.apiResponse && (message.apiResponse.patient_id || message.apiResponse.payer || (message.apiResponse.Intent && message.apiResponse.Intent !== 'greetings')) && (
                                    <div className="mt-2 text-xs opacity-75 border-t border-current pt-2">
                                        {message.apiResponse.Intent && message.apiResponse.Intent !== 'greetings' && <div>Intent: {message.apiResponse.Intent}</div>}
                                        {message.apiResponse.patient_id && <div>Patient ID: {message.apiResponse.patient_id}</div>}
                                        {message.apiResponse.payer && <div>Payer: {typeof message.apiResponse.payer === 'string' ? message.apiResponse.payer : JSON.stringify(message.apiResponse.payer)}</div>}
                                    </div>
                                )}
                                <p className={`text-xs mt-1 ${message.sender === 'user'
                                    ? 'text-blue-100'
                                    : 'text-gray-500 dark:text-gray-400'
                                    }`}>
                                    {formatTime(message.timestamp)}
                                </p>
                            </div>
                        </div>
                    ))
                )}

                {/* Typing Indicator */}
                {(isLoading || chatStatus === 'typing' || chatStatus === 'processing') && (
                    <div className="flex justify-start">
                        <div className="bg-gray-100 dark:bg-gray-700 rounded-lg px-4 py-2">
                            <div className="flex items-center space-x-2">
                                <div className="flex space-x-1">
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                </div>
                                <span className="text-sm text-gray-500">
                                    {chatStatus === 'processing' ? 'Processing...' : 'AI Assistant is typing...'}
                                </span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-4">
                <form onSubmit={handleSubmit} className="flex space-x-2">
                    <input
                        type="text"
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        placeholder={
                            chatStatus === 'typing' ? "AI is typing..." :
                                chatStatus === 'processing' ? "Processing..." :
                                    "Type a message..."
                        }
                        className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                        disabled={isLoading || chatStatus === 'typing' || chatStatus === 'processing'}
                    />
                    <button
                        type="submit"
                        disabled={!newMessage.trim() || isLoading || chatStatus === 'typing' || chatStatus === 'processing'}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md font-medium transition-colors disabled:cursor-not-allowed"
                    >
                        {isLoading || chatStatus === 'typing' || chatStatus === 'processing' ? (
                            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        ) : (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                            </svg>
                        )}
                    </button>
                </form>
            </div>
        </div>
    )
}
