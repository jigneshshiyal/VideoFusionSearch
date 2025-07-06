import chromadb
from image_text_emb import get_text_embbeding, get_image_embeddings_batch
import os
import pandas as pd

client = chromadb.PersistentClient(path="./store_emb")

collection = client.get_or_create_collection(
    name="img_text_emb", 
    configuration={
        "hnsw": {
            "space": "cosine",
            "ef_construction": 200,
            "max_neighbors":32
        }
    }
)

def check_url_in_db(video_url):
    try:
        query_result = collection.get(
            where={"video_url": video_url},
        )

        num_result = len(query_result["ids"])

        if num_result == 0:
            return True, False, "Success"
        else:
            return True, True, "Success"
    except Exception as e:
        return False, False, f"Error: {e}"

def save_emb_in_db(emb, metadata, id):
    try:
        collection.add(
            embeddings=emb,
            metadatas=metadata,
            ids=id
        )
        
        # Verify by querying
        result = collection.get(ids=id)
        if result and result['ids']:
            return True, "Success"
        else:
            return False, "Embedding not found after insertion"
    except Exception as e:
        return False, f"Error: {e}"

def save_text_emb_in_db(text_segments, video_url):
    try:
        texts = [seg["text"] for seg in text_segments]
        extract_text_emb_status, extract_text_emb, extract_text_emb_message = get_text_embbeding(texts)

        if not extract_text_emb_status:
            raise Exception(extract_text_emb_message)

        fail_emb_insert = 0
        final_message = ""

        for index, (tmp_obj, tmp_emb) in enumerate(zip(text_segments, extract_text_emb)):
    
            tmp_metadata = {
                "obj": 'text', 
                "text": tmp_obj["text"],
                "video_url": video_url,
                "start": tmp_obj["start"]
            }
            tmp_id = f"{video_url}_{index}_text"
            tmp_insert_status, tmp_insert_message = save_emb_in_db([tmp_emb.tolist()], tmp_metadata, tmp_id)
            if tmp_insert_status == False:
                fail_emb_insert += 1
                final_message = tmp_insert_message

        if fail_emb_insert > 0:
            raise Exception(final_message)

        return True, "Success"
    except Exception as e:
        return False, f"Error: {e}"

def save_img_emb_in_db(scenes_img_folder_path, scenes_csv_path, video_url):
    try:

        if not os.path.exists(scenes_img_folder_path):
            raise Exception("Scenes image folder is not found")
        
        if not os.path.exists(scenes_csv_path):
            raise Exception("Scenes metadata csv is not found")
        
        
        fail_emb_insert = 0
        final_message = ""
        
        df = pd.read_csv(scenes_csv_path)
        image_path_list = df["file_name"]
        image_path_list = [os.path.join(scenes_img_folder_path, tmp_file_name) for tmp_file_name in image_path_list]

        img_emb = get_image_embeddings_batch(image_path_list)

        for index, ((i,row), tmp_img_emb) in enumerate(zip(df.iterrows(), img_emb[1])):
            start_timestamp = row["timestamp_sec"]
            tmp_file_name = row["file_name"]
            tmp_image_path = os.path.join(scenes_img_folder_path, tmp_file_name)
            if not os.path.exists(tmp_image_path):
                fail_emb_insert += 1
                continue
            
            tmp_metadata = {
                "obj":"image", 
                "scene":  int(row["scene"]),
                "frame_id": int(row["frame_id"]),   
                "start": int(start_timestamp),
                "video_url": video_url,
            }
            tmp_id = f"{video_url}_{index}_image"
            tmp_insert_status, tmp_insert_message = save_emb_in_db(tmp_img_emb, tmp_metadata, tmp_id)
            if tmp_insert_status == False:
                fail_emb_insert += 1
                final_message = tmp_insert_message
        
        if fail_emb_insert > 0:
            final_message = f"fail emb insert > 0, {fail_emb_insert}"
            print("**********************")
            print(f"fail emb insert > 0, {fail_emb_insert}")
            print("**********************")

            # raise Exception(final_message)
        
        return True, "Success"
    except Exception as e:
        return False, f"Error: {e}"

