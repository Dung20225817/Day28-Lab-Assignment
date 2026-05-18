from kafka import KafkaConsumer
import json, os, datetime
import pandas as pd

consumer = KafkaConsumer(
    "data.raw",
    bootstrap_servers="127.0.0.1:29092",
    auto_offset_reset="earliest",
    consumer_timeout_ms=5000,
    value_deserializer=lambda m: json.loads(m.decode())
)
records = []
for msg in consumer:
    records.append(msg.value)
consumer.close()
print(f"Consumed {len(records)} from Kafka")

if records:
    df = pd.DataFrame(records)
    path = "delta-lake/raw"
    os.makedirs(path, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    df.to_parquet(f"{path}/batch_{ts}.parquet")
    print(f"Saved {len(df)} records to delta-lake")
else:
    print("No records in Kafka topic")
