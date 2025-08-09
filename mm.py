from pydub import AudioSegment

# 파일 로드
sound1 = AudioSegment.from_file("11.mp3")
sound2 = AudioSegment.from_file("22.mp3")

# 두 사운드 길이를 맞춤 (짧은 쪽에 무음 추가)
max_len = max(len(sound1), len(sound2))
sound1 = sound1 + AudioSegment.silent(duration=max_len - len(sound1))
sound2 = sound2 + AudioSegment.silent(duration=max_len - len(sound2))

# 볼륨 조절 (선택적)
sound1 = sound1 - 3  # dB 단위 감소
sound2 = sound2 - 3

# 오버레이 (믹싱)
mixed = sound1.overlay(sound2)

# 결과 저장
mixed.export("mixed_output.mp3", format="mp3")
