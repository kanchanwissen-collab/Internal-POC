import { MongoClient, Db, Collection, ObjectId } from 'mongodb'
import clientPromise from '@/lib/mongodb'

export interface User {
    _id?: ObjectId
    userId: string
    name: string
    email: string
    password: string
    role: string
    emailVerified?: Date
    image?: string
    createdAt: Date
    updatedAt: Date
}

class UserService {
    private client: MongoClient | null = null
    private db: Db | null = null
    private users: Collection<User> | null = null

    async getDb() {
        if (!this.client) {
            this.client = await clientPromise
            this.db = this.client.db('medical_assistant')
            this.users = this.db.collection<User>('users')
        }
        return { db: this.db, users: this.users }
    }

    async createUser(userData: Omit<User, '_id' | 'createdAt' | 'updatedAt'>) {
        const { users } = await this.getDb()

        const user: User = {
            ...userData,
            createdAt: new Date(),
            updatedAt: new Date()
        }

        const result = await users!.insertOne(user)
        return { ...user, _id: result.insertedId }
    }

    async findUserByEmail(email: string) {
        const { users } = await this.getDb()
        return await users!.findOne({ email })
    }

    async findUserByUserId(userId: string) {
        const { users } = await this.getDb()
        return await users!.findOne({ userId })
    }

    async findUserById(id: string) {
        const { users } = await this.getDb()
        return await users!.findOne({ _id: new ObjectId(id) })
    }

    async updateUser(id: string, updateData: Partial<User>) {
        const { users } = await this.getDb()

        const result = await users!.updateOne(
            { _id: new ObjectId(id) },
            {
                $set: {
                    ...updateData,
                    updatedAt: new Date()
                }
            }
        )

        return result.modifiedCount > 0
    }

    async deleteUser(id: string) {
        const { users } = await this.getDb()

        const result = await users!.deleteOne({ _id: new ObjectId(id) })
        return result.deletedCount > 0
    }

    async generateUniqueUserId(): Promise<string> {
        const maxAttempts = 10
        let attempts = 0

        while (attempts < maxAttempts) {
            const userId = Math.random().toString().slice(2, 18).padStart(16, '0')
            const existing = await this.findUserByUserId(userId)

            if (!existing) {
                return userId
            }

            attempts++
        }

        throw new Error('Failed to generate unique user ID')
    }
}

export const userService = new UserService()
