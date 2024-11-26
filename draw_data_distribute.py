import matplotlib.pyplot as plt
import os
import sys

def draw_data_distribution(file_path):
    # 读取文件内容
    with open(file_path, 'r') as file:
        data = file.readlines()

    # 将数据转换为浮点数列表
    data = [float(line.strip()) for line in data]

    # 设置字体
    plt.rcParams['font.family'] = 'DejaVu Serif'

    # 绘制折线图
    plt.figure(figsize=(5, 2.5))  # 缩小图像尺寸
    plt.plot(data, linestyle='-', linewidth=1)
    plt.title('Data Distribution', fontsize=14)
    plt.xlabel('Index', fontsize=12)
    plt.ylabel('Value', fontsize=12)
    plt.grid(True)

    # 保存图片
    output_path = os.path.splitext(file_path)[0] + '_draw.png'
    plt.savefig(output_path, dpi=300)
    print(f"图片已保存至: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python draw_data_distribute.py <文件路径>")
    else:
        draw_data_distribution(sys.argv[1])