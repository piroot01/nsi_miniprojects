import network
import time
import ntptime
import json
from umqtt.simple import MQTTClient
from machine import ADC, Pin

# ==== Configuration constants ====
WIFI_SSID = "w"
WIFI_PASSWORD = "12345678"
MQTT_BROKER = "192.168.214.159"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "pico_client"
MQTT_TOPIC_DATA = "temperature/data"
MQTT_TOPIC_CMD = "control/pico"

# ==== Measurement settings ====
measurement_interval = 10    # seconds between readings
is_measuring = True          # flag: should we publish measurements?
status_led = Pin("LED", Pin.OUT)  # on-board LED for status

# ==== Wi-Fi connection ====
def connect_wifi():
    """Activate station interface and connect to Wi-Fi."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        print("Connecting to WiFi…")
        time.sleep(1)
    print("WiFi connected, IP:", wlan.ifconfig())

# ==== Time synchronization ====
def sync_rtc():
    """Synchronize the real-time clock via NTP."""
    try:
        ntptime.settime()
        print("RTC synchronized")
    except Exception:
        print("Failed to sync RTC")

def get_timestamp(offset_hours=2):
    """
    Return a local timestamp string in YYYY-MM-DD HH:MM:SS.mmm format,
    applying a fixed timezone offset.
    """
    epoch = time.time() + offset_hours * 3600
    tm = time.localtime(epoch)
    ms = time.ticks_ms() % 1000
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}.{:03d}".format(
        tm[0], tm[1], tm[2], tm[3], tm[4], tm[5], ms
    )

# ==== Temperature sensor reading ====
def read_temperature_c():
    """
    Read the on-chip ADC, convert voltage to temperature (°C),
    and round to two decimal places.
    """
    temp_sensor = ADC(4)
    voltage = temp_sensor.read_u16() * 3.3 / 65535
    # Formula from RP2040 datasheet
    temp_c = 27 - (voltage - 0.706) / 0.001721
    return round(temp_c, 2)

# ==== Command handling ====
def handle_command(cmd_str):
    """
    Process incoming control commands over MQTT:
      - LED ON/OFF
      - MEASURE ON/OFF
      - SET INTERVAL <seconds>
    """
    global is_measuring, measurement_interval
    print("Command received:", cmd_str)

    if cmd_str == "LED ON":
        status_led.on()
    elif cmd_str == "LED OFF":
        status_led.off()
    elif cmd_str == "MEASURE ON":
        is_measuring = True
    elif cmd_str == "MEASURE OFF":
        is_measuring = False
    elif cmd_str.startswith("SET INTERVAL "):
        try:
            secs = int(cmd_str.split(" ", 2)[2])
            measurement_interval = max(1, secs)
            print("New measurement interval:", measurement_interval, "s")
        except ValueError:
            print("Invalid interval value")

# ==== MQTT callback ====
def mqtt_callback(topic, msg):
    """Decode and forward incoming MQTT messages to the command handler."""
    handle_command(msg.decode())

# ==== Main application loop ====
def main():
    global is_measuring, measurement_interval

    # 1) Connect to Wi-Fi and sync time
    connect_wifi()
    sync_rtc()

    # 2) Set up MQTT client
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(MQTT_TOPIC_CMD)
    print("MQTT connected, subscribed to:", MQTT_TOPIC_CMD)

    last_publish_time = time.time()

    # 3) Enter perpetual loop: check for commands, publish data
    while True:
        client.check_msg()  # non-blocking check for new commands

        now = time.time()
        if now - last_publish_time >= measurement_interval:
            if is_measuring:
                temp_c = read_temperature_c()
                ts = get_timestamp()

                payload = {
                    "temperature": temp_c,
                    "timestamp_measurement": ts,
                    "timestamp_sent": ts
                }

                try:
                    client.publish(MQTT_TOPIC_DATA, json.dumps(payload), qos=1)
                    print("Published:", payload)
                    last_publish_time = now
                except Exception as e:
                    print("Publish error:", e)
            else:
                print("Measurement paused; skipping publish")

        # small sleep to yield to network interrupts
        time.sleep(0.1)

if __name__ == "__main__":
    main()
