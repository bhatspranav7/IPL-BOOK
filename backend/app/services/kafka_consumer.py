from kafka import KafkaConsumer
import json
import os

consumer = KafkaConsumer(
    "booking-events",
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "kafka:9092"),
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

print("Kafka consumer started...")

for message in consumer:
    data = message.value
    print("EVENT RECEIVED:", data)

    # 👉 FUTURE USE:
    # - ML training data
    # - analytics
    # - notifications