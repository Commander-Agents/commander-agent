import time
import requests

class KeepAliveManager:
    def __init__(self, config, token):
        self.config = config
        self.token = token
        self.api_url = config["api_url"]
        self.interval = config.get("keepalive_interval", 60)

    def send_keepalive(self):
        """Envoie un signal keepalive au serveur."""
        try:
            response = requests.post(
                f"{self.api_url}/keepalive",
                json={"token": self.token}
            )
            if response.status_code == 200:
                print("Keepalive signal sent successfully.")
            else:
                print(f"Keepalive failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error sending keepalive: {e}")

    def start(self):
        """Lance la boucle d'envoi des signaux keepalive."""
        print("Starting KeepAlive...")
        while True:
            self.send_keepalive()
            time.sleep(self.interval)
