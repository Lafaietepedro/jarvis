import os
import json
import queue
import threading
import logging
import tempfile
import wave

try:
    from vosk import Model, KaldiRecognizer
    import sounddevice as sd
except Exception:
    Model = None


class ASR:
    def __init__(self, model_path=None, samplerate=16000):
        model_path = model_path or os.environ.get("VOSK_MODEL_PATH")
        self.samplerate = samplerate
        if model_path and os.path.exists(model_path):
            logging.info("Loading Vosk model from %s", model_path)
            self.model = Model(model_path)
        else:
            logging.warning("Vosk model not found (VOSK_MODEL_PATH=%s). ASR disabled.", model_path)
            self.model = None
        self.q = queue.Queue()
        self.running = False
        self.stream = None

    def _audio_callback(self, indata, frames, time, status):
        if status:
            logging.debug(status)
        # indata is a numpy array
        self.q.put(bytes(indata))

    def start_streaming(self, on_result=None):
        if self.model is None:
            raise RuntimeError("Vosk model not available")
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._stream_worker, args=(on_result,), daemon=True)
        self.thread.start()
        self.stream = sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, dtype='int16', channels=1, callback=self._audio_callback)
        self.stream.start()

    def _stream_worker(self, on_result):
        rec = KaldiRecognizer(self.model, self.samplerate)
        while self.running:
            data = self.q.get()
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                text = res.get('text', '')
                if text and on_result:
                    on_result(text)
            else:
                pass

    def stop_streaming(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1)

    def recognize_file(self, file_path):
        if self.model is None:
            logging.warning("No model available; returning empty transcription")
            return ""
        wf = wave.open(file_path, "rb")
        rec = KaldiRecognizer(self.model, wf.getframerate())
        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                results.append(json.loads(rec.Result()))
        results.append(json.loads(rec.FinalResult()))
        text = " ".join(r.get('text', '') for r in results if r)
        return text

    def recognize_bytes(self, audio_bytes):
        tf = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        tf.write(audio_bytes)
        tf.flush()
        tf.close()
        try:
            return self.recognize_file(tf.name)
        finally:
            try:
                os.unlink(tf.name)
            except Exception:
                pass
