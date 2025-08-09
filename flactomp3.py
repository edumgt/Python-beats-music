from pydub import AudioSegment
import os

def convert_flac_to_mp3(input_path, output_path, bitrate="320k"):
    try:
        audio = AudioSegment.from_file(input_path, format="flac")
        audio.export(output_path, format="mp3", bitrate=bitrate)
        print(f"✅ Converted: {input_path} → {output_path}")
    except Exception as e:
        print(f"❌ Error converting {input_path}: {e}")

# 예시 사용
convert_flac_to_mp3("11.flac", "11.mp3")
