from pydub import AudioSegment
import os

# ffmpeg 경로가 필요한 경우 수동 지정
# AudioSegment.converter = "C:\\ffmpeg\\bin\\ffmpeg.exe"

def cut_mp3(input_file, start_sec, end_sec):
    try:
        # MP3 로딩
        audio = AudioSegment.from_mp3(input_file)
        start_ms = int(start_sec * 1000)
        end_ms = int(end_sec * 1000)

        # 유효성 검사
        if start_ms < 0 or end_ms > len(audio):
            print(f"❌ 범위 오류: 전체 길이 {len(audio)/1000:.2f}초")
            return

        if start_ms >= end_ms:
            print("❌ 시작 시간이 종료 시간보다 크거나 같습니다.")
            return

        # 자르기
        cut_audio = audio[start_ms:end_ms]

        # 출력 파일명 생성
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_cut_{start_sec}s_to_{end_sec}s.mp3"

        cut_audio.export(output_file, format="mp3")
        print(f"✅ 잘라낸 MP3 저장 완료: {output_file}")
    except FileNotFoundError:
        print("❌ 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    print("🎵 MP3 자르기 도구")

    input_file = input("▶ MP3 파일명을 입력하세요 (예: song.mp3): ").strip()
    try:
        start_time = float(input("⏱ 시작 시간(초): "))
        end_time = float(input("⏱ 종료 시간(초): "))
        cut_mp3(input_file, start_time, end_time)
    except ValueError:
        print("❌ 숫자 형식이 잘못되었습니다.")
