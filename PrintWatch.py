import requests
from bs4 import BeautifulSoup
import re
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 从IP.txt文件读取楼层、设备编号和URL
def read_data_from_file(filename='IP.txt'):
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            print(f"从{filename}读取了{len(lines)}行数据")
            
            for line in lines:
                line = line.strip()
                if not line:  # 跳过空行
                    continue
                    
                print(f"处理行: {line}")
                # 尝试按制表符分割
                parts = line.split('\t')
                # 如果分割后的部分少于3个，尝试按空格分割
                if len(parts) < 3:
                    parts = line.split()
                
                if len(parts) >= 3:
                    floor = parts[0].strip()
                    device_id = parts[1].strip()
                    url = parts[2].strip()
                    print(f"  解析结果: 楼层={floor}, 设备编号={device_id}, URL={url}")
                    
                    # 确保URL以/结尾
                    if not url.endswith('/'):
                        url += '/'
                    # 提取IP地址
                    ip_match = re.search(r'https?://([^/]+)', url)
                    ip_address = ip_match.group(1) if ip_match else url
                    data.append({
                        'floor': floor,
                        'device_id': device_id,
                        'url': url,
                        'ip_address': ip_address
                    })
                else:
                    print(f"  警告: 行格式不正确: {line}")
        
        print(f"成功从{filename}读取了{len(data)}条数据")
        for i, item in enumerate(data):
            print(f"  数据{i+1}: 楼层={item['floor']}, 设备编号={item['device_id']}, URL={item['url']}, IP={item['ip_address']}")
        return data
    except Exception as e:
        print(f"Error reading data from file: {e}")
        return []

# 读取数据
device_data = read_data_from_file()

# 提取URL列表
urls = [item['url'] for item in device_data]

# 如果没有从文件读取到URL，使用硬编码的URL列表作为备份
if not urls:
    print("未从IP.txt读取到URL，使用失败")
 

# 存储爬取结果
results = []

# 遍历每个URL并爬取内容
for url in urls:
    try:
        print(f"正在爬取: {url}")
        # 发送HTTP请求，忽略SSL证书验证
        response = requests.get(url, verify=False, timeout=5)
        response.raise_for_status()  # 检查请求是否成功

        # 解析HTML内容
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找所有class为'consumable'的div标签
        consumables = soup.find_all('div', class_='consumable')
        # 查找class为'product'的strong标签
        product = soup.find('strong', class_='product')

        if consumables:
            print(f"  找到 {len(consumables)} 个耗材信息")
        else:
            print(f"  未找到耗材信息")

        if product:
            print(f"  找到产品信息: {product.text.strip()}")
        else:
            print(f"  未找到产品信息")

        # 处理耗材信息，检查是否包含"10%"
        processed_consumables = []
        for c in consumables:
            consumable_text = c.text.strip()
            # 检查是否包含"10%"
            if "10%" in consumable_text:
                processed_consumables.append({"text": consumable_text, "has_low_toner": True})
            else:
                processed_consumables.append({"text": consumable_text, "has_low_toner": False})
        
        # 将结果存入列表
        results.append({
            "url": url,
            "consumables": processed_consumables,
            "product": product.text.strip() if product else "Product not found"
        })

    except requests.exceptions.RequestException as e:
        print(f"Error occurred while fetching {url}: {e}")
        # 添加空结果，以保持与device_data的索引对应
        results.append({
            "url": url,
            "consumables": [],
            "product": "Error: Connection failed"
        })

# 生成HTML文件
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HP打印机碳粉情况</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            color: #333;
            margin: 0;
            padding: 20px;
        }
        h1 {
            text-align: center;
            color: #555;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #007BFF;
            color: white;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
        .consumable-list {
            list-style-type: none;
            padding: 0;
        }
        .consumable-list li {
            margin: 5px 0;
            padding: 5px;
            background-color: #e9ecef;
            border-radius: 4px;
        }
        .low-toner {
            color: #ff6666;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>HP打印机碳粉情况</h1>
    <b2>当前时间：</b2>
    <p id="current-time"></p>

    <script>
        // 定义一个函数来获取并显示当前时间
        function displayCurrentTime() {
            const now = new Date(); // 获取当前时间
            const timeString = now.toLocaleTimeString(); // 格式化时间为本地时间字符串
            document.getElementById("current-time").textContent = timeString; // 显示时间
        }

        // 页面加载时显示时间
        displayCurrentTime();

        // 每秒更新一次时间
        setInterval(displayCurrentTime, 1000);
    </script>
    <table>
        <thead>
            <tr>
                <th>楼层</th>
                <th>设备编号</th>
                <th>IP地址</th>
                <th>产品</th>
                <th>耗材</th>
            </tr>
        </thead>
        <tbody>
"""

print(f"共爬取了 {len(results)} 个URL的数据")

# 填充表格内容
for i, result in enumerate(results):
    # 查找对应的设备数据
    device_info = device_data[i] if i < len(device_data) else {'floor': 'N/A', 'device_id': 'N/A', 'ip_address': 'N/A'}
    
    html_content += f"""
    <tr>
        <td>{device_info['floor']}</td>
        <td>{device_info['device_id']}</td>
        <td>{device_info['ip_address']}</td>
        <td>{result['product']}</td>
        <td>
            <ul class="consumable-list">
                {''.join([f"<li class='low-toner'>{c['text']}</li>" if isinstance(c, dict) and c.get('has_low_toner', False) else f"<li>{c['text'] if isinstance(c, dict) else c}</li>" for c in result['consumables']])}
            </ul>
        </td>
    </tr>
"""

# 结束HTML内容
html_content += """
        </tbody>
    </table>
</body>
</html>
"""

# 将HTML内容写入文件
with open("output.html", "w", encoding="utf-8") as file:
    file.write(html_content)

print("HTML文件已生成：output.html")
