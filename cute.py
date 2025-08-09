import librosa
import soundfile as sf
from pydub import AudioSegment
import os

def convert_to_puppy(input_mp3, output_mp3):
    # Step 1: MP3 → WAV
    sound = AudioSegment.from_mp3(input_mp3)
    wav_path = "temp_input.wav"
    sound.export(wav_path, format="wav")

    # Step 2: 로드 & 피치/속도 변환
    y, sr = librosa.load(wav_path)
    
    # ✅ 올바르게 keyword arguments로 호출
    y_pitched = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=4)
    y_faster = librosa.effects.time_stretch(y_pitched, rate=1.1)

    # Step 3: 저장
    temp_output = "temp_output.wav"
    sf.write(temp_output, y_faster, sr)

    # Step 4: WAV → MP3
    final_sound = AudioSegment.from_wav(temp_output)
    final_sound.export(output_mp3, format="mp3")
    print(f"✅ 변환 완료: {output_mp3}")

    # Cleanup
    os.remove(wav_path)
    os.remove(temp_output)

# 사용 예시
convert_to_puppy("111.mp3", "1111.mp3")
