import os
import random
import ffmpeg
import cv2
from rembg import remove
from PIL import Image
import numpy as np

# === 사용자 설정 ===
input_videos = ["1.mp4", "2.mp4", "3.mp4", "4.mp4", "5.mp4", "6.mp4"]
background_images = [f"bg{i}.jpg" for i in range(1, 8)]
crop_positions = ["center", "right", "left"]
start_time = 6
duration = 16

def process_video(input_file, background_image, crop_position, output_name):
    # ffmpeg로 영상 정보 추출
    probe = ffmpeg.probe(input_file)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    original_width = int(video_info['width'])
    original_height = int(video_info['height'])

    target_height = original_height
    target_width = int(target_height * 2 / 3)

    if crop_position == "center":
        crop_x = (original_width - target_width) // 2
    elif crop_position == "left":
        crop_x = 240
    elif crop_position == "right":
        crop_x = original_width - target_width - 200
    else:
        raise ValueError("crop 위치는 'center', 'left', 'right' 중 하나여야 합니다.")

    crop_y = 0
    temp_cropped = f"temp_{output_name}_cropped.mp4"
    temp_no_audio = f"temp_{output_name}_no_audio.mp4"
    final_output = f"{output_name}.mp4"

    # ffmpeg로 자르고 크롭
    input_stream = ffmpeg.input(input_file, ss=start_time, t=duration)
    video = input_stream.video.crop(x=crop_x, y=crop_y, width=target_width, height=target_height)
    audio = input_stream.audio
    ffmpeg.output(video, audio, temp_cropped, vcodec='libx264', acodec='aac').run(overwrite_output=True)

    # 배경 제거 + 합성
    cap = cv2.VideoCapture(temp_cropped)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    bg_img = Image.open(background_image).resize((width, height))
    out = cv2.VideoWriter(temp_no_audio, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)

        # rembg + 합성
        fg_removed = remove(pil_img)
        fg = Image.alpha_composite(bg_img.convert("RGBA"), fg_removed.convert("RGBA"))
        result = cv2.cvtColor(np.array(fg), cv2.COLOR_RGBA2BGR)
        out.write(result)

    cap.release()
    out.release()

    # 오디오 재결합
    input_video = ffmpeg.input(temp_no_audio)
    input_audio = ffmpeg.input(temp_cropped)
    ffmpeg.output(
        input_video.video,
        input_audio.audio,
        final_output,
        vcodec='libx264',
        acodec='aac'
    ).run(overwrite_output=True)

    # 임시 파일 삭제
    os.remove(temp_cropped)
    os.remove(temp_no_audio)

    print(f"✅ 생성 완료: {final_output}")

# === 실행 ===
for input_file in input_videos:
    for crop_position in crop_positions:
        bg = random.choice(background_images)
        name_prefix = os.path.splitext(input_file)[0]
        output_name = f"{name_prefix}-{crop_position.capitalize()}"
        print(f"▶️ {input_file}, {crop_position} → {output_name}.mp4 (배경: {bg})")
        process_video(input_file, bg, crop_position, output_name)
