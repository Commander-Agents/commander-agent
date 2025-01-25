import threading
import signal
import sys
import atexit
from enrollment import EnrollmentManager
from keepalive import KeepAliveManager
from crypto_utils import CryptoUtils
from mqtt_manager import MQTTManager
import utils

# Drapeau pour éviter d'envoyer plusieurs KeepAlive lors de la fermeture
shutting_down = False

def cleanup():
    """Envoie un KeepAlive avant l'arrêt et arrête proprement les threads."""
    global shutting_down
    if shutting_down:
        return
    shutting_down = True

    print("\n[Shutdown] Sending final KeepAlive before exiting...")

    try:
        keepalive_manager.send_keepalive(False)
    except Exception as e:
        print(f"[Shutdown] Error sending KeepAlive: {e}")

    try:
        mqtt_manager.stop()
        print("[Shutdown] MQTT manager stopped.")
    except Exception as e:
        print(f"[Shutdown] Error stopping MQTT manager: {e}")

    print("[Shutdown] Cleanup done. Exiting.")

def signal_handler(signum, frame):
    """Gère les interruptions et déclenche le cleanup."""
    print(f"\n[Signal] Received signal {signum}, shutting down...")
    cleanup()
    sys.exit(0)

def main():
    global keepalive_manager, mqtt_manager

    # Gestion des signaux pour arrêt propre
    signal.signal(signal.SIGINT, signal_handler)  # CTRL+C
    signal.signal(signal.SIGTERM, signal_handler)  # Arrêt système

    # Exécuter cleanup() avant la fermeture, peu importe la cause
    atexit.register(cleanup)

    print("[Startup] Starting agent...")

    # Charger la configuration
    config = utils.load_config()

    # Étape 0 : Génération de la paire de clés RSA si nécessaire
    cryptoUtilsObject = CryptoUtils(config)

    # Étape 1 : Vérification de l'enrollment
    enrollment_manager = EnrollmentManager(config, cryptoUtilsObject)
    if not enrollment_manager.is_enrolled():
        enrollment_manager.enroll()
    if not enrollment_manager.is_enrolled():
        print("[Enrollment] Error during enrollment")
        sys.exit(1)

    # Étape 2 : Démarrage du KeepAlive
    keepalive_manager = KeepAliveManager(config, enrollment_manager.get_token(), cryptoUtilsObject)
    keepalive_thread = threading.Thread(target=keepalive_manager.start, daemon=True)
    keepalive_thread.start()
    print("[Startup] KeepAlive thread started.")

    # Étape 3 : Démarrage de MQTT
    mqtt_manager = MQTTManager(enrollment_manager.get_token(), config, cryptoUtilsObject)
    try:
        mqtt_manager.start()  # Bloquant
    except KeyboardInterrupt:
        print("\n[Shutdown] Stopping MQTT manager...")
        cleanup()

if __name__ == "__main__":
    main()
