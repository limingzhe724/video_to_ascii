import cv2
import numpy as np
import argparse
import os
from PIL import Image, ImageDraw, ImageFont
import tempfile
import shutil

# 标准字符集和更密集的字符集
ASCII_CHARS = ['@', '#', 'S', '%', '?', '*', '+', ';', ':', ',', '.', ' ']
ASCII_CHARS_DENSE = ['$', '@', 'B', '%', '8', '&', 'W', 'M', '#', '*', 'o', 'a', 'h', 'k', 'b', 'd', 'p', 'q', 'w', 'm', 'Z', 'O', '0', 'Q', 'L', 'C', 'J', 'U', 'Y', 'X', 'z', 'c', 'v', 'u', 'n', 'x', 'r', 'j', 'f', 't', '/', '\\', '|', '(', ')', '1', '{', '}', '[', ']', '?', '-', '_', '+', '~', '<', '>', 'i', '!', 'l', 'I', ';', ':', ',', '"', '^', '`', '.', ' ']

def resize_frame(frame, new_width=100):
    """调整帧的大小"""
    height, width = frame.shape[:2]
    ratio = height / width / 2  # 除以2是因为字符在终端中通常是高大于宽
    new_height = int(new_width * ratio)
    resized_frame = cv2.resize(frame, (new_width, new_height))
    return resized_frame

def enhance_contrast(frame, alpha=1.5, beta=0):
    """增强图像对比度"""
    return cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

def grayify(frame, enhance=True, contrast=1.5):
    """将帧转换为灰度图，并可选择增强对比度"""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if enhance:
        return enhance_contrast(gray_frame, alpha=contrast)
    return gray_frame

