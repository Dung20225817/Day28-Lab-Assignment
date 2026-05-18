# Hướng Dẫn Nộp Bài - Lab #28: Full Platform Integration Sprint

## Yêu Cầu Nộp Bài

**Full AI infrastructure platform demo** - từ data ingestion đến model serving với full observability.

## Các Artifacts Cần Nộp

### 1. Source Code
- Folder `lab28/` hoàn chỉnh với tất cả files
- Tất cả integration scripts hoạt động
- Prefect flows đã deploy và schedule

### 2. Screenshots Demo
Chụp màn hình các bước:
- Prefect UI: http://localhost:4200 (flow đang chạy)
- API Gateway call: `curl http://localhost:8000/health`
- Grafana dashboard: http://localhost:3000

### 3. Kết Quả Smoke Tests
Chạy và chụp màn hình kết quả:
```bash
cd lab28
pytest smoke-tests/ -v
```
Kỳ vọng: 5/5 tests passing

### 4. Production Readiness Score
```bash
python scripts/production_readiness_check.py
```
Kỳ vọng: Score >80%

### 5. Documentation
- `README.md` giải thích cách:
  - Start platform: `docker compose up -d`
  - Deploy Prefect flows
  - Run smoke tests
  - Access dashboards (Grafana:3000, Prometheus:9090, Prefect:4200)

## Định Dạng Nộp Bài

Tạo Repo GitHub chứa:
```
lab28_submission_[student_id]
├── lab28/                    # Source code hoàn chỉnh
│   ├── docker-compose.yml
│   ├── prefect/flows/
│   ├── scripts/
│   ├── api-gateway/
│   └── monitoring/
├── screenshots/              # Screenshots demo
│   ├── prefect_ui.png
│   ├── api_gateway.png
│   └── grafana_dashboard.png
├── smoke_tests_results.png   # Screenshot kết quả pytest
├── production_readiness.png  # Screenshot readiness score
└── README.md                # Hướng dẫn setup
```

## Địa Điểm Nộp
Nộp link repo GitHub qua LMS

## Tiêu Chí Chấm Điểm

| Tiêu Chí | Trọng Số | Mô Tả |
|----------|----------|-------|
| Integration Completeness | 40% | Tất cả 10 integration points hoạt động, data flow end-to-end |
| Observability | 25% | Logs, metrics, traces hiển thị; alerts configured |
| Performance | 20% | Latency trong SLO; load tested; không có memory leaks |
| Architecture Quality | 15% | Clean separation, GitOps config, documented decisions |

## Các Vấn Đề Cần Tránh

- Config drift giữa các environments
- Thiếu error handling tại integration points
- Monitoring coverage không hoàn chỉnh
- Không có rollback strategy
- Demo không test trước khi nộp

## 5 Câu Hỏi Cần Trả Lời Khi Nộp

1. **Phân tích các trade-offs trong thiết kế kiến trúc AI platform của bạn. Bạn đã cân bằng giữa performance, reliability, và maintainability như thế nào?**

**Trả lời:**

Kiến trúc hybrid Local + Kaggle có các trade-offs chính:
- **Performance:** Dùng Kaggle GPU T4 (miễn phí) cho vLLM inference thay vì cloud provider đắt tiền → tiết kiệm cost nhưng GPU không always-on.
- **Reliability:** Local stack (Kafka, Qdrant, Redis) chạy liên tục đảm bảo data pipeline không phụ thuộc Kaggle. vLLM trên Kaggle là optional - nếu down, API vẫn trả về lỗi thay vì crash hoàn toàn.
- **Maintainability:** Prefect quản lý orchestration tập trung, docker-compose đóng gói local services, Prefect worker chạy trong container tách biệt với host.

Trade-off cụ thể: API Gateway gọi `httpx.AsyncClient(timeout=30)` đến Kaggle vLLM - timeout 30s là balance giữa việc đợi đủ lâu cho model response và không block quá lâu user.

