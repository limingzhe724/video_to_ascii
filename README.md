这个程序可以将视频转换为 ASCII 字符画，并支持两种输出模式：
直接在命令行中播放 ASCII 字符视频
将 ASCII 字符视频保存为新的视频文件
使用方法：
安装必要的依赖库：pip install opencv-python pillow numpy
直接在命令行播放视频：python video_to_ascii.py -i input_video.mp4
保存为视频文件：python video_to_ascii.py -i input_video.mp4 -o output_ascii_video.mp4
你可以通过-w参数调整输出的宽度，通过--fps参数调整输出视频的帧率。程序会自动尝试使用支持中文的字体，确保字符显示正常。
