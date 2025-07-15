const io = require('socket.io-client');

// Kết nối đến server
const socket = io("http://0.0.0.0:9000", {
  transports: ['websocket', 'polling']
});

// Test data
const testData = {
  id: "7521631307152084231_3",
  topic_name: "Vinamilk",
  type: "newsTopic",
  topic_id: "5cd2a99d2e81050a12e5339a",
  site_id: "7427331267015197703",
  site_name: "baothegioisua",
  title: "Vinamilk dính nghi vấn lừa đảo cộng tác viên qua app nhập liệu",
  content: "Nhiều người phản ánh bị treo tiền, không hoàn tiền khi làm cộng tác viên qua nền tảng app được cho là của Vinamilk. Một số nghi ngờ đây là hình thức lừa đảo tinh vi.",
  description: "",
  is_kol: false,
  total_interactions: 57
};

// Xử lý khi kết nối thành công
socket.on("connect", () => {
  console.log("✅ Connected to server, Socket ID:", socket.id);
  
  // Test sequence
  runTests();
});

async function runTests() {
  console.log("\n🧪 Starting tests...");
  
  // Test 1: Single analyze (first time - no cache)
  console.log("\n1️⃣ Testing single analyze (no cache)...");
  socket.emit("analyze_negative", testData);
  
  // Test 2: Same analyze (should use cache)
  setTimeout(() => {
    console.log("\n2️⃣ Testing single analyze (with cache)...");
    socket.emit("analyze_negative", testData);
  }, 2000);
  
  // Test 3: Batch analyze
  setTimeout(() => {
    console.log("\n3️⃣ Testing batch analyze...");
    const batchData = [
      { ...testData, id: "item_1", title: "Title 1" },
      { ...testData, id: "item_2", title: "Title 2" },
      { ...testData, id: "item_3", title: "Title 3" }
    ];
    socket.emit("batch_analyze_negative", batchData);
  }, 4000);
  
  // Test 4: Get cache stats
  setTimeout(() => {
    console.log("\n4️⃣ Getting cache stats...");
    socket.emit("get_cache_stats");
  }, 6000);
  
  // Test 5: Clear cache
  setTimeout(() => {
    console.log("\n5️⃣ Clearing cache...");
    socket.emit("clear_cache");
  }, 8000);
}

// Event handlers
socket.on("connection_status", (data) => {
  console.log("🔌 Connection status:", data);
});

socket.on("analyze_result", (data) => {
  console.log("📊 Analyze result:");
  console.log(`   - Processing time: ${data.processing_time}s`);
  console.log(`   - Cache hit rate: ${data.cache_stats?.hit_rate}%`);
  console.log(`   - Contains topic: ${data.contains_topic}`);
  console.log(`   - Should call LLM: ${data.should_call_llm}`);
});

socket.on("batch_analyze_result", (data) => {
  console.log("📦 Batch analyze result:");
  console.log(`   - Count: ${data.count}`);
  console.log(`   - Processing time: ${data.processing_time}s`);
  console.log(`   - Cache hit rate: ${data.cache_stats?.hit_rate}%`);
});

socket.on("cache_stats", (data) => {
  console.log("📈 Cache stats:", data);
});

socket.on("cache_cleared", (data) => {
  console.log("🗑️ Cache cleared:", data);
});

socket.on("disconnect", () => {
  console.log("❌ Disconnected from server");
});

socket.on("connect_error", (error) => {
  console.error("❌ Connection error:", error.message);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🔌 Closing socket connection...');
  socket.close();
  process.exit(0);
});