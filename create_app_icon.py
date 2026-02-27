from PIL import Image, ImageDraw

def create_icon():
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    
    for size in sizes:
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        margin = size[0] // 8
        rect_coords = [margin, margin, size[0] - margin, size[1] - margin]
        
        draw.rectangle(rect_coords, outline=(0, 168, 255, 255), width=max(1, size[0] // 16))
        
        center = size[0] // 2
        line_len = size[0] // 4
        draw.line([(center - line_len, center - line_len), (center + line_len, center + line_len)], 
                  fill=(0, 168, 255, 255), width=max(1, size[0] // 16))
        draw.line([(center + line_len, center - line_len), (center - line_len, center + line_len)], 
                  fill=(0, 168, 255, 255), width=max(1, size[0] // 16))
        
        images.append(img)
    
    images[0].save('app-icon.ico', format='ICO', sizes=sizes)
    print('Icon created: app-icon.ico')

if __name__ == '__main__':
    create_icon()
