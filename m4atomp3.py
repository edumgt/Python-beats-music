from pydub import AudioSegment
import os

def convert_m4a_to_mp3(input_path, output_path=None, bitrate="192k"):
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".mp3"
    
    try:
        audio = AudioSegment.from_file(input_path, format="m4a")
        audio.export(output_path, format="mp3", bitrate=bitrate)
        print(f"✅ 변환 완료: {output_path}")
    except Exception as e:
        print(f"❌ 변환 실패: {e}")

# 예시 사용
convert_m4a_to_mp3("11.m4a")
# 예시