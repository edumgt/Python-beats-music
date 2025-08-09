from pydub import AudioSegment

# 파일 불러오기
sound1 = AudioSegment.from_file("11.mp3", format="mp3")
sound2 = AudioSegment.from_file("22.mp3", format="mp3")
silence = AudioSegment.silent(duration=5000)  # 5초 정적

# 반복 조합 생성
combined = AudioSegment.empty()

for i in range(3):  # 3번 반복
    combined += sound1 + silence + sound2 + silence

# 결과 저장
combined.export("33.mp3", format="mp3")
print("✅ 33.mp3 has been created.")
