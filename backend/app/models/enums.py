from enum import Enum


class BatchStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    NORMALIZED = "normalized"
    VALIDATED = "validated"
    MATCHED = "matched"
    EXPORT_READY = "export_ready"
    EXPORTED = "exported"
    FAILED = "failed"
    BLOCKED = "blocked"


class MappingSource(str, Enum):
    RULE = "rule"
    LLM = "llm"
    MANUAL = "manual"


class MatchStatus(str, Enum):
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    DUPLICATE = "duplicate"
    LOW_CONFIDENCE = "low_confidence"
    MANUAL = "manual"


class TemplateType(str, Enum):
    SALARY = "salary"
    FINAL_TOOL = "final_tool"