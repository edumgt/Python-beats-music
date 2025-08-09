import ffmpeg

def extract_audio_30sec(input_path, output_path):
    (
        ffmpeg
        .input(input_path)
        .output(output_path, format='mp3', acodec='libmp3lame', t=30)
        .run(overwrite_output=True)
    )
    print(f"✅ 30초 MP3 저장 완료: {output_path}")

# 사용 예
extract_audio_30sec("1.mp4", "back_30s.mp3")
