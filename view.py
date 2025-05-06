import os
from PIL import Image

# --- 配置 ---

input_folder = './img'

# 输出文件夹的基础路径
# 程序会在这个路径下创建 '2k' 和 '4k' 子文件夹来存放转换后的图片
# 默认设置为输入文件夹路径，你也可以指定其他路径
output_base_folder = input_folder

# 目标分辨率及其名称 (宽度, 高度)
# 注意：这里我们选择的是与 1920x1080 等比例缩放后最接近常用标准的 2K 和 4K 分辨率
# 2K: 2560x1440 (QHD), 2560 / 1920 = 1440 / 1080 = 1.333... (比例一致)
# 4K: 3840x2160 (UHD), 3840 / 1920 = 2160 / 1080 = 2.0 (比例一致)
target_resolutions = {
    '2k': (2560, 1440),
    '4k': (3840, 2160),
}

# 预期的原始图片分辨率 (可选，如果只想处理特定尺寸的图片)
expected_original_resolution = (1920, 1080)

# 缩放时使用的重采样滤镜 (高质量)
# Image.Resampling.LANCZOS 适用于 Pillow 9.1.0 或更高版本
# 如果你的 Pillow 版本较旧，可能需要使用 Image.LANCZOS
# LANCZOS 通常用于放大图片时保持细节
resampling_filter = Image.Resampling.LANCZOS


# --- 脚本逻辑 ---
def resize_image(image_path, target_size, target_name, base_name, output_folder):
    """
    打开、缩放并保存图片到指定分辨率。
    """
    try:
        img = Image.open(image_path)

        # 可选：检查图片尺寸是否符合预期
        # if img.size != expected_original_resolution:
        #     print(f"  跳过：图片 {os.path.basename(image_path)} 尺寸为 {img.size}，而非 {expected_original_resolution}")
        #     img.close()
        #     return

        # 确保图片是 RGBA 模式以保留透明通道，即使原始图片模式不是
        if img.mode != 'RGBA':
             img = img.convert('RGBA')

        print(f"  -> 正在缩放至 {target_size[0]}x{target_size[1]} ({target_name})...")

        # 缩放图片
        # 因为目标分辨率与原始分辨率是等比例的，直接使用 resize 即可
        # 如果比例不等，则需要先计算保持比例的新尺寸
        resized_img = img.resize(target_size, resampling_filter)

        # 创建输出文件夹 (如果不存在)
        os.makedirs(output_folder, exist_ok=True)

        # 构建输出文件名和路径
        output_filename = f"{base_name}_{target_name}.png"
        output_file_path = os.path.join(output_folder, output_filename)

        # 保存为 PNG 格式以保留透明信息
        resized_img.save(output_file_path, format='PNG')
        print(f"  已保存：{output_file_path}")

        img.close() # 关闭图片文件

    except FileNotFoundError:
        print(f"  错误：文件未找到 {image_path}")
    except PermissionError:
         print(f"  错误：无权限访问 {image_path}")
    except Exception as e:
        print(f"  处理图片 {os.path.basename(image_path)} 时发生错误：{e}")


# --- 主程序流程 ---
if not os.path.isdir(input_folder):
    print(f"错误：输入文件夹 '{input_folder}' 不存在或不是一个文件夹。请检查路径配置。")
else:
    print(f"正在处理文件夹中的图片：{input_folder}")
    processed_count = 0

    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)

        # 只处理文件且是 PNG 格式
        if os.path.isfile(file_path) and filename.lower().endswith('.png'):
            print(f"\n处理文件：{filename}")

            # 获取文件名 (不含扩展名)
            base_name, ext = os.path.splitext(filename)

            # 逐个目标分辨率进行处理
            for res_name, (width, height) in target_resolutions.items():
                output_folder_path = os.path.join(output_base_folder, res_name)
                resize_image(file_path, (width, height), res_name, base_name, output_folder_path)

            processed_count += 1
        elif os.path.isfile(file_path):
             print(f"\n跳过文件：{filename} (非 PNG 格式)")
        # else: 跳过文件夹或其它文件类型

    print("\n处理完成。")
    print(f"共处理了 {processed_count} 个 PNG 文件。")
    if processed_count > 0:
        print(f"转换后的图片保存在 '{output_base_folder}' 文件夹下的 '2k' 和 '4k' 子文件夹中。")