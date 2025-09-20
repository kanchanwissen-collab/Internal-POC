// Test registration with direct MongoDB
import { userService } from '../src/services/userService.js';
import bcrypt from 'bcryptjs';

async function testDirectMongoDB() {
    try {
        console.log('🧪 Testing direct MongoDB user registration...');

        // Generate a test user
        const testUser = {
            name: 'Test User Direct',
            email: `testdirect${Date.now()}@example.com`,
            password: await bcrypt.hash('password123', 12),
            userId: await userService.generateUniqueUserId(),
            role: 'USER'
        };

        console.log('📝 Creating user:', {
            name: testUser.name,
            email: testUser.email,
            userId: testUser.userId,
            role: testUser.role
        });

        const user = await userService.createUser(testUser);

        console.log('✅ User created successfully:', {
            id: user._id.toString(),
            name: user.name,
            email: user.email,
            userId: user.userId,
            role: user.role,
        });

        // Test finding user by email
        const foundUser = await userService.findUserByEmail(user.email);
        console.log('🔍 Found user by email:', foundUser ? 'Yes' : 'No');

        // Test authentication
        const isPasswordValid = await bcrypt.compare('password123', foundUser.password);
        console.log('🔐 Password validation:', isPasswordValid ? 'Valid' : 'Invalid');

        // Clean up - delete the test user
        await userService.deleteUser(user._id.toString());
        console.log('🧹 Test user cleaned up');
        console.log('✅ Direct MongoDB test passed!');

    } catch (error) {
        console.error('❌ Direct MongoDB test failed:', error);
    }
}

testDirectMongoDB();
