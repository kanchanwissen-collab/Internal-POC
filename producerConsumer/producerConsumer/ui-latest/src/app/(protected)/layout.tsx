import { redirect } from "next/navigation"
import { auth } from "@/lib/auth"
import Sidebar from "@/components/layout/Sidebar"
import TopNavbar from "@/components/layout/TopNavbar"
import MainLayoutClient from "@/components/layout/MainLayoutClient"
import { ThemeProvider } from "@/providers/ThemeProvider"
import SSEProvider from "@/providers/SSEProvider"
import NotificationProvider from "@/providers/NotificationProvider"
import ToastProvider from "@/components/providers/ToastProvider"

export default async function ProtectedLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const session = await auth()

    // If user is not logged in, redirect to login
    if (!session) {
        redirect("/login")
    }

    return (
        <ThemeProvider>
            <ToastProvider />
            <NotificationProvider>
                <SSEProvider serverUrl={`${process.env.NEXT_PUBLIC_API_URL}/api/v1`} showToastNotifications={true}>
                    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
                        <Sidebar user={session.user} />
                        <div className="flex-1 flex flex-col min-h-0 pl-20">
                            <TopNavbar user={session.user} />
                            <main className="flex-1 min-h-0">
                                <MainLayoutClient user={session.user}>
                                    {children}
                                </MainLayoutClient>
                            </main>
                        </div>
                    </div>
                </SSEProvider>
            </NotificationProvider>
        </ThemeProvider>
    )
}
