from fastapi import FastAPI, HTTPException, UploadFile, Form, File
from typing import Optional, Literal
import uvicorn
import os
import uuid
import shutil
import tempfile
import requests

from video_fusion_search import video_audio_fusion_search, convert_seconds_to_time_str
from backend.search_functions import multimodel_search

app = FastAPI()

@app.post("/embed")
def embed_video(url: str = Form(...)):
    status, msg = video_audio_fusion_search(url)
    if not status:
        raise HTTPException(status_code=500, detail=msg)
    return {"status": "success", "message": msg}


@app.post("/search")
def search_video(
    video_url: str = Form(...),
    n_results: int = Form(5),
    search_query_type: Literal["text", "image"] = Form(...),
    output_from: Literal["text", "image", "both"] = Form(...),
    query: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    image_file: Optional[UploadFile] = File(None)
):
    image_path = None

    try:
        # --------- Text Query ---------
        if search_query_type == "text":
            if not query:
                raise HTTPException(status_code=400, detail="Text query not provided.")

            status, query_result, msg = multimodel_search(
                query=query,
                video_url=video_url,
                n_results=n_results,
                search_query_type="text",
                output_from=output_from
            )

        # --------- Image Query ---------
        elif search_query_type == "image":
            tmp_dir = tempfile.gettempdir()
            tmp_filename = f"tmp_{uuid.uuid4().hex}.jpg"
            image_path = os.path.join(tmp_dir, tmp_filename)

            if image_file:
                with open(image_path, "wb") as buffer:
                    shutil.copyfileobj(image_file.file, buffer)

            elif image_url:
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    with open(image_path, "wb") as out_file:
                        shutil.copyfileobj(response.raw, out_file)
                else:
                    raise HTTPException(status_code=400, detail="Image download failed.")
            else:
                raise HTTPException(status_code=400, detail="Provide either image_file or image_url for image search.")

            # Call multimodel search using the image path
            status, query_result, msg = multimodel_search(
                query=image_path,
                video_url=video_url,
                n_results=n_results,
                search_query_type="image",
                output_from=output_from
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid search_query_type")

        # --------- Handle result ---------
        if not status:
            raise HTTPException(status_code=500, detail=msg)

        timestamps = []
        for tmp in query_result["metadatas"][0]:
            start_time = tmp["start"]
            tmp_timestamp = convert_seconds_to_time_str(start_time)
            timestamps.append(tmp_timestamp)

        return {"status": "success", "results": timestamps}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


if __name__ == "__main__":
    uvicorn.run(app=app, port=8000)
