from pydub import AudioSegment
from pydub.silence import detect_nonsilent

# 파일 불러오기
sound = AudioSegment.from_file("back.mp3", format="mp3")

# 무음이 아닌 구간(nonsilent)을 감지 (단위: 밀리초)
# silence_thresh: 음량 임계값 (기본 -50dBFS)
# min_silence_len: 무음으로 간주할 최소 길이 (여기선 300ms 이상이면 무음으로 간주)
nonsilent_ranges = detect_nonsilent(sound, min_silence_len=50, silence_thresh=-50)

# 무음이 아닌 구간을 잘라서 이어붙임
output = AudioSegment.empty()
for start, end in nonsilent_ranges:
    output += sound[start:end]

# 결과를 다시 33.mp3로 저장 (덮어쓰기)
output.export("back.mp3", format="mp3")
print("✅ 무음 제거 후 33.mp3로 저장 완료.")
