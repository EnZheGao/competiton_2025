import cv2
import numpy as np
import torch
from PIL import Image

# 加载YOLOv5模型（首次运行会自动下载）
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
model.classes = [0]  # 只检测人体（类别0）

def guide_filter(I, p, r=15, eps=1e-3):
    """
    导向滤波实现
    :param I: 导向图像（灰度图像）
    :param p: 输入图像（灰度图像）
    :param r: 滤波半径
    :param eps: 正则化参数
    :return: 滤波后的图像
    """
    # 计算均值
    mean_I = cv2.boxFilter(I, cv2.CV_64F, (r, r))
    mean_p = cv2.boxFilter(p, cv2.CV_64F, (r, r))
    mean_Ip = cv2.boxFilter(I * p, cv2.CV_64F, (r, r))
    cov_Ip = mean_Ip - mean_I * mean_p

    mean_II = cv2.boxFilter(I * I, cv2.CV_64F, (r, r))
    var_I = mean_II - mean_I * mean_I

    # 计算a和b
    a = cov_Ip / (var_I + eps)
    b = mean_p - a * mean_I

    # 对a和b进行均值滤波
    mean_a = cv2.boxFilter(a, cv2.CV_64F, (r, r))
    mean_b = cv2.boxFilter(b, cv2.CV_64F, (r, r))

    # 输出图像
    q = mean_a * I + mean_b
    return q

def remove_fog(frame, window_size=15, omega=0.85, r=60, eps=1e-3):
    """
    去烟算法（基于导向滤波）
    :param frame: 输入灰度图像
    :param window_size: 窗口大小
    :param omega: 去雾强度参数
    :param r: 导向滤波半径
    :param eps: 导向滤波正则化参数
    :return: 去烟后的灰度图像
    """
    # 计算暗通道
    min_channel = cv2.erode(frame, np.ones((window_size, window_size)))
    dark_channel = cv2.minMaxLoc(min_channel)[1]

    # 估计大气光
    atmospheric_light = np.percentile(frame, 99)

    # 计算透射率
    transmission = 1 - omega * (frame / atmospheric_light)
    transmission = np.clip(transmission, 0.1, 0.9)

    # 使用导向滤波优化透射率
    refined_transmission = guide_filter(frame, transmission, r, eps)

    # 去烟处理
    defogged = (frame - atmospheric_light) / np.maximum(refined_transmission, 0.1) + atmospheric_light
    defogged = np.clip(defogged, 0, 255).astype(np.uint8)

    return defogged

def detect_humans(frame, model):
    """
    使用YOLOv5检测人体并绘制边界框
    :param frame: 输入图像（BGR格式）
    :param model: YOLOv5模型
    :return: 绘制检测框后的图像
    """
    # 转换颜色空间 BGR -> RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 转换为PIL格式并进行推理
    results = model(Image.fromarray(rgb_frame))

    # 解析检测结果
    boxes = results.xyxy[0].cpu().numpy()

    # 绘制检测框
    for box in boxes:
        if box[5] == 0:  # 确保是人体类别
            x1, y1, x2, y2 = map(int, box[:4])
            conf = box[4]
            # 绘制矩形和置信度
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f'Person: {conf:.2f}'
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return frame

def process_video(input_path, output_path):
    """
    处理视频：去烟 + 人体检测
    :param input_path: 输入视频路径
    :param output_path: 输出视频路径
    """
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 视频编码参数优化
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 红外图像通常是单通道的，直接使用灰度图像
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 去烟处理
        defogged = remove_fog(gray_frame)

        # 检查 defogged 是否为空
        if defogged is None or defogged.size == 0:
            continue

        # 将去烟后的灰度图像转换为BGR格式用于检测
        bgr_frame = cv2.cvtColor(defogged, cv2.COLOR_GRAY2BGR)

        # 人体检测与标注
        detected_frame = detect_humans(bgr_frame, model)

        # 写入处理后的帧
        out.write(detected_frame)

    cap.release()
    out.release()

if __name__ == "__main__":
    input_video = "../无锡低温烟雾环境双光视频/output_rgb_smoked1.mp4"
    output_video = "output_detected.mp4"

    # 启用GPU加速（如果可用）
    if torch.cuda.is_available():
        model = model.cuda()

    process_video(input_video, output_video)