"""Tests voice input: STT -> pipeline (parity dengan text) + fallback."""

import unittest
from datetime import datetime

from financial_engine import AccountType, FinancialEngine
from nlp import ParsePipeline
from nlp.pipeline import READY
from voice import FakeSpeechToText, VoiceInputHandler
from voice.voice_input import LOW_CONFIDENCE, OK, STT_FAILED


class BaseCase(unittest.TestCase):
    def setUp(self):
        self.e = FinancialEngine()
        self.bca = self.e.add_account("BCA", AccountType.BANK, starting_balance=5_000_000)
        self.pipe = ParsePipeline(self.e)

    def handler(self, **stt_kwargs):
        return VoiceInputHandler(self.pipe, FakeSpeechToText(**stt_kwargs))


class TestVoiceParity(BaseCase):
    PHRASE = "Beli makan siang 50 ribu pakai BCA"

    def test_voice_menghasilkan_transaksi_yang_sama_dengan_teks(self):
        now = datetime(2026, 9, 12, 12, 0, 0)
        # jalur teks
        text_draft = self.pipe.process(self.PHRASE, now=now)[0]
        # jalur suara (transkrip identik)
        vr = self.handler(transcript=self.PHRASE, confidence=0.95).handle(b"audio", now=now)

        self.assertEqual(vr.status, OK)
        self.assertFalse(vr.fallback)
        self.assertEqual(len(vr.drafts), 1)
        v = vr.drafts[0]
        self.assertEqual(v.parsed.type, text_draft.parsed.type)
        self.assertEqual(v.parsed.amount, text_draft.parsed.amount)
        self.assertEqual(v.account_id, text_draft.account_id)
        self.assertEqual(v.status, text_draft.status)
        # nilai konkret sesuai contoh
        self.assertEqual(v.parsed.type, "expense")
        self.assertEqual(v.parsed.amount, 50_000)
        self.assertEqual(v.parsed.category, "Makanan & Minuman")
        self.assertEqual(v.account_id, self.bca.id)
        self.assertEqual(v.status, READY)

    def test_voice_tidak_auto_simpan(self):
        vr = self.handler(transcript=self.PHRASE).handle(b"audio")
        self.assertEqual(len(self.e.transactions()), 0)  # belum tersimpan
        self.pipe.commit(vr.drafts[0])  # commit eksplisit
        self.assertEqual(self.e.balance(self.bca.id), 4_950_000)


class TestVoiceFallback(BaseCase):
    def test_stt_gagal_fallback(self):
        vr = self.handler(ok=False, error="tidak terdengar").handle(b"audio")
        self.assertEqual(vr.status, STT_FAILED)
        self.assertTrue(vr.fallback)
        self.assertEqual(vr.drafts, [])

    def test_transkrip_kosong_fallback(self):
        vr = self.handler(transcript="   ", confidence=0.9).handle(b"audio")
        self.assertEqual(vr.status, STT_FAILED)
        self.assertTrue(vr.fallback)

    def test_exception_stt_ditangani(self):
        handler = VoiceInputHandler(self.pipe, FakeSpeechToText(raises=RuntimeError("network")))
        vr = handler.handle(b"audio")
        self.assertEqual(vr.status, STT_FAILED)
        self.assertTrue(vr.fallback)
        self.assertEqual(len(self.e.transactions()), 0)

    def test_low_confidence_minta_review(self):
        vr = self.handler(transcript="Beli makan siang 50 ribu pakai BCA",
                          confidence=0.3).handle(b"audio")
        self.assertEqual(vr.status, LOW_CONFIDENCE)
        self.assertTrue(vr.fallback)  # tampilkan transkrip untuk diperiksa/diedit
        self.assertEqual(len(vr.drafts), 1)  # tetap di-parse agar bisa dikoreksi
        self.assertEqual(vr.transcript, "Beli makan siang 50 ribu pakai BCA")


if __name__ == "__main__":
    unittest.main()
