import tempfile
import shutil
import os

from download_video import download_video
from audio_processing import extract_audio
from extract_text import extract_text
from chromadb_functions import save_text_emb_in_db, save_img_emb_in_db, check_url_in_db
from extract_scenes_from_video import extract_frames_per_scene
from backend.search_functions import multimodel_search

def convert_seconds_to_time_str(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02}"

def video_audio_fusion_search(video_url):
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        check_url_status, is_url_present, check_url_message = check_url_in_db(video_url)
        if is_url_present:
            return True, "Success"

        # Step 1: Download Video
        video_download_status, video_file_path = download_video(video_url, output_path=temp_dir)
        if not video_download_status:
            raise Exception("Video is not downloaded.")

        # Step 2: Extract Audio
        output_audio_path = os.path.join(temp_dir, "output_audio.wav")
        audio_convert_status, audio_file_path = extract_audio(video_file_path, output_audio_path=output_audio_path)
        if not audio_convert_status:
            raise Exception("Audio extraction failed.")

        # Step 3: Extract Text
        extract_text_status, text_segments, full_text, message = extract_text(audio_file_path)
        if not extract_text_status:
            raise Exception(f"Text extraction failed: {message}")

        # Step 4: Save Text Embeddings
        save_text_emb_status, save_text_emb_message = save_text_emb_in_db(text_segments, video_url)
        if not save_text_emb_status:
            raise Exception(f"Saving text embeddings failed: {save_text_emb_message}")

        # Step 5: Extract Frames per Scene
        scenes_tmp_folder = os.path.join(temp_dir, "scenes")
        extract_frames_status, scenes_folder_path, scenes_csv_path, scenes_create_message = extract_frames_per_scene(
            video_file_path, output_dir=scenes_tmp_folder, fps=0.5, save_csv=True
        )
        if not extract_frames_status:
            raise Exception(f"Scene frame extraction failed: {scenes_create_message}")

        # Step 6: Save Image Embeddings
        save_img_emb_status, save_img_emb_message = save_img_emb_in_db(scenes_folder_path, scenes_csv_path, video_url)
        if not save_img_emb_status:
            raise Exception(f"Saving image embeddings failed: {save_img_emb_message}")

        return True, "Success"

    except Exception as e:
        return False, f"Error: {e}"

    finally:
        # Clean up the temporary directory
        try:
            shutil.rmtree(temp_dir)
        except Exception as cleanup_err:
            print(f"Cleanup failed: {cleanup_err}")
