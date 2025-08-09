import subprocess
import os
import math
from pydub import AudioSegment

# === 입력 파일
video_file = "music0001.mp4"
audio_file = "1_mixed.mp3"
output_file = "output.mp4"

# === 1. MP3 길이 계산 (ms → s)
audio = AudioSegment.from_mp3(audio_file)
audio_duration = audio.duration_seconds

# === 2. MP4 길이 계산
probe = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=noprint_wrappers=1:nokey=1", video_file],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)
video_duration = float(probe.stdout)
repeat_count = math.ceil(audio_duration / video_duration)

# === 3. 반복용 텍스트 리스트 생성
with open("inputs.txt", "w") as f:
    for _ in range(repeat_count):
        f.write(f"file '{os.path.abspath(video_file)}'\n")

# === 4. 영상 반복 (concat)
concat_video = "looped.mp4"
subprocess.run([
    "ffmpeg", "-f", "concat", "-safe", "0", "-i", "inputs.txt",
    "-c", "copy", concat_video
])

# === 5. 영상 자르기 (정확히 오디오 길이만큼)
trimmed_video = "trimmed.mp4"
subprocess.run([
    "ffmpeg", "-y", "-i", concat_video, "-t", str(audio_duration),
    "-c", "copy", trimmed_video
])

# === 6. 오디오 입히기
subprocess.run([
    "ffmpeg", "-y", "-i", trimmed_video, "-i", audio_file,
    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", output_file
])

print(f"✅ 생성 완료: {output_file}")
