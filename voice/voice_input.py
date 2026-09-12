"""Speech-to-Text adapter + orchestrator voice input.

``SpeechToText`` = antarmuka. ``FakeSpeechToText`` = implementasi deterministik
untuk test/dev. ``VoiceInputHandler`` menyatukan STT dengan ``ParsePipeline``
yang sama seperti text input, plus fallback bila STT gagal/low-confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Protocol

from nlp import Draft, ParsePipeline

# Status hasil voice
OK = "ok"
LOW_CONFIDENCE = "low_confidence"
STT_FAILED = "stt_failed"


@dataclass
class STTResult:
    """Hasil transkripsi audio -> teks."""

    ok: bool
    transcript: Optional[str] = None
    confidence: float = 0.0
    error: Optional[str] = None


class SpeechToText(Protocol):
    def transcribe(self, audio) -> STTResult:  # audio: bytes/stream/dsb (opaque)
        ...


class FakeSpeechToText:
    """STT palsu deterministik untuk test/dev.

    Dikonfigurasi dengan transcript & confidence, atau di-set gagal / melempar
    exception untuk menguji error handling.
    """

    def __init__(
        self, transcript: Optional[str] = None, confidence: float = 0.95,
        ok: bool = True, error: Optional[str] = None, raises: Optional[Exception] = None,
    ):
        self._transcript = transcript
        self._confidence = confidence
        self._ok = ok
        self._error = error
        self._raises = raises

    def transcribe(self, audio) -> STTResult:
        if self._raises is not None:
            raise self._raises
        return STTResult(
            ok=self._ok, transcript=self._transcript,
            confidence=self._confidence, error=self._error,
        )


@dataclass
class VoiceResult:
    status: str
    transcript: Optional[str] = None
    stt_confidence: float = 0.0
    drafts: List[Draft] = field(default_factory=list)
    fallback: bool = False  # True => UX sebaiknya menampilkan input teks manual/editable
    message: str = ""


class VoiceInputHandler:
    """Voice -> STT -> ParsePipeline (identik dengan text) -> drafts.

    Tidak menyimpan apa pun; commit tetap eksplisit lewat ``ParsePipeline``.
    """

    def __init__(
        self, pipeline: ParsePipeline, stt: SpeechToText,
        min_stt_confidence: float = 0.5,
    ):
        self.pipeline = pipeline
        self.stt = stt
        self.min_stt_confidence = min_stt_confidence

    def handle(
        self, audio, now: Optional[datetime] = None,
        default_account_id: Optional[str] = None,
    ) -> VoiceResult:
        # 1) Speech-to-Text (dengan error handling)
        try:
            stt = self.stt.transcribe(audio)
        except Exception:  # segala kegagalan STT (jaringan, dsb) -> fallback
            return VoiceResult(
                status=STT_FAILED, fallback=True, stt_confidence=0.0,
                message="Gagal memproses suara. Coba lagi atau ketik manual.",
            )

        # 2) Gagal / kosong -> fallback ke input teks manual
        if not stt.ok or not (stt.transcript and stt.transcript.strip()):
            return VoiceResult(
                status=STT_FAILED, fallback=True, stt_confidence=stt.confidence,
                message=stt.error or "Suara tidak terdengar. Coba lagi atau ketik manual.",
            )

        transcript = stt.transcript.strip()

        # 3) Konvergensi ke teks: pakai pipeline yang SAMA dengan text input
        drafts = self.pipeline.process(
            transcript, now=now, default_account_id=default_account_id
        )

        # 4) STT low-confidence -> tetap parse, tapi minta review/edit transkrip
        if stt.confidence < self.min_stt_confidence:
            return VoiceResult(
                status=LOW_CONFIDENCE, transcript=transcript,
                stt_confidence=stt.confidence, drafts=drafts, fallback=True,
                message="Kami kurang yakin mendengar. Periksa teks berikut sebelum menyimpan.",
            )

        return VoiceResult(
            status=OK, transcript=transcript, stt_confidence=stt.confidence,
            drafts=drafts, fallback=False, message=transcript,
        )
