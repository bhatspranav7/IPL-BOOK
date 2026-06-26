from kafka import KafkaProducer
import json
import os

producer = None


def get_producer():
    global producer

    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP", "kafka:9092"),
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except Exception as e:
            print("Kafka not ready, retry later:", e)
            return None

    return producer


def send_event(topic, data):
    try:
        prod = get_producer()

        if prod is None:
            print("Skipping Kafka event (Kafka not ready)")
            return

        prod.send(topic, data)
        prod.flush()

    except Exception as e:
        print("Kafka send failed:", e)