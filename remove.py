import cv2
from rembg import remove
from PIL import Image
import numpy as np

input_video = "102.mp4"
output_video = "1012.mp4"
background_image = "bg2.jpg"

cap = cv2.VideoCapture(input_video)
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

out = cv2.VideoWriter(output_video, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
bg_img = Image.open(background_image).resize((width, height))

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # OpenCV → PIL (RGB)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(frame_rgb)

    # 배경 제거
    fg_removed = remove(pil_img)

    # 합성
    fg = Image.alpha_composite(bg_img.convert("RGBA"), fg_removed.convert("RGBA"))

    # PIL → OpenCV (BGR)
    result = cv2.cvtColor(np.array(fg), cv2.COLOR_RGBA2BGR)
    out.write(result)

cap.release()
out.release()
