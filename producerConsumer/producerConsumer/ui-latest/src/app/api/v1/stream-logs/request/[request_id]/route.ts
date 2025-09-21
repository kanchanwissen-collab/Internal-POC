import { NextRequest, NextResponse } from 'next/server';
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL || 'redis://redis:6379');

export async function GET(
  request: NextRequest,
  { params }: { params: { request_id: string } }
) {
  const { request_id } = params;

  console.log(`🔗 SSE connection request for request_id: ${request_id}`);
  console.log(`📍 Redis URL: ${process.env.REDIS_URL || 'redis://redis:6379'}`);

  const encoder = new TextEncoder();
  
  const stream = new ReadableStream({
    start(controller) {
      console.log(`🚀 Starting SSE stream for request_id: ${request_id}`);
      
      const sendEvent = (data: any) => {
        const payload = `data: ${JSON.stringify(data)}\n\n`;
        console.log(`📤 Sending SSE event: ${data.type} for ${request_id}`);
        controller.enqueue(encoder.encode(payload));
      };

      // Send initial connection event
      sendEvent({ 
        type: 'connected', 
        request_id,
        message: `Connected to logs for request ${request_id}`,
        timestamp: new Date().toISOString()
      });

      // Subscribe to Redis streams for this request
      const subscriber = redis.duplicate();
      
      // Subscribe to the logs channel for this request (matches agent.py pattern)
      const logChannel = `browser_use_logs:${request_id}`;
      console.log(`🎧 Attempting to subscribe to Redis channel: ${logChannel}`);
      
      subscriber.subscribe(logChannel, (err) => {
        if (err) {
          console.error(`❌ Redis subscription error for ${logChannel}:`, err);
          sendEvent({
            type: 'error',
            message: `Failed to subscribe to logs: ${err.message}`,
            timestamp: new Date().toISOString()
          });
        } else {
          console.log(`✅ Successfully subscribed to ${logChannel}`);
          sendEvent({
            type: 'status',
            message: `Subscribed to Redis channel: ${logChannel}`,
            timestamp: new Date().toISOString()
          });
        }
      });

      // Handle incoming messages from Redis
      subscriber.on('message', (channel, message) => {
        try {
          // Try to parse as JSON first (if PUBSUB_JSON=1 in agent)
          const logData = JSON.parse(message);
          
          // Handle enhanced JSON format from agent.py
          sendEvent({
            type: 'log',
            data: {
              level: 'INFO',
              message: logData.msg || message,
              source: logData.agent_name || 'browser-agent',
              request_id: logData.request_id || request_id,
              timestamp: logData.timestamp || new Date().toISOString(),
              log_source: logData.source || 'logger'
            },
            timestamp: new Date().toISOString(),
            channel: channel
          });
        } catch (error) {
          // Handle plain text messages (if PUBSUB_JSON=0)
          sendEvent({
            type: 'log',
            data: {
              level: 'INFO',
              message: message,
              source: 'browser-agent',
              request_id: request_id,
              log_source: 'text'
            },
            timestamp: new Date().toISOString(),
            channel: channel
          });
        }
      });

      // Handle Redis connection errors
      subscriber.on('error', (error) => {
        console.error(`❌ Redis subscriber error for ${request_id}:`, error);
        sendEvent({
          type: 'error',
          message: `Redis error: ${error.message}`,
          timestamp: new Date().toISOString()
        });
      });

      // Handle Redis connection status
      subscriber.on('connect', () => {
        console.log(`✅ Redis connected for request_id: ${request_id}`);
        sendEvent({
          type: 'status',
          message: 'Redis connection established',
          timestamp: new Date().toISOString()
        });
      });

      subscriber.on('ready', () => {
        console.log(`🚀 Redis ready for request_id: ${request_id}`);
      });

      subscriber.on('close', () => {
        console.log(`🔌 Redis connection closed for request_id: ${request_id}`);
      });

      // Handle client disconnect
      request.signal.addEventListener('abort', () => {
        console.log(`👋 Client disconnected from logs:${request_id}`);
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
