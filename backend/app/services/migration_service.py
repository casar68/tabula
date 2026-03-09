"""Data migration between SQLite and PostgreSQL.

When switching modes, copies documents and templates between databases.
PDF files remain on disk (same upload_dir); only metadata is migrated.
"""

import logging
import uuid

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.document import Document
from app.models.job import Job
from app.models.template import Template

logger = logging.getLogger(__name__)


def _make_sqlite_session(path: str) -> Session:
    """Create a session connected to a SQLite database file."""
    url = f"sqlite:///{path}"
    engine = create_engine(
        url, connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    return factory()


def _make_pg_session(url: str) -> Session:
    """Create a session connected to a PostgreSQL database."""
    engine = create_engine(url, pool_pre_ping=True)
    factory = sessionmaker(bind=engine)
    return factory()


def migrate_sqlite_to_postgres(
    sqlite_path: str,
    pg_url: str,
    admin_user_id: uuid.UUID,
) -> dict:
    """Copy all documents and templates from SQLite to PostgreSQL.

    All migrated records are assigned to *admin_user_id*.
    Returns a summary dict.
    """
    src = _make_sqlite_session(sqlite_path)
    dst = _make_pg_session(pg_url)
    doc_count = 0
    tpl_count = 0

    try:
        # Migrate documents (and their jobs)
        for doc in src.query(Document).all():
            new_doc = Document(
                id=doc.id,
                original_filename=doc.original_filename,
                file_path=doc.file_path,
                file_size=doc.file_size,
                page_count=doc.page_count,
                pages=doc.pages,
                detected_tables=doc.detected_tables,
                sha256=doc.sha256,
                user_id=admin_user_id,
            )
            dst.merge(new_doc)
            doc_count += 1

            # Migrate jobs linked to this document
            for job in src.query(Job).filter(Job.document_id == doc.id).all():
                new_job = Job(
                    id=job.id,
                    document_id=job.document_id,
                    status=job.status,
                    progress=job.progress,
                    message=job.message,
                    error_type=job.error_type,
                )
                dst.merge(new_job)

        # Migrate templates
        for tpl in src.query(Template).all():
            new_tpl = Template(
                id=tpl.id,
                name=tpl.name,
                selections=tpl.selections,
                selection_count=tpl.selection_count,
                page_count=tpl.page_count,
                user_id=admin_user_id,
                is_shared=False,
            )
            dst.merge(new_tpl)
            tpl_count += 1

        dst.commit()
    finally:
        src.close()
        dst.close()

    logger.info(
        "Migrated %d documents and %d templates from SQLite to PostgreSQL",
        doc_count, tpl_count,
    )
    return {"documents": doc_count, "templates": tpl_count}


def migrate_postgres_to_sqlite(
    pg_url: str,
    sqlite_path: str,
    source_user_id: uuid.UUID | None = None,
    include_all: bool = True,
) -> dict:
    """Copy documents and templates from PostgreSQL to SQLite.

    If *include_all* is True, copies all users' data.
    If False, copies only data belonging to *source_user_id*.
    Migrated records have user_id set to NULL (mono mode).
    """
    src = _make_pg_session(pg_url)
    dst = _make_sqlite_session(sqlite_path)
    doc_count = 0
    tpl_count = 0

    try:
        doc_query = src.query(Document)
        tpl_query = src.query(Template)

        if not include_all and source_user_id is not None:
            doc_query = doc_query.filter(Document.user_id == source_user_id)
            tpl_query = tpl_query.filter(Template.user_id == source_user_id)

        for doc in doc_query.all():
            new_doc = Document(
                id=doc.id,
                original_filename=doc.original_filename,
                file_path=doc.file_path,
                file_size=doc.file_size,
                page_count=doc.page_count,
                pages=doc.pages,
                detected_tables=doc.detected_tables,
                sha256=doc.sha256,
                user_id=None,
            )
            dst.merge(new_doc)
            doc_count += 1

            for job in src.query(Job).filter(Job.document_id == doc.id).all():
                new_job = Job(
                    id=job.id,
                    document_id=job.document_id,
                    status=job.status,
                    progress=job.progress,
                    message=job.message,
                    error_type=job.error_type,
                )
                dst.merge(new_job)

        for tpl in tpl_query.all():
            new_tpl = Template(
                id=tpl.id,
                name=tpl.name,
                selections=tpl.selections,
                selection_count=tpl.selection_count,
                page_count=tpl.page_count,
                user_id=None,
                is_shared=False,
            )
            dst.merge(new_tpl)
            tpl_count += 1

        dst.commit()
    finally:
        src.close()
        dst.close()

    logger.info(
        "Migrated %d documents and %d templates from PostgreSQL to SQLite",
        doc_count, tpl_count,
    )
    return {"documents": doc_count, "templates": tpl_count}
