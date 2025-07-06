import os
import cv2
import csv
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

def detect_scenes(video_path):
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=30.0))

    video_manager.set_downscale_factor()
    video_manager.start()

    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list()
    print(f"[INFO] Detected {len(scene_list)} scenes.")
    video_manager.release()
    return scene_list


def extract_frames_per_scene(video_path, output_dir, fps=0.5, save_csv=True):
    try:
        scene_list = detect_scenes(video_path)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        cap = cv2.VideoCapture(video_path)
        original_fps = cap.get(cv2.CAP_PROP_FPS)

        metadata = []

        for i, (start_time, end_time) in enumerate(scene_list):
            scene_start_frame = int(start_time.get_seconds() * original_fps)
            scene_end_frame = int(end_time.get_seconds() * original_fps)
            step = int(original_fps / fps)  # ⬅ this is now large for low fps (e.g., 60 if 30fps input and 0.5 fps target)

            cap.set(cv2.CAP_PROP_POS_FRAMES, scene_start_frame)
            frame_id = scene_start_frame
            frame_count = 0

            while frame_id < scene_end_frame:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
                ret, frame = cap.read()
                if not ret:
                    break

                timestamp_sec = frame_id / original_fps
                out_filename = f'scene_{i:03}_frame_{frame_count:04}.jpg'
                out_path = os.path.join(output_dir, out_filename)
                cv2.imwrite(out_path, frame)

                metadata.append({
                    "scene": i,
                    "frame_count": frame_count,
                    "frame_id": frame_id,
                    "timestamp_sec": round(timestamp_sec, 3),
                    "file_name": out_filename
                })

                frame_id += step
                frame_count += 1

        cap.release()
        print(f"[INFO] Frames saved in {output_dir}")

        if save_csv and metadata:
            csv_path = os.path.join(output_dir, "frame_metadata.csv")
            with open(csv_path, mode='w', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=metadata[0].keys())
                writer.writeheader()
                writer.writerows(metadata)
            print(f"[INFO] Frame metadata saved to {csv_path}")
        
        return True, output_dir, csv_path, "Success"
    except Exception as e:
        print(e)
        
        return False, None, None, f"Error: {e}"

        

