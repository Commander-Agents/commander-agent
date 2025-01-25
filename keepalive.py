import time
import requests

class KeepAliveManager:
    def __init__(self, config, token, crypto_utils):
        self.config = config
        self.token = token
        self.crypto_utils = crypto_utils
        self.api_url = config["api_url"]
        self.interval = config.get("keepalive_interval", 60)

    def send_keepalive(self, connected=True):
        """Envoie un signal keepalive au serveur."""
        try:
            payload = {
                "agent_uid": self.crypto_utils.generate_machine_id(),
                "status": connected
            }
            headers = {
                "X-Signature": self.crypto_utils.generate_signature(self.token, payload)
            }
            
            response = requests.post(
                f"{self.api_url}/keepalive",
                json=payload,
                headers=headers
            )

            if response.status_code != 200:
                print(f"[Keepalive] Keepalive failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[Keepalive] Error sending keepalive: {e}")

    def start(self):
        """Lance la boucle d'envoi des signaux keepalive."""
        print("[Keepalive] Starting KeepAlive...")
        while True:
            self.send_keepalive()
            time.sleep(self.interval)
