import clip
import torch
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def get_image_features(image_path):
    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
    with torch.no_grad():
        return model.encode_image(image)

def get_text_features(texts):
    tokens = clip.tokenize(texts).to(device)
    with torch.no_grad():
        return model.encode_text(tokens)

def compare_image_to_text(image_path, texts):
    image_features = get_image_features(image_path)
    text_features = get_text_features(texts)
    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)
    similarities = (image_features @ text_features.T).squeeze(0)
    best_index = similarities.argmax().item()
    return texts[best_index], similarities[best_index].item()