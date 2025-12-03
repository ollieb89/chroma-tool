import logging


def make_fake_collection():
    class FakeCollection:
        def __init__(self):
            self.upserts = []

        def upsert(self, documents=None, ids=None, metadatas=None):
            self.upserts.append((documents or [], ids or [], metadatas or []))

        def count(self):
            # return number of stored chunks
            return sum(len(d[0]) for d in self.upserts)

        def get(self, limit=5):
            # return a minimal shape to satisfy callers
            return {"ids": ["fake"], "documents": ["doc"], "metadatas": [{"filename": "f"}]}

    return FakeCollection()


def make_fake_client(fake_coll):
    class FakeClient:
        def __init__(self, coll):
            self._coll = coll

        def get_or_create_collection(self, name, **kwargs):
            return self._coll

    return FakeClient(fake_coll)


def test_ingest_prints_host_port_and_collection(monkeypatch, tmp_path, caplog):
    # Create a small sample file to ingest
    folder = tmp_path / "sample"
    folder.mkdir()
    sample = folder / "example.md"
    sample.write_text("# Example\n\nThis is a test document for chunking.")

    # Import the CodeIngester and supporting modules
    from chroma_ingestion.ingestion.base import CodeIngester

    # Prepare fake client/collection and monkeypatch client factory
    fake_coll = make_fake_collection()
    fake_client = make_fake_client(fake_coll)

    import chroma_ingestion.clients.chroma as chroma_clients

    monkeypatch.setattr(chroma_clients, "get_chroma_client", lambda: fake_client)

    # Monkeypatch config to return a deterministic host/port for audit printing.
    # The base module may have imported get_chroma_config directly, so patch there too.
    import chroma_ingestion.config as cfg

    monkeypatch.setattr(cfg, "get_chroma_config", lambda: {"host": "testhost", "port": 12345})
    import chroma_ingestion.ingestion.base as base_module

    monkeypatch.setattr(
        base_module, "get_chroma_config", lambda: {"host": "testhost", "port": 12345}
    )
    # Capture logs from the ingester module at INFO level
    caplog.set_level(logging.INFO, logger="chroma_ingestion.ingestion.base")

    # Run the ingester (small chunk sizes to keep it quick)
    ingester = CodeIngester(
        target_folder=str(folder),
        collection_name="test_collection",
        chunk_size=50,
        chunk_overlap=10,
        batch_size=10,
    )

    files_processed, chunks_ingested = ingester.ingest_files()

    # Assert the audit line with host/port/collection appears in logs
    text = caplog.text
    assert "[INGEST]" in text, "Expected an ingest audit line to be logged"
    assert "Chroma host=testhost" in text
    assert "port=12345" in text
    assert "collection=test_collection" in text

    # Also ensure some chunks were upserted
    assert chunks_ingested >= 1
