# PowerShell script to test agent request_id logging
# Run this script to verify the agent logging system

Write-Host "🧪 Agent Request ID Logging Test Suite" -ForegroundColor Cyan
Write-Host "=" * 50

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python available: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Check if required packages are installed
$requiredPackages = @("redis", "aiohttp")
Write-Host "`n📦 Checking required packages..." -ForegroundColor Yellow

foreach ($package in $requiredPackages) {
    try {
        python -c "import $package" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $package is installed" -ForegroundColor Green
        } else {
            Write-Host "❌ $package is not installed" -ForegroundColor Red
            Write-Host "   Install with: pip install $package" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $package is not installed" -ForegroundColor Red
        Write-Host "   Install with: pip install $package" -ForegroundColor Yellow
    }
}

Write-Host "`n🔍 Checking Docker services..." -ForegroundColor Yellow

# Check if Docker is running
try {
    docker ps 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker is running" -ForegroundColor Green
        
        # Check Redis container
        $redisRunning = docker ps --filter "name=redis" --format "table {{.Names}}" | Select-String "redis"
        if ($redisRunning) {
            Write-Host "✅ Redis container is running" -ForegroundColor Green
        } else {
            Write-Host "❌ Redis container not found" -ForegroundColor Red
            Write-Host "   Start with: docker-compose up -d redis" -ForegroundColor Yellow
        }
        
        # Check agent service
        $agentRunning = docker ps --filter "name=browser-use" --format "table {{.Names}}" | Select-String "browser-use"
        if ($agentRunning) {
            Write-Host "✅ Browser-use agent container is running" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Browser-use agent container not found" -ForegroundColor Yellow
            Write-Host "   Start with: docker-compose up -d browser-use-serverless" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Docker is not running" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Docker is not available" -ForegroundColor Red
}

Write-Host "`n" + "=" * 50
Write-Host "🚀 Available Tests:" -ForegroundColor Cyan

Write-Host "`n1. 🔍 Redis Monitor - Watch live agent logs"
Write-Host "   python redis_monitor.py"

Write-Host "`n2. 🧪 Full Test Suite - Comprehensive testing"
Write-Host "   python test_agent_request_id_logging.py"

Write-Host "`n3. 📊 Quick Redis Check - Check existing streams"
Write-Host "   docker exec -it redis-container redis-cli KEYS 'browser_use_logs:*'"

Write-Host "`n4. 🌊 Test SSE Endpoint - Direct SSE testing"
Write-Host "   curl http://localhost:3000/api/v1/stream-logs/request/test_req_123"

Write-Host "`n5. 🤖 Start Test Agent - Create test agent request"
Write-Host "   curl -X POST http://localhost:8000/agents \"
Write-Host "        -H 'Content-Type: application/json' \"
Write-Host "        -d '{\"task\":\"test task\",\"session_id\":\"test_session\",\"request_id\":\"test_req_123\"}'"

Write-Host "`n" + "=" * 50
Write-Host "💡 Recommended Test Flow:" -ForegroundColor Green

Write-Host "`n1. Start the Redis monitor in one terminal:"
Write-Host "   python redis_monitor.py" -ForegroundColor Yellow

Write-Host "`n2. In another terminal, start an agent or run the full test:"
Write-Host "   python test_agent_request_id_logging.py" -ForegroundColor Yellow

Write-Host "`n3. Check the monitor terminal for live logs"

Write-Host "`n4. Verify SSE endpoint with frontend or curl"

Write-Host "`n" + "=" * 50

# Ask user what they want to run
Write-Host "What would you like to run? (1-5 or 'q' to quit): " -NoNewline -ForegroundColor Cyan
$choice = Read-Host

switch ($choice) {
    "1" { 
        Write-Host "`n🔍 Starting Redis Monitor..." -ForegroundColor Green
        python redis_monitor.py 
    }
    "2" { 
        Write-Host "`n🧪 Starting Full Test Suite..." -ForegroundColor Green
        python test_agent_request_id_logging.py 
    }
    "3" { 
        Write-Host "`n📊 Checking Redis streams..." -ForegroundColor Green
        # Try to find Redis container name
        $redisContainer = docker ps --filter "name=redis" --format "{{.Names}}" | Select-Object -First 1
        if ($redisContainer) {
            docker exec -it $redisContainer redis-cli KEYS "browser_use_logs:*"
        } else {
            Write-Host "❌ Redis container not found" -ForegroundColor Red
        }
    }
    "4" { 
        Write-Host "`n🌊 Testing SSE endpoint..." -ForegroundColor Green
        Write-Host "Testing with curl..." -ForegroundColor Yellow
        curl.exe "http://localhost:3000/api/v1/stream-logs/request/test_req_123" -H "Accept: text/event-stream"
    }
    "5" { 
        Write-Host "`n🤖 Creating test agent request..." -ForegroundColor Green
        $testRequest = @{
            task = "Test agent logging with request_id"
            session_id = "test_session_123"
            request_id = "test_req_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        } | ConvertTo-Json
        
        Write-Host "Request payload:" -ForegroundColor Yellow
        Write-Host $testRequest
        
        try {
            Invoke-RestMethod -Uri "http://localhost:8000/agents" -Method POST -Body $testRequest -ContentType "application/json"
        } catch {
            Write-Host "❌ Failed to create agent request: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    "q" { 
        Write-Host "`n👋 Goodbye!" -ForegroundColor Green
        exit 0 
    }
    default { 
        Write-Host "`n❌ Invalid choice. Please run the script again." -ForegroundColor Red 
    }
}

Write-Host "`n✅ Test completed!" -ForegroundColor Green
