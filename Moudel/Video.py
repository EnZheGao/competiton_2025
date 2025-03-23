import torch
import cv2
import numpy as np
import torch.nn.functional as F
from concurrent.futures import ThreadPoolExecutor



def normalize_image(img):
    img_min = img.min()
    img_max = img.max()
    return (img - img_min) / (img_max - img_min + 1e-6)

def to_uint8(img):
    img = np.clip(img * 255, 0, 255).astype(np.uint8)
    return img


def get_atmospheric_light(I_avg, I_max, A_scale=1.0):
    A = A_scale * (I_avg + I_max) / 2
    return A

def estimate_transmission(I, A, rho=0.9):
    I_avg = I.mean().item()
    delta = min(rho * I_avg, 0.75)
    t = 1 - delta * (I / A)
    t = torch.clamp(t, 0.2, 1.0)
    return t

def recover_scene_radiance(I, A, t):
    L = A * (1 - t)
    J = (I - L) / (t + 1e-6)
    J = torch.clamp(J, 0.0, 1.0)
    return J

def gaussian_kernel(size, sigma):
    ax = torch.arange(-size // 2 + 1., size // 2 + 1.)
    xx, yy = torch.meshgrid([ax, ax], indexing='ij')
    kernel = torch.exp(-(xx ** 2 + yy ** 2) / (2. * sigma ** 2))
    kernel = kernel / torch.sum(kernel)
    return kernel

def single_scale_retinex(I, sigma=15):
    kernel_size = int(6 * sigma + 1)
    kernel = gaussian_kernel(kernel_size, sigma).unsqueeze(0).unsqueeze(0).to(I.device)
    I_log = torch.log1p(I)
    blurred = F.conv2d(I.unsqueeze(0).unsqueeze(0), kernel, padding=kernel_size // 2)
    blurred_log = torch.log1p(blurred)
    return (I_log - blurred_log).squeeze()

def multi_scale_retinex(I, scales=[15, 80], gain=1.5):
    weights = [1 / len(scales)] * len(scales)
    retinex = torch.zeros_like(I)
    for w, sigma in zip(weights, scales):
        retinex += w * single_scale_retinex(I, sigma)
    retinex = gain * retinex
    return normalize_image(retinex)

def enhance_image(img, gamma=1.2, clahe_clip=2.0):
    img = np.power(img, gamma)
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=(8, 8))
    img_uint8 = to_uint8(normalize_image(img))
    return clahe.apply(img_uint8).astype(np.float32) / 255.0


def process_frame(img, rho=0.9, A_scale=1.0, gain=1.5, gamma=1.2):
    img_tensor = torch.tensor(img).to(torch.float32).cuda()
    I_avg = img_tensor.mean().item()
    I_max = img_tensor.max().item()
    A = get_atmospheric_light(I_avg, I_max, A_scale=A_scale)
    t = estimate_transmission(img_tensor, A, rho=rho)
    J = recover_scene_radiance(img_tensor, A, t)
    retinex_img = multi_scale_retinex(J, gain=gain)
    enhanced_img = enhance_image(retinex_img.cpu().numpy(), gamma=gamma)
    return enhanced_img


def process_video(input_path, output_path, rho=0.95, A_scale=1.2, gain=1.8, gamma=1.2, device='cuda'):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height), isColor=False)

    frame_count = 0
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if len(frame.shape) == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            img = frame.astype(np.float32) / 255.0

            futures.append(executor.submit(process_frame, img, rho, A_scale, gain, gamma))

            if len(futures) >= 4:
                for future in futures:
                    enhanced_img = future.result()
                    final_frame = to_uint8(enhanced_img)
                    out.write(final_frame)
                futures = []

            frame_count += 1
            if frame_count % 50 == 0:
                print(f"Processed {frame_count} frames...")

        for future in futures:
            enhanced_img = future.result()
            final_frame = to_uint8(enhanced_img)
            out.write(final_frame)

    cap.release()
    out.release()
    print(f"Processing completed. Saved to {output_path}")


if __name__ == "__main__":
    input_video = "output_rgb_smoked2.mp4"
    output_video = "output_video.mp4"

    process_video(
        input_path=input_video,
        output_path=output_video,
        rho=0.95,
        A_scale=1.2,
        gain=1.8,
        gamma=1.2
    )
