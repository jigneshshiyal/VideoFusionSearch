import clip
import torch
from PIL import Image
import numpy as np
from tqdm import tqdm

device = "cuda" if torch.cuda.is_available() else "cpu"

model, preprocess = clip.load("ViT-B/32", device=device)

def get_text_embbeding(texts):
    try:
        text_tokens = clip.tokenize(texts).to(device)
        with torch.no_grad():
            text_embeddings = model.encode_text(text_tokens)
            text_embeddings = text_embeddings / text_embeddings.norm(dim=-1, keepdim=True)

        return True, text_embeddings, "Success"
    except Exception as e:
        return False, None, f"Error: {e}"


def get_image_embeddings_batch(image_paths, batch_size=32):
    try:
        all_embeddings = []
        for i in tqdm(range(0, len(image_paths), batch_size), desc="Extracting CLIP embeddings"):
            batch_paths = image_paths[i:i+batch_size]
            batch_images = [preprocess(Image.open(p).convert("RGB")) for p in batch_paths]
            batch_tensor = torch.stack(batch_images).to(device)
            with torch.no_grad():
                batch_features = model.encode_image(batch_tensor).cpu().numpy()
            all_embeddings.extend(batch_features)

        return True, all_embeddings, "Success"
    except Exception as e:
        return False, None, f"Error: {e}"
