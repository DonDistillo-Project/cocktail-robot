__version__ = "1.9.5-shim"


def create(*_, **__):
    raise RuntimeError("Wake word (Porcupine) is disabled in this build.")
