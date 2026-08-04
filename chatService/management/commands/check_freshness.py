import chromadb
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand

REQUIRED = ["source_hash", "last_built_at", "chunker_version", "embedding_model"]

class Command(BaseCommand):
    def handle(self, *args, **opts):
        client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        meta = client.get_collection("knowledge").metadata or {}

        self.stdout.write("Freshness metadata:")
        ok = True
        for key in REQUIRED:
            val = meta.get(key)
            present = val not in (None, "")
            ok &= present
            mark = "\033[92m✓\033[0m" if present else "\033[91m✗\033[0m"
            self.stdout.write(f"  {mark} {key:<16} {val if present else '— MISSING'}")

        # sanity-check the timestamp actually parses
        try:
            datetime.fromisoformat(meta.get("last_built_at", ""))
        except ValueError:
            ok = False
            self.stdout.write("  \033[91m✗\033[0m last_built_at is not valid ISO format")

        if ok:
            self.stdout.write(self.style.SUCCESS("\nAll freshness fields present ✓"))
        else:
            self.stdout.write(self.style.ERROR("\nMissing freshness metadata ✗"))
            raise SystemExit(1)   # non-zero → fails the docker build if run in it