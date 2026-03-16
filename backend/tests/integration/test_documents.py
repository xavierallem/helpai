"""Integration tests for the documents endpoints."""

import io


class TestDocumentsEndpoints:
    def _make_pdf_upload(self, filename="test.pdf", content=b"%PDF-1.4 fake"):
        return {"file": (filename, io.BytesIO(content), "application/pdf")}

    def test_upload_non_pdf_returns_400(self, api_client):
        files = {"file": ("document.txt", io.BytesIO(b"hello"), "text/plain")}
        response = api_client.post(
            "/api/documents",
            files=files,
            data={"title": "My Doc"},
        )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_missing_title_returns_422(self, api_client):
        response = api_client.post(
            "/api/documents",
            files=self._make_pdf_upload(),
        )
        assert response.status_code == 422

    def test_upload_oversized_file_returns_400(self, api_client):
        big_content = b"%PDF-1.4 " + b"x" * (51 * 1024 * 1024)
        files = {"file": ("big.pdf", io.BytesIO(big_content), "application/pdf")}
        response = api_client.post(
            "/api/documents",
            files=files,
            data={"title": "Big Doc"},
        )
        assert response.status_code == 400
        assert "size" in response.json()["detail"].lower()
