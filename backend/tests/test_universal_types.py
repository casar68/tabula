"""Tests for UniversalUUID and UniversalJSON on SQLite."""

import uuid

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.template import Template


class TestUniversalUUID:
    """Verify that UUID values round-trip correctly via SQLite."""

    def test_uuid_stored_and_retrieved(self, db_session: Session):
        doc = Document(
            original_filename="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
        )
        db_session.add(doc)
        db_session.commit()

        fetched = db_session.get(Document, doc.id)
        assert fetched is not None
        assert isinstance(fetched.id, uuid.UUID)

    def test_uuid_default_generation(self, db_session: Session):
        doc = Document(
            original_filename="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
        )
        db_session.add(doc)
        db_session.commit()

        assert doc.id is not None
        assert isinstance(doc.id, uuid.UUID)

    def test_uuid_foreign_key(self, db_session: Session):
        from app.models.job import Job

        doc = Document(
            original_filename="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
        )
        db_session.add(doc)
        db_session.flush()

        job = Job(document_id=doc.id)
        db_session.add(job)
        db_session.commit()

        fetched_job = db_session.get(Job, job.id)
        assert fetched_job is not None
        assert fetched_job.document_id == doc.id


class TestUniversalJSON:
    """Verify that JSON values round-trip correctly via SQLite."""

    def test_json_dict(self, db_session: Session):
        pages = [{"number": 1, "width": 612, "height": 792}]
        doc = Document(
            original_filename="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            pages=pages,
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        assert doc.pages == pages

    def test_json_complex_data(self, db_session: Session):
        selections = [
            {"page": 1, "x1": 0, "y1": 0, "x2": 100, "y2": 100, "method": "guess"}
        ]
        tpl = Template(
            name="Test",
            selections=selections,
            selection_count=1,
            page_count=1,
        )
        db_session.add(tpl)
        db_session.commit()
        db_session.refresh(tpl)

        assert tpl.selections == selections

    def test_json_null(self, db_session: Session):
        doc = Document(
            original_filename="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            pages=None,
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        assert doc.pages is None
