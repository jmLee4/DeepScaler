import matplotlib.pyplot as plt

# 读取文件内容
file_path = './sendFlow/random-100max.req'
with open(file_path, 'r') as file:
    data = file.readlines()

# 将数据转换为整数列表
data = [int(line.strip()) for line in data]

# 设置字体
plt.rcParams['font.family'] = 'DejaVu Serif'

# 绘制折线图
plt.figure(figsize=(5, 2.5))  # 缩小图像尺寸
plt.plot(data, linestyle='-', linewidth=1)
plt.title('Data Distribution from random-100max.req', fontsize=14)
plt.xlabel('Index', fontsize=12)
plt.ylabel('Value', fontsize=12)
plt.grid(True)
plt.savefig("./sendFlow/data_distribute.png", dpi=300)
plt.show()