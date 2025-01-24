import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import platform
import uuid
import hashlib
import socket

class CryptoUtils:
    def __init__(self, config):
        self.config = config
        self.keysSelfDirectory = "keys/self"
        self.keysServerDirectory = "keys/server"

        os.makedirs(self.keysSelfDirectory, exist_ok=True)
        os.makedirs(self.keysServerDirectory, exist_ok=True)
        if (not os.path.isfile(os.path.join(self.keysSelfDirectory, 'private_key.pem'))) or (not os.path.isfile(os.path.join(self.keysSelfDirectory, 'public_key.pem'))):
            print("Generating RSA keys")
            self.generate_rsa_key_pair()
            print("RSA keys generated")

    def generate_rsa_key_pair(self):
        # Génération de la clé privée RSA
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )

        # Génération de la clé publique
        public_key = private_key.public_key()

        # Sérialisation de la clé privée (en format PEM)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Sérialisation de la clé publique (en format PEM)
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Sauvegarder les clés dans des fichiers
        with open(os.path.join(self.keysSelfDirectory, 'private_key.pem'), 'wb') as f:
            f.write(private_pem)

        with open(os.path.join(self.keysSelfDirectory, 'public_key.pem'), 'wb') as f:
            f.write(public_pem)

        # print(public_pem.decode())

    def save_server_public_key(self, public_key):
        if type(public_key) == str:
            public_key = str.encode(public_key)

        with open(os.path.join(self.keysServerDirectory, 'public_key.pem'), 'wb') as f:
            f.write(public_key)

    def load_private_key(self):
        with open(os.path.join(self.keysSelfDirectory, 'private_key.pem'), "rb") as key_file:
            private_key = load_pem_private_key(
                key_file.read(),
                password=None, # if private key use password, handle it here
            )
        return private_key

    def decrypt_with_private_key(self, encrypted_value):
        private_key = self.load_private_key()

        decrypted_value = private_key.decrypt(
            encrypted_value,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted_value

    def get_mac_address(self):
        mac = None
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                            for elements in range(0,2*6,2)][::-1])
        except Exception as e:
            print("Error while retrieving MAC address :", e)
        return mac

    def generate_machine_id(self):
        hostname = self.config["hostname"] or socket.gethostname()
        port = self.config["agent_port"]
        protocol = self.config["agent_protocol"]
        os_info = platform.system() + platform.release()
        mac_address = self.get_mac_address()

        if not mac_address:
            raise ValueError("Adresse MAC introuvable")

        unique_string = f"{hostname}-{port}-{protocol}-{os_info}-{mac_address}"
        machine_id = hashlib.sha256(unique_string.encode()).hexdigest()
        return machine_id