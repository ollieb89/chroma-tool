import logging


def make_fake_collection():
    class FakeCollection:
        def __init__(self):
            self.upserts = []

        def upsert(self, documents=None, ids=None, metadatas=None):
            self.upserts.append((documents or [], ids or [], metadatas or []))

        def count(self):
            return sum(len(d[0]) for d in self.upserts)

        def get(self, limit=5):
            return {"ids": ["fake"], "documents": ["doc"], "metadatas": [{"filename": "f"}]}

    return FakeCollection()


def make_fake_client(fake_coll):
    class FakeClient:
        def __init__(self, coll):
            self._coll = coll

        def get_or_create_collection(self, name, **kwargs):
            return self._coll

    return FakeClient(fake_coll)


def test_batches_logged(monkeypatch, tmp_path, caplog):
    # Create sample content that will be split into multiple chunks
    folder = tmp_path / "sample"
    folder.mkdir()
    sample = folder / "big.md"
    # repeat a paragraph so splitter will produce multiple chunks
    paragraph = "This is a repeated sentence. " * 50
    sample.write_text(paragraph)

    from chroma_ingestion.ingestion.base import CodeIngester

    fake_coll = make_fake_collection()
    fake_client = make_fake_client(fake_coll)

    import chroma_ingestion.clients.chroma as chroma_clients

    monkeypatch.setattr(chroma_clients, "get_chroma_client", lambda: fake_client)

    import chroma_ingestion.config as cfg

    monkeypatch.setattr(cfg, "get_chroma_config", lambda: {"host": "testhost", "port": 12345})

    import chroma_ingestion.ingestion.base as base_module

    monkeypatch.setattr(
        base_module, "get_chroma_config", lambda: {"host": "testhost", "port": 12345}
    )

    caplog.set_level(logging.INFO, logger="chroma_ingestion.ingestion.base")

    # Use a very small batch_size to force multiple batches
    ingester = CodeIngester(
        target_folder=str(folder),
        collection_name="batch_test",
        chunk_size=100,
        chunk_overlap=10,
        batch_size=1,
    )

    files_processed, chunks_ingested = ingester.ingest_files()

    # Ensure at least 2 chunks were created so there is more than one batch
    assert chunks_ingested >= 2

    text = caplog.text
    assert "Batch 1 complete" in text or "Batch 1 complete (" in text
