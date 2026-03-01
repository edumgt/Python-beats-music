from __future__ import annotations

from pathlib import Path

from app.celery_app import celery_app
from app.config import settings
from app.music_pipeline import render_grand_piano_backing


@celery_app.task(bind=True, name="tasks.make_piano_backing")
def make_piano_backing(
    self,
    input_filename: str,
    output_filename: str,
    dramatic_level: int,
    target_bpm: int | None,
) -> dict[str, str]:
    input_path = settings.upload_dir / input_filename
    output_path = settings.output_dir / output_filename

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    rendered_path: Path = render_grand_piano_backing(
        input_path=input_path,
        output_path=output_path,
        dramatic_level=dramatic_level,
        target_bpm=target_bpm,
    )

    return {"output_file": rendered_path.name}
