"""Voice input layer.

Alur: Voice -> Speech-to-Text -> (teks) -> AI Transaction Parser -> Validation
-> Financial Engine -> Database -> Confirmation.

Prinsip: voice HANYA menghasilkan teks lalu memakai ``ParsePipeline`` yang sama
dengan text input, sehingga hasilnya identik dengan mengetik kalimat yang sama.
STT berada di balik antarmuka ``SpeechToText`` (adapter) — implementasi nyata
(browser Web Speech API / provider) menyusul; fallback ke input teks manual bila
STT gagal.
"""

from .voice_input import (
    FakeSpeechToText,
    SpeechToText,
    STTResult,
    VoiceInputHandler,
    VoiceResult,
)

__all__ = [
    "SpeechToText",
    "STTResult",
    "FakeSpeechToText",
    "VoiceInputHandler",
    "VoiceResult",
]
