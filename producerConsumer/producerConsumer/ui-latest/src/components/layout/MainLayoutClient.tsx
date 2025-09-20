"use client"

import { useState } from "react"
import { usePathname } from "next/navigation"
import { User } from "next-auth"
import AgentChat from "@/components/chat/AgentChat"

interface MainLayoutClientProps {
    children: React.ReactNode
    user?: User
}

export default function MainLayoutClient({ children, user: _user }: MainLayoutClientProps) {
    const pathname = usePathname()
    const [isRightPanelCollapsed, setIsRightPanelCollapsed] = useState(true) // Start with modal closed


    return (
        <div className="h-full relative overflow-y-auto">
            {/* Main Content Area */}
            <div className="p-6">
                {children}
            </div>

            {/* AI Assistant Toggle Button - Fixed Position */}
            {(
                <button
                    onClick={() => setIsRightPanelCollapsed(!isRightPanelCollapsed)}
                    className="fixed top-20 right-6 p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 z-40"
                    aria-label={isRightPanelCollapsed ? 'Open AI Assistant' : 'Close AI Assistant'}
                >
                    {isRightPanelCollapsed ? (
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                    ) : (
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    )}
                </button>
            )}

            {/* AI Assistant Modal Overlay */}
            {!isRightPanelCollapsed && (
                <div className="fixed inset-y-0 right-0 w-96 bg-white dark:bg-gray-800 shadow-2xl z-50 border-l border-gray-200 dark:border-gray-700 transition-all duration-300 ease-in-out transform translate-x-0">
                    <div className="h-full">
                        <AgentChat
                            isCollapsed={isRightPanelCollapsed}
                            onToggleCollapse={() => setIsRightPanelCollapsed(!isRightPanelCollapsed)}
                        />
                    </div>
                </div>
            )}
        </div>
    )
}
