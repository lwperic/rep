from PIL import Image, ImageDraw, ImageFont
import os

# 创建一个白色背景的图片
img = Image.new('RGB', (400, 300), color='white')
d = ImageDraw.Draw(img)

# 添加文字
d.text((150, 150), "Placeholder Image", fill='black')

# 保存图片
img.save('placeholder.png')