import matplotlib.pyplot as plt
import os

def draw_data_distribution(file_path, output_dir):
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
    output_path = os.path.join(output_dir, os.path.splitext(os.path.basename(file_path))[0] + '_draw.png')
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"图片已保存至: {output_path}")

if __name__ == "__main__":
    data_dir = './data/train'
    output_dir = './data/train_distribute'

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        if os.path.isfile(file_path):
            draw_data_distribution(file_path, output_dir)