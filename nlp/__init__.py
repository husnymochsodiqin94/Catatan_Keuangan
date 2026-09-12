"""AI Transaction Parser — Natural Language -> Structured Transaction.

Arsitektur (SYSTEM_ARCHITECTURE.md): parser berada di balik antarmuka
``TransactionParser``. Implementasi default ``RuleBasedParser`` bersifat
deterministik & offline (tanpa dependency/LLM) sehingga dapat diuji dan menjadi
fallback. Adapter berbasis LLM dapat mengimplementasikan antarmuka yang sama
tanpa mengubah pipeline.

Alur wajib: input -> parse -> schema validation -> business validation ->
Financial Engine -> (persistensi, di luar modul ini). Output AI TIDAK boleh
langsung masuk database.
"""

from .schema import ParsedTransaction, ParseResult, validate_schema
from .parser import RuleBasedParser, TransactionParser
from .pipeline import Draft, ParsePipeline, PipelineError

__all__ = [
    "ParsedTransaction",
    "ParseResult",
    "validate_schema",
    "TransactionParser",
    "RuleBasedParser",
    "ParsePipeline",
    "Draft",
    "PipelineError",
]
