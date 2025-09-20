"use client"

import { useState } from "react"
import { signIn } from "next-auth/react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import toast from 'react-hot-toast'

export default function LoginForm() {
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState("")
    const router = useRouter()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError("")

        const loadingToast = toast.loading('Signing in...')

        try {
            const result = await signIn("credentials", {
                email,
                password,
                redirect: false,
            })

            toast.dismiss(loadingToast)

            if (result?.error) {
                setError("Invalid credentials. Please try again.")
                toast.error("Invalid credentials. Please try again.")
            } else {
                toast.success("Successfully signed in!")
                router.push("/history")
                router.refresh()
            }
        } catch (_error) {
            toast.dismiss(loadingToast)
            setError("An error occurred. Please try again.")
            toast.error("An error occurred. Please try again.")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
            {/* Professional Background Pattern */}
            <div className="absolute inset-0 bg-white"></div>
            <div className="absolute inset-0" style={{
                backgroundImage: `radial-gradient(circle at 1px 1px, rgba(156, 163, 175, 0.15) 1px, transparent 0)`,
                backgroundSize: '20px 20px'
            }}></div>

            {/* Main Login Container */}
            <div className="w-full max-w-md relative z-10">
                {/* Professional Login Box */}
                <div className="bg-white rounded-lg shadow-lg border border-gray-200 px-10 py-12">
                    {/* Corporate Header */}
                    <div className="text-center mb-10">
                        <div className="mx-auto w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-6 border-2 border-slate-200">
                            <svg className="w-8 h-8 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-semibold text-gray-900 mb-2 tracking-tight">
                            Sign In
                        </h2>
                        <p className="text-gray-600 text-sm">
                            Please sign in to your account
                        </p>
                    </div>
                    {/* Professional Login Form */}
                    <form className="space-y-6" onSubmit={handleSubmit}>
                        <div className="space-y-6">
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                                    Email Address
                                </label>
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    autoComplete="email"
                                    required
                                    className="w-full px-4 py-3 text-base border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-slate-500 transition-colors bg-white"
                                    placeholder="Enter your email address"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>
                            <div>
                                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                                    Password
                                </label>
                                <input
                                    id="password"
                                    name="password"
                                    type="password"
                                    autoComplete="current-password"
                                    required
                                    className="w-full px-4 py-3 text-base border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-slate-500 transition-colors bg-white"
                                    placeholder="Enter your password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="rounded-md bg-red-50 p-4 border border-red-200">
                                <div className="text-sm text-red-600 text-center">{error}</div>
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-slate-800 text-white py-3 px-4 rounded-md text-base font-medium hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                        >
                            {isLoading ? (
                                <div className="flex items-center justify-center">
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Signing in...
                                </div>
                            ) : "Sign In"}
                        </button>

                        {/* Professional Register Link */}
                        <div className="text-center pt-6 border-t border-gray-200">
                            <p className="text-sm text-gray-600">
                                Don&apos;t have an account?{" "}
                                <Link
                                    href="/register"
                                    className="font-medium text-slate-600 hover:text-slate-800 transition-colors"
                                >
                                    Create an account
                                </Link>
                            </p>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    )
}
