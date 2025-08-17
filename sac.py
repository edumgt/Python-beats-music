import argparse
import os
import time
import numpy as np
import soundcard as sc
import soundfile as sf

try:
    from pydub import AudioSegment
    HAVE_PYDUB = True
except Exception:
    HAVE_PYDUB = False


def capture_to_wav_w_loopback(duration, wav_path, samplerate=48000, channels=2, block_seconds=1.0):
    """
    soundcard로 시스템 사운드(스피커 loopback) 캡처 → WAV 실시간 기록
    """
    # 기본 스피커의 loopback 마이크 핸들
    mic = sc.get_microphone(sc.default_speaker().name, include_loopback=True)
    frames_per_block = int(samplerate * block_seconds)
    total_blocks = int(np.ceil(duration / block_seconds))

    print(f"[INFO] Loopback device: {mic.name}")
    print(f"[INFO] {samplerate} Hz, {channels} ch, duration={duration}s -> {wav_path}")

    with mic.recorder(samplerate=samplerate, channels=channels) as rec, \
         sf.SoundFile(wav_path, mode="w", samplerate=samplerate, channels=channels, subtype="PCM_16") as wav:
        start = time.time()
        for i in range(total_blocks):
            # 남은 시간 계산해 마지막 블록 길이 조정
            elapsed = time.time() - start
            remain = max(0.0, duration - elapsed)
            if remain <= 0:
                break
            cur_block = frames_per_block if remain >= block_seconds else int(remain * samplerate)

            data = rec.record(cur_block)  # float32 [-1,1]
            wav.write(data)               # soundfile가 float32 → PCM_16 변환
    print("[OK] WAV saved.")


def wav_to_mp3(wav_path, mp3_path, bitrate="192k"):
    if not HAVE_PYDUB:
        raise RuntimeError("pydub이 없습니다. `pip install pydub` 후 다시 시도하세요.")
    print("[INFO] Converting to MP3 ...")
    AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3", bitrate=bitrate)
    print(f"[OK] MP3 saved: {mp3_path}")


def main():
    ap = argparse.ArgumentParser(description="Capture system audio (loopback) with soundcard")
    ap.add_argument("--duration", type=float, default=60.0, help="녹음 길이(초)")
    ap.add_argument("--samplerate", type=int, default=48000, help="샘플레이트")
    ap.add_argument("--channels", type=int, default=2, help="채널 (1/2)")
    ap.add_argument("--outfile", type=str, default="system.mp3", help="출력 파일(.wav 또는 .mp3)")
    ap.add_argument("--bitrate", type=str, default="192k", help="MP3 비트레이트")
    ap.add_argument("--block-seconds", type=float, default=1.0, help="버퍼 블록 길이(초)")
    args = ap.parse_args()

    is_mp3 = args.outfile.lower().endswith(".mp3")
    wav_path = args.outfile if not is_mp3 else args.outfile[:-4] + ".tmp.wav"

    try:
        capture_to_wav_w_loopback(
            duration=args.duration,
            wav_path=wav_path,
            samplerate=args.samplerate,
            channels=args.channels,
            block_seconds=args.block_seconds,
        )
        if is_mp3:
            wav_to_mp3(wav_path, args.outfile, bitrate=args.bitrate)
            try:
                os.remove(wav_path)
            except Exception:
                pass
        else:
            print(f"[OK] Saved: {wav_path}")
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user.")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()

# python sac.py --duration 2400 --outfile system.mp3