import { redirect } from "next/navigation"
import { auth } from "@/lib/auth"

export default async function AuthLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const session = await auth()

    // If user is already logged in, redirect to history
    if (session) {
        redirect("/history")
    }

    return <>{children}</>
}
