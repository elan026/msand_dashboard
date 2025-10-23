import cv2
import numpy as np
from sklearn.cluster import KMeans
import os, uuid

def save_image_file(file_storage, upload_folder):
    filename = f"{uuid.uuid4().hex}.jpg"
    path = os.path.join(upload_folder, filename)
    img_bytes = file_storage.read()
    with open(path, "wb") as f:
        f.write(img_bytes)
    file_storage.seek(0)
    return path

def kmeans_color_quantization(image, k=4):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    data = img.reshape((-1,3)).astype(np.float32)
    kmeans = KMeans(n_clusters=k, random_state=42).fit(data)
    centers = np.uint8(kmeans.cluster_centers_)
    labels = kmeans.labels_
    quant = centers[labels].reshape(img.shape)
    quant_bgr = cv2.cvtColor(quant, cv2.COLOR_RGB2BGR)
    return quant_bgr, centers, labels.reshape(img.shape[:2])

def contour_particle_features(gray_img):
    blurred = cv2.GaussianBlur(gray_img, (5,5), 0)
    _, th = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    areas = [cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 5]
    if not areas:
        return {"count": 0, "avg_area": 0.0, "median_area": 0.0}
    import numpy as np
    return {"count": len(areas), "avg_area": float(np.mean(areas)), "median_area": float(np.median(areas))}

def analyze_image(path, upload_folder):
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    resized = cv2.resize(img, (512,512))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    quant, centers, labels = kmeans_color_quantization(resized, k=3)
    centers_mean_brightness = np.mean(centers, axis=1)
    dominant_cluster = np.argmax(np.bincount(labels.flatten()))
    brightness = centers_mean_brightness[dominant_cluster] / 255.0
    features = contour_particle_features(gray)
    area_score = np.tanh(features['avg_area'] / 100.0)
    vision_conf = 0.6 * brightness + 0.4 * area_score
    vision_conf = float(np.clip(vision_conf, 0.0, 1.0))
    preview_name = f"seg_{os.path.basename(path)}"
    preview_path = os.path.join(upload_folder, preview_name)
    cv2.imwrite(preview_path, quant)
    return {
        "vision_conf": vision_conf,
        "features": features,
        "segmented_path": preview_path
    }