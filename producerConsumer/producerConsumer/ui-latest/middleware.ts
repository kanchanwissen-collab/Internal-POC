import { auth } from "@/lib/auth"

export default auth((req) => {
    const { nextUrl } = req
    const isLoggedIn = !!req.auth

    // Define public routes that don't require authentication
    const publicRoutes = [
        "/",
        "/login",
        "/register",
    ]

    // API auth routes
    const authApiRoutes = [
        "/api/auth",
    ]

    // Check if the route is an API auth route
    if (nextUrl.pathname.startsWith("/api/auth")) {
        return
    }

    // Check if the route is public
    const isPublicRoute = publicRoutes.includes(nextUrl.pathname)

    // If user is not logged in and trying to access a protected route
    if (!isLoggedIn && !isPublicRoute) {
        return Response.redirect(new URL("/login", nextUrl))
    }

    // If user is logged in and trying to access auth pages, redirect to history
    if (isLoggedIn && (nextUrl.pathname === "/login" || nextUrl.pathname === "/register")) {
        return Response.redirect(new URL("/history", nextUrl))
    }
})

// Optionally, don't invoke Middleware on some paths
export const config = {
    matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}
