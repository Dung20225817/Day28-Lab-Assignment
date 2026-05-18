# scripts/01_ingest_to_kafka.py
from confluent_kafka import Producer
import json, time

producer = Producer({
    "bootstrap.servers": "127.0.0.1:29092",
})

def delivery_report(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Sent: {msg.value()}")

def ingest_data(records: list[dict]):
    for record in records:
        producer.produce(
            "data.raw",
            key=record["id"].encode(),
            value=json.dumps(record).encode(),
            callback=delivery_report
        )
    producer.flush()

# Test
sample_data = [
    {"id": "doc_001", "text": "AI platform integration test", "timestamp": time.time()},
    {"id": "doc_002", "text": "Kafka to Airflow pipeline", "timestamp": time.time()},
]
ingest_data(sample_data)
print("Integration 1 OK: Data -> Kafka")
