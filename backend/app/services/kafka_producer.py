import json
import logging

from app.config import KAFKA_BOOTSTRAP

logger = logging.getLogger(__name__)

try:
    from kafka import KafkaProducer
except ImportError:  # kafka-python is optional
    KafkaProducer = None

producer = None


def kafka_enabled() -> bool:
    return bool(KAFKA_BOOTSTRAP) and KafkaProducer is not None


def get_producer():
    global producer

    if not kafka_enabled():
        return None

    if producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                request_timeout_ms=3000,
                max_block_ms=3000,
            )
        except Exception as e:
            logger.warning("Kafka not ready, retry later: %s", e)
            return None

    return producer


def send_event(topic, data):
    try:
        prod = get_producer()

        if prod is None:
            return

        # Async send: booking latency must not depend on the broker
        prod.send(topic, data)

    except Exception as e:
        logger.warning("Kafka send failed: %s", e)
