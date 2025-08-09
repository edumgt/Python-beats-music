import os
import json
import song
import waveimport
from pydub import AudioSegment

FRAMERATE = waveimport.FRAMERATE
prj_path = './db/projects/'
os.makedirs(prj_path, exist_ok=True)

# === 변환 대상 JSON 파일 ===
json_file = prj_path + 'new.json'  # 예: 'all_patterns.json'

with open(json_file, 'r') as f:
    json_data = json.load(f)

for key, song_data in json_data.items():
    song_name = f"{key}_auto"
    wav_path = f"{prj_path}{song_name}.wav"
    mp3_path = wav_path.replace('.wav', '.mp3')

    print(f"\n🎵 Generating for: {song_name}")

    # Song 객체 생성
    s = song.Song()
    s.name = song_name
    s.nchannels = song_data.get("Channels", 2)
    s.repeat = song_data.get("Repeat", 8)
    s.data = song.generate_data(song_data["Tracks"], s.repeat)

    # 재생 (옵션)
    # song.play(s.nchannels, s.data, FRAMERATE, s.repeat)

    # WAV 저장
    song.record(s.name, s.nchannels, s.data, FRAMERATE, s.repeat)
    print(f"✅ WAV saved: {wav_path}")

    # MP3 저장
    sound = AudioSegment.from_wav(wav_path)
    sound.export(mp3_path, format="mp3")
    print(f"✅ MP3 saved: {mp3_path}")