def pixels_to_ascii(frame, char_set=ASCII_CHARS):
    """将像素转换为ASCII字符"""
    pixels = frame.flatten()
    ascii_str = ''
    for pixel_value in pixels:
        # 根据像素值选择对应的ASCII字符
        ascii_str += char_set[pixel_value * len(char_set) // 256]
    # 将字符串按帧高度分割成多行
    img_width = frame.shape[1]
    ascii_str_len = len(ascii_str)
    ascii_img = ''
    for i in range(0, ascii_str_len, img_width):
        ascii_img += ascii_str[i:i+img_width] + '\n'
    return ascii_img

def pixels_to_color_ascii(frame, char_set=ASCII_CHARS):
    """将像素转换为带颜色的ASCII字符"""
    pixels = frame.reshape(-1, 3)  # BGR格式
    ascii_str = ''
    for b, g, r in pixels:
        # 根据亮度选择字符
        brightness = int(0.299 * r + 0.587 * g + 0.114 * b)
        char = char_set[brightness * len(char_set) // 256]
        # 添加ANSI颜色代码
        color_code = f"\033[38;2;{r};{g};{b}m"
        ascii_str += f"{color_code}{char}\033[0m"  # 重置颜色
    
    img_width = frame.shape[1]
    ascii_str_len = len(ascii_str)
    ascii_img = ''
    for i in range(0, ascii_str_len, img_width * 5):  # 乘以5是因为每个字符包含颜色代码
        ascii_img += ascii_str[i:i+img_width*5] + '\n'
    return ascii_img

def convert_to_ascii_video(input_path, output_path=None, width=100, fps=None, font_size=12, char_spacing=1.2, contrast=1.5):
    """将视频转换为ASCII字符视频"""
    # 打开视频文件
    cap = cv2.VideoCapture(input_path)
    
    # 获取视频的原始帧率
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    # 如果未指定输出帧率，则使用原始帧率
    if fps is None:
        fps = original_fps
    
    # 获取视频的总帧数
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 创建临时目录来存储ASCII帧图像
    temp_dir = tempfile.mkdtemp()
    
    # 计算处理进度
    frame_count = 0
    
    try:
        # 逐帧处理视频
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 显示处理进度
            frame_count += 1
            progress = frame_count / total_frames * 100
            print(f"\r处理进度: {progress:.2f}% ({frame_count}/{total_frames})", end='')
            
            # 调整帧大小
            resized_frame = resize_frame(frame, width)
            
            # 转换为灰度图并增强对比度
            gray_frame = grayify(resized_frame, contrast=contrast)
            
            # 转换为ASCII字符
            ascii_img = pixels_to_ascii(gray_frame, ASCII_CHARS_DENSE)
            
            # 创建图像以保存ASCII字符
            img_height = len(ascii_img.split('\n'))
            img_width = width
            char_width = int(font_size * char_spacing)  # 考虑字符间距
            
            # 创建一个白色背景的图像
            image = Image.new('RGB', (img_width * char_width, img_height * font_size), color='white')
            draw = ImageDraw.Draw(image)
            
            # 尝试加载支持中文的字体
            font = None
            try:
                font = ImageFont.truetype("simhei.ttf", font_size)
            except IOError:
                try:
                    font = ImageFont.truetype("Arial Unicode.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()
            
            # 在图像上绘制ASCII字符
            draw.text((0, 0), ascii_img, fill='black', font=font)
            
            # 保存帧图像
            frame_path = os.path.join(temp_dir, f"frame_{frame_count:05d}.png")
            image.save(frame_path)
        
        print("\n视频处理完成，正在生成输出视频...")
        
        if output_path:
            # 获取第一帧图像以确定输出视频的尺寸
            first_frame_path = os.path.join(temp_dir, "frame_00001.png")
            first_frame = Image.open(first_frame_path)
            frame_width, frame_height = first_frame.size
            
            # 创建视频写入对象
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
            
            # 读取所有帧并写入视频
            for i in range(1, frame_count + 1):
                frame_path = os.path.join(temp_dir, f"frame_{i:05d}.png")
                frame = cv2.imread(frame_path)
                out.write(frame)
            
            # 释放视频写入对象
            out.release()
            print(f"ASCII视频已保存到: {output_path}")
        else:
            print("未指定输出路径，已将ASCII帧保存到临时目录")
    
    finally:
        # 释放视频捕获对象
        cap.release()
        # 删除临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

def play_ascii_video(input_path, width=100, use_color=True, char_set=ASCII_CHARS_DENSE, contrast=1.5):
    """在命令行中播放ASCII字符视频"""
    # 打开视频文件
    cap = cv2.VideoCapture(input_path)
    
    # 获取视频的原始帧率
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # 计算每一帧应该显示的毫秒数
    frame_delay = int(1000 / fps)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 调整帧大小
            resized_frame = resize_frame(frame, width)
            
            if use_color:
                # 彩色模式下不进行灰度转换
                enhanced_frame = enhance_contrast(resized_frame, alpha=contrast)
                ascii_img = pixels_to_color_ascii(enhanced_frame, char_set)
            else:
                # 非彩色模式下进行灰度转换和对比度增强
                gray_frame = grayify(resized_frame, contrast=contrast)
                ascii_img = pixels_to_ascii(gray_frame, char_set)
            
            # 清屏
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 显示ASCII图像
            print(ascii_img)
            
            # 控制帧率
            cv2.waitKey(frame_delay)
    
    finally:
        # 释放视频捕获对象
        cap.release()

def main():
    """主函数，处理命令行参数并执行相应操作"""
    parser = argparse.ArgumentParser(description='视频转ASCII字符命令行工具')
    parser.add_argument('-i', '--input', required=True, help='输入视频文件路径')
    parser.add_argument('-o', '--output', help='输出视频文件路径，不指定则直接在命令行播放')
    parser.add_argument('-w', '--width', type=int, default=100, help='输出的ASCII字符画宽度，默认100')
    parser.add_argument('--fps', type=float, help='输出视频的帧率，不指定则使用原视频帧率')
    parser.add_argument('--color', action='store_true', help='启用彩色输出（仅命令行播放有效）')
    parser.add_argument('--dense', action='store_true', help='使用更密集的字符集')
    parser.add_argument('--font-size', type=int, default=12, help='输出视频中的字体大小')
    parser.add_argument('--char-spacing', type=float, default=1.2, help='字符间距系数')
    parser.add_argument('--contrast', type=float, default=1.5, help='对比度增强系数')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件 '{args.input}' 不存在")
        return
    
    # 根据参数选择字符集
    char_set = ASCII_CHARS_DENSE if args.dense else ASCII_CHARS
    
    if args.output:
        # 转换为ASCII视频并保存
        convert_to_ascii_video(
            args.input, 
            args.output, 
            args.width, 
            args.fps,
            args.font_size,
            args.char_spacing,
            args.contrast
        )
    else:
        # 直接在命令行播放ASCII视频
        play_ascii_video(
            args.input, 
            args.width, 
            args.color,
            char_set,
            args.contrast
        )

if __name__ == "__main__":
    main()    