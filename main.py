from enrollment import EnrollmentManager
from keepalive import KeepAliveManager
from crypto_utils import CryptoUtils
import utils

def main():
    print("Starting agent...")

    # Charger la configuration
    config = utils.load_config()

    # Step 0 : Generate RSA key pair if not already generated
    cryptoUtilsObject = CryptoUtils(config)

    # Step 1 : Enrollment check
    enrollment_manager = EnrollmentManager(config, cryptoUtilsObject)
    if not enrollment_manager.is_enrolled():
        enrollment_manager.enroll()

    # Étape 2 : Démarrage du KeepAlive
    # keepalive_manager = KeepAliveManager(config, enrollment_manager.get_token())
    # keepalive_manager.start()

if __name__ == "__main__":
    main()
