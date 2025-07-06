from chromadb_functions import get_text_embbeding, collection, client, get_image_embeddings_batch


def multimodel_search(query, video_url, n_results, search_query_type=["text", "image"], output_from=["text", "image", "both"]):
    try:
        if search_query_type == "text":
            tmp_emb_status, tmp_text_emb, tmp_message = get_text_embbeding(query)
            tmp_text_emb = tmp_text_emb.tolist()
        elif search_query_type == "image":
            tmp_emb_status, tmp_text_emb, tmp_message = get_image_embeddings_batch([query])
        else:
            raise Exception("Unrecognize search query type")

        if tmp_emb_status == False:
            raise Exception("Error in generate text embedding")
        if not client:
            raise Exception("Error in establish connection with database")
        
        if output_from == "both":
            query_result = collection.query(
                query_embeddings=tmp_text_emb,
                n_results=n_results,
                where={"obj": "text"},
            )
        elif output_from == "text" or output_from == "image":
            query_result = collection.query(
                query_embeddings=tmp_text_emb,
                n_results=n_results,
                where={
                    "$and": [
                        {"obj": output_from},
                        {"video_url": video_url},
                    ]
                }
            )

        return True, query_result, "Success"
    except Exception as e:
        return False, None, f"Error: {e}"