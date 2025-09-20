"use client"

import { Toaster } from 'react-hot-toast'

export default function ToastProvider() {
    return (
        <Toaster
            position="top-right"
            reverseOrder={false}
            gutter={8}
            containerClassName=""
            containerStyle={{}}
            toastOptions={{
                // Define default options
                className: '',
                duration: 4000,
                style: {
                    background: '#fff',
                    color: '#363636',
                    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
                    borderRadius: '6px',
                    border: '1px solid rgba(0, 0, 0, 0.05)',
                    padding: '12px 16px',
                    fontSize: '14px',
                    fontWeight: '500',
                },
                // Default options for specific types
                success: {
                    duration: 3000,
                    style: {
                        background: '#f0fdf4',
                        color: '#166534',
                        border: '1px solid #bbf7d0',
                        boxShadow: '0 1px 3px 0 rgba(34, 197, 94, 0.1)',
                    },
                    iconTheme: {
                        primary: '#22c55e',
                        secondary: '#f0fdf4',
                    },
                },
                error: {
                    duration: 5000,
                    style: {
                        background: '#fef2f2',
                        color: '#dc2626',
                        border: '1px solid #fecaca',
                        boxShadow: '0 1px 3px 0 rgba(239, 68, 68, 0.1)',
                    },
                    iconTheme: {
                        primary: '#ef4444',
                        secondary: '#fef2f2',
                    },
                },
                loading: {
                    style: {
                        background: '#f8fafc',
                        color: '#475569',
                        border: '1px solid #e2e8f0',
                        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
                    },
                },
            }}
        />
    )
}
