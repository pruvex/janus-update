import os
import tempfile
from unittest.mock import patch


from backend.data.models import Document
from backend.tools.pdf_generator import register_and_index_file


def _create_dummy_pdf() -> str:
    fd, path = tempfile.mkstemp(suffix=".pdf")
    try:
        os.write(fd, b"%PDF-1.4\n%%EOF\n")
    finally:
        os.close(fd)
    return path


def test_pdf_status_flow(db_session):
    pdf_path = _create_dummy_pdf()
    try:
        with patch("backend.tools.pdf_generator.rag_manager.index_document"):
            doc_id = register_and_index_file("status_flow.pdf", pdf_path, db_session)
        assert doc_id is not None
        doc = db_session.get(Document, doc_id)
        assert doc is not None
        assert doc.audit_status == "new"

        doc.audit_status = "warning"
        db_session.commit()
        db_session.refresh(doc)
        assert doc.audit_status == "warning"

        with patch("backend.tools.pdf_generator.rag_manager.index_document"):
            register_and_index_file("status_flow.pdf", pdf_path, db_session, audit_status="verified")
        updated_doc = db_session.get(Document, doc_id)
        assert updated_doc is not None
        assert updated_doc.audit_status == "verified"
    finally:
        os.remove(pdf_path)
