import os
import re
import subprocess
from pydub import AudioSegment
import openai
from dotenv import load_dotenv
load_dotenv()
# === 설정 ===
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4"
SF2_PATH = "C:/soundfonts/GAX_Sound_Engine_Soundfont__V1_.sf2"
MIDI_PATH = "chord_progression.mid"
WAV_PATH = "chord_progression.wav"
MP3_PATH = "chord_progression.mp3"
TARGET_DURATION_MS = 30000

# === OpenAI API 설정 ===
openai.api_key = API_KEY
if not API_KEY:
    raise EnvironmentError("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")



prompt = """
K-POP 감성의 감미로운 발라드 분위기를 바탕으로, 웅장한 오케스트라 스타일의 음악을 생성해줘.  
Python의 midiutil 라이브러리를 사용해서 60마디 분량의 코드 진행 기반 멀티 트랙 MIDI 파일을 생성하고,  
리드미컬하게 연주되도록 구성해줘.

다음 조건을 반드시 반영해줘:

- 템포는 60bpm, 각 마디는 0.3초 길이
- `MIDIFile(10)`처럼 충분한 트랙 수를 생성해야 함 (트랙 번호 9번 사용 예정이므로 최소 10트랙)
- 트랙/채널 구성:
  - **Track 0 / Channel 0**: 피아노 코드 진행 (Cmaj7 → Am7 → Dm7 → G7 반복, 마디당 3회 반복 또는 아르페지오 구성)
  - **Track 1 / Channel 0**: 콘트라베이스처럼 부드러운 베이스 루트음 (마디당 2회)
  - **Track 2 / Channel 1**: 스트링 패드 (각 마디에서 코드의 루트 + 7도 정도를 길게 지속)
  - **Track 3 / Channel 2**: 브라스 섹션 (4마디마다 한 번 울리며 웅장함 추가)
  - **Track 9 / Channel 9 (GM 드럼)**: 킥(36), 스네어(38), 하이햇(42), 팀파니(47), 심벌(49) 등 포함

- `start_time`은 누적되도록 구성해줘서 마디 간 끊김이 없도록 해줘.
- 악기별로 겹치지 않도록 음역대를 조절해서 조화롭게 배치해줘.
- 마지막에 `'chord_progression.mid'`로 저장해주는 코드로 마무리해줘.

코드 실행에 오류가 없도록 `addTrackName`, `addTempo` 등에서 트랙 번호가 MIDIFile에 정의된 트랙 수를 초과하지 않도록 반드시 주의해줘.
함수 내부에서 사용하는 모든 객체(midi 등)는 함수 정의 전에 전역에서 먼저 생성되거나, 함수의 인자로 전달되도록 만들어줘.

설명은 하지 말고, 실행 가능한 전체 Python 코드를 코드 블록 안에 포함해줘.



"""



def generate_code_from_gpt(prompt):
    print("🤖 GPT에게 코드 요청 중...")
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You're a Python composer."},
            {"role": "user", "content": prompt}
        ]
    )
    content = response["choices"][0]["message"]["content"]
    match = re.search(r"```(?:python)?\n([\s\S]+?)```", content)
    code = match.group(1) if match else content.strip()
    return code

def run_generated_code(code):
    print("🎹 GPT가 생성한 코드 실행 중...\n")
    print(code)
    exec(code)

def convert_midi_to_wav(sf2_path, midi_path, wav_path):
    if not os.path.exists(sf2_path):
        raise FileNotFoundError(f"❌ SoundFont 파일이 없습니다: {sf2_path}")
    if not os.path.exists(midi_path):
        raise FileNotFoundError(f"❌ MIDI 파일이 없습니다: {midi_path}")

    command = [
        "fluidsynth", "-ni",
        "-F", wav_path,
        "-r", "44100",
        sf2_path, midi_path
    ]
    print(f"\n🎼 fluidsynth 실행: {' '.join(command)}")
    subprocess.run(command, check=True)
    print(f"✅ WAV 생성 완료: {wav_path}")

def trim_or_pad_wav(wav_path, target_ms):
    print("⏱️ WAV를 30초로 맞추는 중...")
    sound = AudioSegment.from_wav(wav_path)
    if len(sound) < target_ms:
        silence = AudioSegment.silent(duration=target_ms - len(sound))
        sound += silence
    else:
        sound = sound[:target_ms]
    return sound

def export_to_mp3(audio_segment, mp3_path):
    audio_segment.export(mp3_path, format="mp3")
    print(f"✅ MP3 생성 완료: {mp3_path}")

# === 실행 흐름 ===
if __name__ == "__main__":
    generated_code = generate_code_from_gpt(prompt)
    run_generated_code(generated_code)
    convert_midi_to_wav(SF2_PATH, MIDI_PATH, WAV_PATH)
    final_audio = trim_or_pad_wav(WAV_PATH, TARGET_DURATION_MS)
    export_to_mp3(final_audio, MP3_PATH)
