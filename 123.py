from pydub import AudioSegment

# 🔊 병합할 MP3 파일 경로 리스트
mp3_files = ['11.mp3', '22.mp3', '33.mp3']

# 🎵 첫 번째 파일 로드
merged = AudioSegment.from_mp3(mp3_files[0])

# 🎧 나머지 파일 순차적으로 이어붙이기
for file in mp3_files[1:]:
    sound = AudioSegment.from_mp3(file)
    merged += sound

# 💾 최종 결과 저장
output_path = 'merged_output.mp3'
merged.export(output_path, format='mp3')
print(f"✅ 병합 완료: {output_path}")
