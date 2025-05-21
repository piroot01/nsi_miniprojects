import json
import paho.mqtt.client as mqtt
from database import insert_measurement

# ==== MQTT configuration ====
MQTT_BROKER = "192.168.214.159"           # IP address of the MQTT broker
MQTT_DATA_TOPIC = "temperature/data"
MQTT_CMD_TOPIC = "control/pico"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

# ==== MQTT client instance ====
mqtt_client = mqtt.Client(client_id="db_writer")

def handle_connect(client, userdata, flags, return_code):
    """Called when the MQTT client connects to the broker."""
    print("---------------------------------")
    print("Connected to broker with result code:", return_code)
    print("---------------------------------")
    client.subscribe(MQTT_DATA_TOPIC, qos=1)  # subscribe with delivery confirmation

def handle_message(client, userdata, message):
    """Called when a new MQTT message arrives."""
    try:
        data = json.loads(message.payload.decode())
        temperature_c = data.get("temperature")
        measurement_timestamp = data.get("timestamp_measurement")
        sent_timestamp = data.get("timestamp_sent")

        print(f"Received temperature: {temperature_c}°C")
        insert_measurement(temperature_c, measurement_timestamp, sent_timestamp)
    except Exception as err:
        print("Error processing incoming message:", err)

def start_mqtt():
    """
    Initialize and start the MQTT client loop in a background thread.
    This allows the Flask app (or other main loop) to continue running.
    """
    mqtt_client.on_connect = handle_connect
    mqtt_client.on_message = handle_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
    mqtt_client.loop_start()

def publish_command(command_str):
    """Send a control command over MQTT."""
    print(f"Publishing command: {command_str}")
    mqtt_client.publish(MQTT_CMD_TOPIC, command_str, qos=1)
