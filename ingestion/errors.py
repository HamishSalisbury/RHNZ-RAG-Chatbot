"""All ingestion error types and their messages, in one place."""


class IngestionError(Exception):
    """Base class for all ingestion pipeline errors."""
    template = "Ingestion error"

    def __init__(self, **kwargs):
        super().__init__(self.template.format(**kwargs))


class MissingEnvVar(IngestionError):
    template = "{name} is not set. Add it to .env or the environment."


class InvalidEnvVar(IngestionError):
    template = "{name} has invalid value {value!r}: expected {expected}."


class KnowledgeDirNotFound(IngestionError):
    template = "Knowledge directory not found: {path}"


class NoIndexableFiles(IngestionError):
    template = "No indexable files found in {path}"