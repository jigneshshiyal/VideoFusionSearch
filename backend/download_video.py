import yt_dlp
import os
import glob

def download_video(url, output_path='.'):
    output_path = os.path.abspath(output_path)
    os.makedirs(output_path, exist_ok=True)

    temp_outtmpl = os.path.join(output_path, 'temp_download.%(ext)s')
    final_video_path = os.path.join(output_path, 'video.mp4')

    ydl_opts = {
        'outtmpl': temp_outtmpl,
        'format': 'bestvideo[height<=480][vcodec^=avc1]+bestaudio[acodec^=mp4a]/best[height<=480][ext=mp4]',
        'quiet': True,
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the final downloaded file (temp_download.mp4 or similar)
        downloaded_files = glob.glob(os.path.join(output_path, 'temp_download.*'))
        if not downloaded_files:
            return False, None

        downloaded_path = downloaded_files[0]

        # Rename only after everything is complete
        if downloaded_path != final_video_path:
            os.replace(downloaded_path, final_video_path)

        return True, final_video_path

    except Exception as e:
        return False, None
