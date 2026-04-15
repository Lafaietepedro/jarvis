import threading
import logging

class WakewordSimulator:
    """Simulador simples de wake-word usando ENTER no terminal.
    Substitua por Porcupine/Precise para produção.
    """
    def __init__(self):
        self.running = False

    def start(self, on_wake):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, args=(on_wake,), daemon=True)
        self.thread.start()

    def _loop(self, on_wake):
        logging.info("Wakeword simulator iniciado. Pressione ENTER para simular.")
        try:
            while self.running:
                input()  # bloqueia até ENTER
                if not self.running:
                    break
                logging.info("Wakeword detectado (simulado)")
                try:
                    on_wake()
                except Exception:
                    logging.exception("Erro no callback de wake")
        except KeyboardInterrupt:
            pass

    def stop(self):
        self.running = False
