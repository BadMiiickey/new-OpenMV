import os
from PIL import Image, ImageEnhance

def adjust_brightness_batch(input_folder, output_folder, factor):
    """
    批量调整指定文件夹内所有图片的亮度。

    :param input_folder: 包含原始图片的文件夹路径。
    :param output_folder: 保存调整后图片的文件夹路径。
    :param factor: 亮度调整因子。
                   1.0 表示原始亮度。
                   < 1.0 表示降低亮度 (例如 0.6 表示降低40%)。
                   > 1.0 表示增加亮度。
                   0.0 表示纯黑色。
    """
    # 确保输出文件夹存在，如果不存在则创建
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"创建输出文件夹: {output_folder}")

    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_folder):
        # 构造完整的文件路径
        input_path = os.path.join(input_folder, filename)

        # 检查文件是否是图片
        if not (filename.lower().endswith('.png') or filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg')):
            print(f"跳过非图片文件: {filename}")
            continue

        try:
            # 打开图片
            with Image.open(input_path) as img:
                # 创建亮度增强器
                enhancer = ImageEnhance.Brightness(img)
                
                # 应用亮度调整
                img_adjusted = enhancer.enhance(factor)
                
                # 构造输出文件路径
                output_path = os.path.join(output_folder, filename)
                
                # 保存调整后的图片
                img_adjusted.save(output_path)
                print(f"已处理并保存: {filename} -> {output_path}")

        except Exception as e:
            print(f"处理文件 {filename} 时出错: {e}")

# --- 主程序入口 ---
if __name__ == "__main__":
    # --- 请修改以下参数 ---
    
    # 1. 原始图片所在的文件夹
    INPUT_DIRECTORY = "C:\\Users\\28974\\Desktop\\image\\0908\\yellow0908"

    # 2. 调整后图片要保存的文件夹
    OUTPUT_DIRECTORY = "C:\\Users\\28974\\Desktop\\image\\0908\\yellow0908"

    # 3. 亮度调整因子
    BRIGHTNESS_FACTOR = 1.4

    # --- 执行批量处理 ---
    print("开始批量调整图片亮度...")
    adjust_brightness_batch(INPUT_DIRECTORY, OUTPUT_DIRECTORY, BRIGHTNESS_FACTOR)
    print("处理完成！")