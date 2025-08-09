import ffmpeg

# 사용자 입력
input_file = input("🎬 입력 파일명 (예: input.mp4): ").strip()
output_file = input("💾 출력 파일명 (예: output.mp4): ").strip()
start_time = int(input("⏱ 시작 시간 (초 단위): ").strip())
duration_seconds = int(input("⏳ 길이 (초 단위): ").strip())

crop_position = input("📍 crop 위치 (center / left / right): ").strip().lower()
if crop_position not in ["center", "left", "right"]:
    raise ValueError("crop 위치는 'center', 'left', 'right' 중 하나여야 합니다.")

# 1. 비디오 정보 추출
probe = ffmpeg.probe(input_file)
video_streams = [s for s in probe['streams'] if s['codec_type'] == 'video']
if not video_streams:
    raise ValueError("비디오 스트림 없음")
video_info = video_streams[0]
original_width = int(video_info['width'])
original_height = int(video_info['height'])

print(f"📐 원본 해상도: {original_width}x{original_height}")

# 2. 타겟 해상도 (2:3 비율)
target_height = original_height
target_width = int(target_height * 2 / 3)
if target_width > original_width:
    raise ValueError(f"Crop width({target_width})가 원본보다 큽니다. 원본 width: {original_width}")

# 3. crop 위치 계산
if crop_position == "center":
    crop_x = (original_width - target_width) // 2
elif crop_position == "left":
    crop_x = 20
elif crop_position == "right":
    crop_x = original_width - target_width - 200

crop_y = 0

print(f"📏 crop 위치: x={crop_x}, y={crop_y}, width={target_width}, height={target_height}")

# 4. ffmpeg 입력 + crop + trim + 오디오 포함
input_stream = ffmpeg.input(input_file, ss=start_time, t=duration_seconds)
video = input_stream.video.crop(x=crop_x, y=crop_y, width=target_width, height=target_height)
audio = input_stream.audio

# 5. 출력
(
    ffmpeg
    .output(video, audio, output_file, vcodec='libx264', acodec='aac')
    .run()
)

print(f"✅ 변환 완료: {output_file}")
