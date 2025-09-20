import { NextRequest, NextResponse } from 'next/server';
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL || 'redis://redis:6379');

export async function GET(
  request: NextRequest,
  { params }: { params: { batch_id: string } }
) {
  const { batch_id } = params;

  const encoder = new TextEncoder();
  
  const stream = new ReadableStream({
    start(controller) {
      const sendEvent = (data: any) => {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify(data)}\n\n`)
        );
      };

      // Send initial connection event
      sendEvent({ 
        type: 'connected', 
        batch_id,
        message: `Connected to logs for batch ${batch_id}`,
        timestamp: new Date().toISOString()
      });

      // Subscribe to Redis streams for this batch
      const subscriber = redis.duplicate();
      
      // Subscribe to the logs channel for this batch
      subscriber.subscribe(`browser_use_logs:${batch_id}`, (err) => {
        if (err) {
          console.error('Redis subscription error:', err);
          sendEvent({
            type: 'error',
            message: `Failed to subscribe to logs: ${err.message}`,
            timestamp: new Date().toISOString()
          });
        } else {
          console.log(`Subscribed to browser_use_logs:${batch_id}`);
        }
      });

      // Handle incoming messages from Redis
      subscriber.on('message', (channel, message) => {
        try {
          const logData = JSON.parse(message);
          sendEvent({
            type: 'log',
            data: logData,
            timestamp: new Date().toISOString(),
            channel: channel
          });
        } catch (error) {
          // Handle plain text messages
          sendEvent({
            type: 'log',
            data: {
              level: 'INFO',
              message: message,
              source: 'browser-use'
            },
            timestamp: new Date().toISOString(),
            channel: channel
          });
        }
      });

      // Handle Redis connection errors
      subscriber.on('error', (error) => {
        console.error('Redis subscriber error:', error);
        sendEvent({
          type: 'error',
          message: `Redis error: ${error.message}`,
          timestamp: new Date().toISOString()
        });
      });

      // Handle client disconnect
      request.signal.addEventListener('abort', () => {
        console.log(`Client disconnected from logs:${batch_id}`);
        subscriber.unsubscribe();
        subscriber.disconnect();
        controller.close();
      });

      // Send periodic heartbeat
      const heartbeat = setInterval(() => {
        try {
          sendEvent({
            type: 'heartbeat',
            timestamp: new Date().toISOString()
          });
        } catch (error) {
          clearInterval(heartbeat);
        }
      }, 30000); // Every 30 seconds

      // Clean up heartbeat on disconnect
      request.signal.addEventListener('abort', () => {
        clearInterval(heartbeat);
      });
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET',
      'Access-Control-Allow-Headers': 'Cache-Control',
    },
  });
}
