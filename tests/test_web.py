import importlib

import pytest
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Создаёт тестовый клиент с подменой директории для временных файлов."""
    monkeypatch.setattr("web.config.JOBS_BASE_DIR", tmp_path / "jobs")
    import web.web

    importlib.reload(web.web)
    from web.web import app

    return TestClient(app, follow_redirects=False)


def test_image_optimization_success(client, tmp_path):
    """Тест успешной оптимизации изображения."""
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path, format="PNG")

    with open(img_path, "rb") as f:
        response = client.post(
            "/image",
            files={"file": ("test.png", f, "image/png")},
            data={
                "output_format": "webp",
                "quality": 80,
                "max_width": 50,
                "max_height": 50,
                "contrast": 1.0,
                "sharpness": 1.0,
                "brightness": 1.0,
            },
        )
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/result/")
    job_id = location.split("/")[2].split("?")[0]
    job_dir = tmp_path / "jobs" / job_id
    assert job_dir.exists()
    output_files = list((job_dir / "output").glob("*"))
    assert len(output_files) > 0


def test_archive_creation_success(client, tmp_path):
    """Тест успешного создания архива."""
    file1 = tmp_path / "a.txt"
    file1.write_text("test1")
    file2 = tmp_path / "b.txt"
    file2.write_text("test2")

    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        response = client.post(
            "/archive",
            files=[
                ("files", ("a.txt", f1, "text/plain")),
                ("files", ("b.txt", f2, "text/plain")),
            ],
            data={
                "archive_format": "zip",
                "archive_name": "myarchive",
            },
        )
    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/result/")
    job_id = location.split("/")[2].split("?")[0]
    job_dir = tmp_path / "jobs" / job_id
    assert job_dir.exists()
    output_files = list((job_dir / "output").glob("*"))
    assert len(output_files) > 0


def test_download_result(client, tmp_path):
    """Тест скачивания результата и последующей очистки."""
    job_id = "testjob"
    job_dir = tmp_path / "jobs" / job_id
    job_dir.mkdir(parents=True)
    output_dir = job_dir / "output"
    output_dir.mkdir()
    fake_file = output_dir / "result.txt"
    fake_file.write_text("Hello world")

    response = client.get(f"/download/{job_id}/result.txt")
    assert response.status_code == 200
    assert response.content == b"Hello world"
    assert not job_dir.exists()


def test_result_page_not_found(client):
    """Тест страницы результата для несуществующей задачи."""
    response = client.get("/result/nonexistent?type=image")
    assert response.status_code == 404


def test_lang_switch(client):
    """Тест переключения языка."""
    response = client.get("/set_lang?lang=en&redirect=/")
    assert response.status_code == 303
    assert response.cookies.get("lang") == "en"
    assert response.headers["location"] == "/"
