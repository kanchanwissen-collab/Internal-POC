# Batch Processing API with Outbox Pattern

A production-ready FastAPI server implementing the Outbox Pattern for reliable batch JSON processing with MongoDB and Pub/Sub integration.

## 🔹 **Batch-Aware Outbox Pattern Implementation**

### **Flow Overview:**

1. **Batch Ingest (Writer Service)**
   - Assigns sequential `batch_sequence` number for ordering
   - Assigns sequential `item_sequence` within each batch
   - Extracts `request_id` from each JSON request
   - Inserts batch metadata and batch_items into MongoDB in a single transaction
   - Items have status: "pending", sent: False, publish_id: None
   - Commits transaction ✅
   - No messages sent to Pub/Sub yet

2. **Publisher Worker (Batch-Aware Outbox Processor)**
   - 🔹 **Sequential Batch Processing**: Finds oldest batch with status="pending" by `batch_sequence`
   - 🔹 **Complete Batch Processing**: Processes ALL items in that batch before moving to next
   - 🔹 **Ordered Item Processing**: Processes items within batch by `item_sequence`
   - Publishes items one-by-one to Pub/Sub with full request context:
     ```json
     {
       "batch_id": "a9a7551c40fd44eb",
       "item_id": "uuid", 
       "request_id": "4473",
       "vendor_name": "EVICORE",
       "payload": { ...full JSON... }
     }
     ```
   - On success: updates item with sent=True, publish_id, sent_at
   - Once ALL items in batch are sent=True: updates batch status="committed"
   - 🔹 **Then (and only then)** moves to next batch

### **Why Batch-Aware Processing:**

✅ **Guarantees processing order**: Batch 1 fully sent → then Batch 2  
✅ **Prevents partial data leaks**: No downstream systems see incomplete batches  
✅ **Easy failure recovery**: Retry only failed requests in a batch  
✅ **Batch boundaries**: Downstream systems can reason about complete batches  
✅ **Request traceability**: Each request tied to batch_id with original request_id

## Features

- **Single Endpoint**: Simple POST endpoint for batch submission
- **MongoDB Storage**: Transactional storage with outbox pattern
- **Automatic Metadata**: 16-digit UUID batch ID and timestamp
- **Vendor Analytics**: Counts requests grouped by vendor
- **Outbox Processing**: Background worker for reliable message delivery
- **Monitoring**: APIs to monitor outbox status and batch progress

## API Endpoints

### **Core Processing**
- **POST** `/api/v1/batch/process` - Submit batch for processing

### **Outbox Monitoring**
- **GET** `/api/v1/outbox/status` - Get batch-aware processor status
- **POST** `/api/v1/outbox/start` - Start batch-aware processor
- **POST** `/api/v1/outbox/stop` - Stop batch-aware processor
- **GET** `/api/v1/outbox/pending-batches` - View pending batches in processing order
- **GET** `/api/v1/outbox/batch/{batch_id}/status` - Get detailed batch status
- **GET** `/api/v1/outbox/batch/{batch_id}/items` - Get batch items in processing order

### **System**
- **GET** `/health` - Health check
- **GET** `/metrics` - System metrics
- **GET** `/docs` - API documentation

## Quick Start

### 1. Prerequisites
```bash
# Start MongoDB
docker-compose up -d
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Server
```bash
python main.py
```

### 4. Test Batch-Aware Outbox Pattern
```bash
python scripts/test_batch_aware_outbox.py
```

## MongoDB Collections

### **batches** Collection
```json
{
  "_id": ObjectId,
  "batch_id": "abcd1234efgh5678",
  "created_at": ISODate,
  "total_items": 100,
  "vendor_counts": {"EVICORE": 50, "Cohere": 50},
  "status": "pending|processing|committed|failed",
  "processing_time_ms": 15.67,
  "committed_at": ISODate,
  "batch_sequence": 1
}
```

### **batch_items** Collection
```json
{
  "_id": ObjectId,
  "item_id": "uuid",
  "batch_id": "abcd1234efgh5678",
  "request_id": "4473",
  "request_data": {...},
  "vendor_name": "EVICORE",
  "status": "pending|sent|failed",
  "sent": false,
  "publish_id": null,
  "created_at": ISODate,
  "sent_at": ISODate,
  "item_sequence": 1
}
```

## Configuration

Environment variables (`.env`):

```env
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=batch_processing
MONGODB_BATCH_COLLECTION=batches
MONGODB_ITEMS_COLLECTION=batch_items

# Outbox Pattern Configuration
OUTBOX_POLL_INTERVAL_SECONDS=5
OUTBOX_BATCH_SIZE=100
ENABLE_OUTBOX_PROCESSOR=true
```

## Usage Examples

### Submit Batch for Processing
```bash
curl -X POST "http://localhost:8000/api/v1/batch/process" \
     -H "Content-Type: application/json" \
     -d @your_batch_data.json
```

### Monitor Outbox Status
```bash
curl "http://localhost:8000/api/v1/outbox/status"
```

### Check Batch Progress
```bash
curl "http://localhost:8000/api/v1/outbox/batch/{batch_id}/status"
```

## Response Example

```json
{
  "status": "success",
  "message": "Batch processed successfully with metadata",
  "data": {
    "batch_id": "0520273745064b63",
    "timestamp": "2025-08-22T12:19:19.086074",
    "total_json_objects": 100,
    "vendor_counts": {
      "EVICORE": 50,
      "Cohere": 50
    },
    "unique_vendors": 2,
    "processing_time_ms": 0.44
  }
}
```

## Monitoring

### Batch Status Lifecycle
1. **pending** - Items stored, waiting for outbox processor
2. **processing** - Outbox processor sending items
3. **committed** - All items successfully sent
4. **failed** - Processing failed

### Item Status Lifecycle
1. **pending** - Waiting to be sent
2. **sent** - Successfully published to Pub/Sub
3. **failed** - Publishing failed (will retry)

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HTTP Request  │───▶│  Writer Service │───▶│    MongoDB      │
│   (Batch JSON)  │    │  (Transaction)  │    │   (Outbox)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Pub/Sub      │◀───│ Outbox Processor│◀───│  Poll Unsent    │
│   (Messages)    │    │  (Background)   │    │     Items       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Production Considerations

1. **Database**: MongoDB with replica set for transactions
2. **Pub/Sub**: Replace MockPubSubService with actual service
3. **Monitoring**: Add metrics collection and alerting
4. **Scaling**: Multiple outbox processor instances
5. **Error Handling**: Dead letter queues for failed items
6. **Security**: Authentication and authorization

## Dependencies

- **FastAPI**: Web framework
- **Motor**: Async MongoDB driver  
- **PyMongo**: MongoDB driver
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server
