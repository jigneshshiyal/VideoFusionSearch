import subprocess
import os
import ffmpeg

def get_video_info(video_path):
    try:
        probe = ffmpeg.probe(video_path)
        streams = probe.get("streams", [])

        video_info = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
        audio_info = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)

        return {
            "video_codec": video_info.get("codec_name") if video_info else None,
            "audio_codec": audio_info.get("codec_name") if audio_info else None,
            "format": probe.get("format", {}).get("format_name"),
            "duration": probe.get("format", {}).get("duration"),
            "width": video_info.get("width") if video_info else None,
            "height": video_info.get("height") if video_info else None,
            "bitrate": probe.get("format", {}).get("bit_rate"),
        }

    except Exception as e:
        return None

def extract_audio(video_path, output_audio_path="output_audio.wav"):
    """
    Extract audio from a video file and convert it to 16kHz mono WAV.

    Parameters:
    - video_path (str): Path to the input video file (.webm or .mp4)
    - output_audio_path (str): Path to save the extracted WAV audio
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # ffmpeg command
    command = [
        "ffmpeg",
        "-i", video_path,
        "-vn",  # disable video
        "-acodec", "pcm_s16le",  # uncompressed audio format
        "-ar", "16000",  # sample rate 16kHz
        "-ac", "1",  # mono channel
        output_audio_path,
        "-y"  # overwrite output if exists
    ]

    try:
        subprocess.run(command, check=True)
        print(f"✅ Audio extracted and saved to: {output_audio_path}")
        return True, output_audio_path
    except subprocess.CalledProcessError as e:
        print("❌ ffmpeg failed:", e)
        return False, None