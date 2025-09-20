// MongoDB connection test
const { MongoClient } = require('mongodb');
require('dotenv').config();

const client = new MongoClient(process.env.DATABASE_URL);

async function testMongoConnection() {
    try {
        console.log('🔗 Attempting to connect to MongoDB...');
        console.log('📍 Connection URL:', process.env.DATABASE_URL?.replace(/\/\/.*@/, '//***:***@'));

        await client.connect();
        console.log('✅ Connected to MongoDB successfully');

        const db = client.db();
        const result = await db.admin().ping();
        console.log('✅ MongoDB ping successful:', result);

        // Test database operations
        const collections = await db.listCollections().toArray();
        console.log('📚 Available collections:', collections.map(c => c.name));

        // Test if we can create a test collection
        const testCollection = db.collection('connection_test');
        await testCollection.insertOne({ test: true, timestamp: new Date() });
        console.log('✅ Test write operation successful');

        await testCollection.deleteMany({ test: true });
        console.log('✅ Test cleanup successful');

        return true;
    } catch (error) {
        console.error('❌ MongoDB connection failed:', error.message);
        return false;
    } finally {
        await client.close();
        console.log('🔒 Connection closed');
    }
}

// Run the test
testMongoConnection().then(success => {
    process.exit(success ? 0 : 1);
});
