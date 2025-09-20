import "next-auth"
import "next-auth/jwt"

declare module "next-auth" {
    interface User {
        userId: string
        role: string
    }

    interface Session {
        user: {
            id: string
            userId: string
            role: string
        } & DefaultSession["user"]
    }
}

declare module "next-auth/jwt" {
    interface JWT {
        userId: string
        role: string
    }
}
