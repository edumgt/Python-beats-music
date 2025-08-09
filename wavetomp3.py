from pydub import AudioSegment

# wav 파일 불러오기
sound = AudioSegment.from_wav("11.wav")

# mp3로 저장하기
sound.export("11.mp3", format="mp3")

print("변환 완료: output.mp3")
