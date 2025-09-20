// Test registration without transactions
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function testRegistration() {
    try {
        console.log('🧪 Testing user registration without transactions...');

        // Generate a test user
        const testUser = {
            name: 'Test User',
            email: `test${Date.now()}@example.com`,
            password: 'hashedpassword123',
            userId: Math.random().toString().slice(2, 18).padStart(16, '0'),
        };

        console.log('📝 Creating user:', { name: testUser.name, email: testUser.email, userId: testUser.userId });

        const user = await prisma.user.create({
            data: testUser,
        });

        console.log('✅ User created successfully:', {
            id: user.id,
            name: user.name,
            email: user.email,
            userId: user.userId,
        });

        // Clean up - delete the test user
        await prisma.user.delete({
            where: { id: user.id },
        });

        console.log('🧹 Test user cleaned up');
        console.log('✅ Registration test passed!');

    } catch (error) {
        console.error('❌ Registration test failed:', error);
    } finally {
        await prisma.$disconnect();
    }
}

testRegistration();
