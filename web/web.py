"""Веб-интерфейс для FileOptimizer на FastAPI с поддержкой Babel."""

import json
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from babel.support import Translations
from jinja2.ext import i18n

from config import TEMPLATES_DIR, STATIC_DIR, JOBS_BASE_DIR, MAX_UPLOAD_SIZE, LOCALES_DIR
from fileoptimizer.storage import StorageService
from fileoptimizer.image_optimizer import ImageOptimizer
from fileoptimizer.archive_service import ArchiveService
from fileoptimizer.exceptions import (
    FileOptimizerError,
    UnsupportedFormatError,
    OptimizationError,
    StorageError,
    ArchiveCreationError,
)
from fileoptimizer.models import ImageOptimizeResult, ArchiveResult

app = FastAPI(title="FileOptimizer", version="0.1.0")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.add_extension(i18n)



storage_service = StorageService(base_dir=JOBS_BASE_DIR)
image_optimizer = ImageOptimizer()
archive_service = ArchiveService()


@app.middleware("http")
async def set_locale(request: Request, call_next):
    """Устанавливает язык из куки или параметра запроса для текущего запроса."""
    lang = request.query_params.get("lang")
    if lang and lang in ("ru", "en"):
        response = await call_next(request)
        response.set_cookie("lang", lang)
        return response

    lang = request.cookies.get("lang", "ru")
    translations = Translations.load(LOCALES_DIR, [lang])
    templates.env.install_gettext_translations(translations, newstyle=True)
    request.state.lang = lang
    response = await call_next(request)
    return response


@app.exception_handler(FileOptimizerError)
async def file_optimizer_exception_handler(request: Request, exc: FileOptimizerError):
    """Обработка пользовательских ошибок FileOptimizer."""
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error": str(exc)},
        status_code=400,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Обработка HTTP-ошибок (404 и т.п.)."""
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error": exc.detail},
        status_code=exc.status_code,
    )


def cleanup_job(job_dir: Path) -> None:
    """Удаляет папку задачи (используется в фоновых задачах)."""
    try:
        storage_service.cleanup_job_dir(job_dir)
    except Exception as e:
        print(f"Cleanup error for {job_dir}: {e}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница с выбором инструмента."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/image", response_class=HTMLResponse)
async def image_form(request: Request):
    """Форма для оптимизации изображений."""
    return templates.TemplateResponse("image_form.html", {"request": request})


@app.post("/image", response_class=HTMLResponse)
async def process_image(
    request: Request,
    file: UploadFile = File(...),
    output_format: str = Form("webp"),
    quality: int = Form(75),
    max_width: Optional[int] = Form(None),
    max_height: Optional[int] = Form(None),
    contrast: float = Form(1.0),
    sharpness: float = Form(1.0),
    brightness: float = Form(1.0),
):
    """Обработка загруженного изображения."""
    try:
        file_content = await file.read()
        if len(file_content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        job_dir = storage_service.create_job_dir()
        input_dir = storage_service.get_input_dir(job_dir)

        temp_path = input_dir / file.filename
        with open(temp_path, "wb") as f:
            f.write(file_content)

        result: ImageOptimizeResult = image_optimizer.optimize(
            input_path=temp_path,
            output_dir=storage_service.get_output_dir(job_dir),
            output_format=output_format,
            quality=quality,
            max_width=max_width if max_width and max_width > 0 else None,
            max_height=max_height if max_height and max_height > 0 else None,
            contrast_factor=contrast,
            sharpness_factor=sharpness,
            brightness_factor=brightness,
        )

        return RedirectResponse(
            url=f"/result/{job_dir.name}?type=image",
            status_code=303,
        )
    except (UnsupportedFormatError, OptimizationError, ValueError) as e:
        return templates.TemplateResponse(
            "image_form.html",
            {"request": request, "error": str(e)},
            status_code=400,
        )
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/archive", response_class=HTMLResponse)
async def archive_form(request: Request):
    """Форма для создания архива."""
    return templates.TemplateResponse("archive_form.html", {"request": request})


@app.post("/archive", response_class=HTMLResponse)
async def process_archive(
    request: Request,
    files: List[UploadFile] = File(...),
    archive_format: str = Form("zip"),
    archive_name: str = Form("archive"),
):
    """Обработка загрузки нескольких файлов и создание архива."""
    try:
        if not files or len(files) == 0:
            raise ValueError("No files uploaded")

        job_dir = storage_service.create_job_dir()
        input_dir = storage_service.get_input_dir(job_dir)

        input_paths = []
        for uploaded_file in files:
            if uploaded_file.filename == "":
                continue
            content = await uploaded_file.read()
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File {uploaded_file.filename} too large"
                )
            file_path = input_dir / uploaded_file.filename
            with open(file_path, "wb") as f:
                f.write(content)
            input_paths.append(file_path)

        if not input_paths:
            raise ValueError("No valid files to archive")

        result: ArchiveResult = archive_service.create_archive(
            input_paths=input_paths,
            output_dir=storage_service.get_output_dir(job_dir),
            archive_name=archive_name,
            archive_format=archive_format,
        )

        return RedirectResponse(
            url=f"/result/{job_dir.name}?type=archive",
            status_code=303,
        )
    except (UnsupportedFormatError, ArchiveCreationError, ValueError) as e:
        return templates.TemplateResponse(
            "archive_form.html",
            {"request": request, "error": str(e)},
            status_code=400,
        )
    except StorageError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/result/{job_id}", response_class=HTMLResponse)
async def show_result(request: Request, job_id: str, type: str):
    """Страница результата обработки."""
    job_dir = JOBS_BASE_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    output_dir = storage_service.get_output_dir(job_dir)
    output_files = list(output_dir.glob("*"))
    if not output_files:
        raise HTTPException(status_code=404, detail="Result file not found")

    result_file = output_files[0]
    file_size = result_file.stat().st_size

    context = {
        "request": request,
        "job_id": job_id,
        "result_file": result_file.name,
        "file_size": file_size,
        "result_type": type,
    }
    return templates.TemplateResponse("result.html", context)


@app.get("/download/{job_id}/{filename}")
async def download_result(
    request: Request,
    job_id: str,
    filename: str,
    background_tasks: BackgroundTasks,
):
    """Скачивание обработанного файла и удаление job-директории."""
    job_dir = JOBS_BASE_DIR / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    file_path = job_dir / "output" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    background_tasks.add_task(cleanup_job, job_dir)

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


def main():
    """Запуск веб-сервера через uvicorn."""
    import uvicorn
    uvicorn.run("web:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()