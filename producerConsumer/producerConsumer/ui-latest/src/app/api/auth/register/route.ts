
import { NextRequest, NextResponse } from "next/server"
import bcrypt from "bcryptjs"
import { userService } from "@/services/userService"
import { z } from "zod"

const registerSchema = z.object({
    name: z.string().min(1, "Name is required"),
    email: z.string().email("Invalid email address"),
    password: z.string().min(6, "Password must be at least 6 characters"),
})

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const { name, email, password } = registerSchema.parse(body)

        // Check if user already exists
        const existingUser = await userService.findUserByEmail(email)

        if (existingUser) {
            return NextResponse.json(
                { message: "User with this email already exists" },
                { status: 400 }
            )
        }

        // Hash password
        const hashedPassword = await bcrypt.hash(password, 12)

        // Generate unique 16-digit user ID
        const userId = await userService.generateUniqueUserId()

        // Create user with error handling
        try {
            const user = await userService.createUser({
                name,
                email,
                password: hashedPassword,
                userId,
                role: "USER"
            })

            // Remove password from response
            const { password: _password, ...userWithoutPassword } = user

            return NextResponse.json(
                {
                    message: "User created successfully",
                    user: userWithoutPassword
                },
                { status: 201 }
            )
        } catch (createError: any) {
            // Handle duplicate key errors gracefully
            if (createError.code === 11000 || createError.message?.includes('duplicate')) {
                return NextResponse.json(
                    { message: "A user with this email or ID already exists" },
                    { status: 400 }
                )
            }
            throw createError
        }
    } catch (error) {
        if (error instanceof z.ZodError) {
            return NextResponse.json(
                { message: error.issues[0].message },
                { status: 400 }
            )
        }

        console.error("Registration error:", error)
        return NextResponse.json(
            { message: "Internal server error" },
            { status: 500 }
        )
    }
}