2. **Trong kiến trúc hybrid (Local + Kaggle), bạn xử lý ngắt kết nối giữa local và Kaggle như thế nào? Có cơ chế fallback không?**

**Trả lời:**

Có fallback: Khi Kaggle vLLM không available (timeout hoặc không kết nối được), `/api/v1/chat` endpoint sẽ raise exception từ `httpx` và trả về HTTP 500 cho client thay vì crash toàn bộ service. Health endpoint luôn trả `{"status":"ok"}` độc lập với vLLM.

Tunnel ngrok/cloudflared đảm bảo local có thể expose Kaggle endpoint ra internet. Nếu tunnel drop, vLLM URL trong `.env` vẫn là string cũ - cần restart api-gateway để load URL mới.

Thiếu: chưa có circuit breaker pattern (ví dụ `tenacity` retry với exponential backoff) để tự động retry khi Kaggle lag.

3. **Giải thích cách event-driven architecture với Kafka giúp decouple các components trong AI platform của bạn.**

**Trả lời:**

Data flow: `scripts/01_ingest_to_kafka.py` (Producer) → Kafka topic `data.raw` → `prefect/flows/kafka_to_delta.py` (Consumer/Prefect worker).

Decoupling:
- Producer không biết consumer là ai, chỉ gửi message vào topic.
- Prefect worker có thể scale độc lập với producer (worker pool `lab28-pool`).
- Kafka giữ buffer - nếu consumer chậm, messages không mất (persistent log với offset tracking).
- Prefect flow `kafka_to_delta_flow` chạy theo cron `*/5 * * * *` (5 phút/lần) - tách biệt hoàn toàn với ingestion timing.

4. **Bạn đã implement observability như thế nào? Logs, metrics, và traces được thu thập và visualized ra sao?**

**Trả lời:**

- **Metrics:** `prometheus_fastapi_instrumentator` trong `api-gateway/main.py` tự động expose `/metrics` endpoint. Prometheus scrape job `api-gateway:8000` theo cấu hình trong `monitoring/prometheus.yml`. Metrics bao gồm `http_requests_total` với labels: handler, method, status.
- **Logs:** Tất cả services log ra stdout/stderr, Docker Compose thu thập tự động. Prefect UI (port 4200) hiển thị flow logs.
- **Traces:** LangSmith integration qua `LANGCHAIN_API_KEY` và `LANGCHAIN_PROJECT=lab28-platform` - tracing được bật với `LANGCHAIN_TRACING_SAMPLE_RATE=1.0` (100% sampled).
- **Visualization:** Grafana (port 3000) kết nối Prometheus làm datasource, hiển thị dashboard "AI Platform Metrics" với HTTP requests graph và stat panels.**

5. **Nếu một service trong stack (ví dụ: Qdrant hoặc Kafka) bị crash, hệ thống của bạn sẽ xử lý như thế nào? Có graceful degradation không?**

**Trả lời:**

- **Qdrant crash:** API Gateway `/api/v1/chat` gọi Qdrant để vector search trước khi inference. Nếu Qdrant down, `httpx` sẽ raise `ConnectError`, endpoint trả HTTP 500. Không có graceful degradation - Qdrant là hard dependency.
- **Kafka crash:** Prefect worker `depends_on: [prefect-orion, kafka]` trong docker-compose. Nếu Kafka down, worker vẫn start nhưng `KafkaConsumer` sẽ fail. Flow không chạy được nhưng không ảnh hưởng API Gateway.
- **Redis crash:** Dùng cho Feast feature store. Nếu down, `/health` vẫn OK nhưng inference endpoint sẽ fail khi cần features.
- **Graceful degradation:** Chưa có. Cần thêm try/except + fallback response (ví dụ: skip vector search nếu Qdrant down, dùng cached response) và health check để load balancer route away từ unhealthy services.

## Câu Hỏi Thêm?
Liên hệ giảng viên qua LMS hoặc office hours.
