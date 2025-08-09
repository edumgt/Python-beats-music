from pydub import AudioSegment
import os

# 🔍 변환할 MP3 파일 경로
input_mp3 = "launcher7.mp3"

# 🧠 MP3 파일 로드
audio = AudioSegment.from_mp3(input_mp3)

# 💾 WAV 파일로 저장
output_wav = "kic_heavy3.wav"
audio.export(output_wav, format="wav")

print(f"✅ 변환 완료: {output_wav}")
