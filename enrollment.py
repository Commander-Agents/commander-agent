import os
import json
import uuid
import requests
import socket
import base64
import platform
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

class EnrollmentManager:
    def __init__(self, config, crypto_utils):
        self.config = config
        self.crypto_utils = crypto_utils
        self.enrollment_token_path = "keys/enrollment_token.json"

    def is_enrolled(self):
        """Vérifie si l'agent est déjà enrôlé."""
        return os.path.exists(self.enrollment_token_path)

    def get_token(self):
        """Récupère le token d'enrollment depuis le fichier local."""
        if not self.is_enrolled():
            raise FileNotFoundError("Agent is not enrolled. No token found.")
        with open(self.enrollment_token_path, "r") as f:
            return json.load(f)["token"]

    def save_token(self, token):
        """Sauvegarde le token d'enrollment dans un fichier local."""
        if len(token) != 64:
            raise Exception("Token format is not acceptable, there is most likely an error during decryption")

        with open(self.enrollment_token_path, "w") as f:
            json.dump({"token": token}, f)

    def enroll(self):
        """Effectue l'enrollment de l'agent auprès du serveur."""
        api_url = self.config["api_url"]
        agent_port = self.config["agent_port"]
        agent_protocol = self.config["agent_protocol"]
        hostname = self.config["hostname"] or socket.gethostname()

        with open(os.path.join(self.crypto_utils.keysSelfDirectory, 'public_key.pem'), 'r') as file:
            public_key = file.read()

        payload = {
            "agent_port": agent_port,
            "agent_protocol": agent_protocol,
            "agent_hostname": hostname,
            "agent_public_key": public_key,
            "agent_operating_system": platform.system() + platform.release(),
            "agent_uid": self.crypto_utils.generate_machine_id() # Just to avoid agent duplication in case of reinstallation
        }

        print("Attempting to enroll...")
        try:
            response = requests.post(f"{api_url}/enroll", json=payload)
            response.raise_for_status()
            data = response.json()

            if data["success"]:
                print("Enrollment from server is OK")
                print("Registering server public key")
                server_public_key = data["server_public_key"]
                self.crypto_utils.save_server_public_key(server_public_key)
                print("Server public key registered")

                # Decrypt HMAC key with Agent private key and save HMAC key
                decoded_key = base64.b64decode(data["encrypted_hmac_signing_key"])
                try:
                    hmac_signing_key = self.crypto_utils.decrypt_with_private_key(decoded_key).decode('utf-8')
                    self.save_token(hmac_signing_key)
                except Exception as e:
                    print("Error while decrypting HMAC key :", str(e))
            else:
                raise Exception("Error while enrolling from the server") 

        except Exception as e:
            print(f"Enrollment failed: {e}")
