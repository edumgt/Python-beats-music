# === beats.py 연동용 ===
import os
import song
import waveimport
from pydub import AudioSegment

FRAMERATE = waveimport.FRAMERATE

userinput = input("Enter song name: ")
SONG = song.Song(userinput)
print(f"✅ Loaded song: {SONG.name}")

song.play(SONG.nchannels, SONG.data, FRAMERATE, SONG.repeat)

# === mp3 자동 저장 ===
prj_path = './db/projects/'
wav_path = f"{prj_path}{userinput}.wav"
mp3_path = wav_path.replace('.wav', '.mp3')

song.record(userinput, SONG.nchannels, SONG.data, FRAMERATE, SONG.repeat)
print(f"✅ WAV file saved: {wav_path}")

sound = AudioSegment.from_wav(wav_path)
sound.export(mp3_path, format='mp3')
print(f"✅ MP3 file saved: {mp3_path}")

# === json 합치기/리팩토링 ===
import json

def merge_json(file1, file2, output_file):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    merged = {
        "merged": {
            "Tempo": max(data1[list(data1.keys())[0]]['Tempo'], data2[list(data2.keys())[0]]['Tempo']),
            "Channels": 2,
            "Beat": "....",
            "Repeat": 2,
            "Tracks": {}
        }
    }

    tracks = {}
    idx = 0
    for src in [data1, data2]:
        key = list(src.keys())[0]
        for tnum, tdata in src[key]['Tracks'].items():
            tracks[str(idx)] = tdata
            idx += 1

    merged['merged']['Tracks'] = tracks

    with open(output_file, 'w') as out:
        json.dump(merged, out, indent=2)

    print(f"✅ Merged JSON saved to {output_file}")

# 예시 실행
# merge_json('gym.json', 'new.json', 'merged_gym_new.json')
