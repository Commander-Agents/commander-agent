import paho.mqtt.client as mqtt
import subprocess
import requests
import chardet
import json
import sys

class MQTTManager:
    def __init__(self, token, config, crypto_utils):
        self.token = token
        self.config = config
        self.crypto_utils = crypto_utils
        self.uid = self.crypto_utils.generate_machine_id()
        self.broker = config.get("mqtt", {}).get("broker", "localhost")
        self.port = config.get("mqtt", {}).get("port", 1883)
        self.topic = "agents/" + self.uid # agents/{uid}
        self.client_id = "laravel_client_1" # self.uid

        username = self.uid
        password = self.token

        self.client = mqtt.Client()
        self.client.username_pw_set(username, password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def send_output(self, taskUID, stdout, stderr):
        payload = {
            "agent_uid": self.crypto_utils.generate_machine_id(),
            "command": {
                "stdout": (stdout.replace("\r\n", "\n").strip() if stdout else None),
                "stderr": (stderr.replace("\r\n", "\n").strip() if stderr else None),
                "uid": taskUID
            }
        }
        headers = {
            "X-Signature": self.crypto_utils.generate_signature(self.token, payload)
        }

        try:
            response = requests.post(
                f"{self.config["api_url"]}/commandOutput",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
        except Exception as e:
            print(f"[Command output] Failed to send response to server for task {taskUID} : {e}")

    def send_acknowledgment(self, taskUID):
        payload = {
            "agent_uid": self.crypto_utils.generate_machine_id(),
            "command_uid": taskUID
        }
        headers = {
            "X-Signature": self.crypto_utils.generate_signature(self.token, payload)
        }

        try:
            response = requests.post(
                f"{self.config["api_url"]}/commandAcknowledged",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
        except Exception as e:
            print(f"[Command acknowledgement] Failed to send acknowledgement to server for task {taskUID} : {e}")

    def on_connect(self, client, userdata, flags, rc):
        print(f"[MQTT] Connected to MQTT broker with result code {rc}")
        self.client.subscribe(self.topic)
        print(f"[MQTT] Subscribed to topic: {self.topic}")

    def on_message(self, client, userdata, msg):
        try:
            receivedMessage = msg.payload.decode()
            parsedMessage = json.loads(receivedMessage)

            command = parsedMessage["command"]
            signature = parsedMessage["signature"]
            taskUID = parsedMessage["uid"]
            print(f"[MQTT] Command {taskUID} received, checking signature, should be : {signature}")
            generatedSignature = self.crypto_utils.generate_signature(self.token, command)
            if generatedSignature != signature: 
                print(f"   WARNING : Signature for task {taskUID} command doesn't match what is expected ({generatedSignature}), Agent will abort to avoid potential compromission.")
                sys.exit(1)
            
            print(f"[MQTT] Signature checked, executing command {taskUID} received on topic {msg.topic}: {command}")

            # Exécuter la commande et capturer l'output
            self.send_acknowledgment(taskUID)
            result = subprocess.run(
                command,
                shell=True,             # Allow command block
                check=False,            # Don't throw an exception if the command fail
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout = result.stdout.decode('utf-8', errors="replace")  # Décoder la sortie en chaîne
            stderr = result.stderr.decode('utf-8', errors="replace")  # Décoder les erreurs (si présentes)
            
            if stdout:
                print(f"[Task] Command output:\n{stdout}")
            else:
                stdout = None
            if stderr:
                print(f"[Task] Command errors:\n{stderr}")
            else:
                stderr = None

            # Send output to server
            self.send_output(taskUID, stdout, stderr)

        except subprocess.CalledProcessError as e:
            print(f"[Task] Command failed with error: {e}")

        except Exception as e:
            print(f"[Task] Unexpected error: {e}")

    def start(self):
        print("[Startup] Starting MQTT manager...")
        try:
            self.client.connect(self.broker, int(self.port), 60)
            self.client.subscribe(f"agents/{self.uid}")
            self.client.loop_forever()  # Bloque jusqu'à ce qu'il soit arrêté
        except Exception as e:
            print(f"Failed to start MQTT client: {e}")
    
    def stop(self):
        print("[Shutdown] Disconnecting MQTT client...")
        self.client.disconnect()
        print("[Shutdown] MQTT client disconnected.")
