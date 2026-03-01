"""온라인 MP3 다운로드 + MP3->WAV 변환 스모크 테스트 스크립트.

기본 URL은 샘플 MP3 파일이며, 네트워크/ffmpeg 환경에 따라 실패할 수 있습니다.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import urlretrieve

DEFAULT_URL = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"


def main() -> int:
    parser = argparse.ArgumentParser(description="Download MP3 from web and convert to WAV")
    parser.add_argument("--url", default=DEFAULT_URL, help="MP3 URL to download")
    parser.add_argument("--out-dir", default="data/manual_test", help="Output directory")
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("❌ ffmpeg를 찾을 수 없습니다. MP3 변환 테스트를 실행할 수 없습니다.")
        return 2

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    mp3_path = out_dir / "sample.mp3"
    wav_path = out_dir / "sample.wav"

    print(f"🌐 다운로드 시도: {args.url}")
    try:
        urlretrieve(args.url, mp3_path)
    except (HTTPError, URLError, OSError) as exc:
        print(f"❌ MP3 다운로드 실패: {exc}")
        return 3

    print(f"🎵 변환 시도: {mp3_path} -> {wav_path}")
    cmd = [ffmpeg, "-y", "-i", str(mp3_path), str(wav_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print("❌ ffmpeg 변환 실패")
        print(proc.stderr)
        return proc.returncode

    print(f"✅ 변환 완료: {wav_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
