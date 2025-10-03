import json
import os
from websocket import WebSocketApp
import jmcomic
import requests
from PIL import Image
import shutil
from dotenv import load_dotenv
import base64

PDF_DIR = './pdf'
BASE_DIR = './comic'
HTTP_SERVER_ADD = 'http://47.122.117.204:3000'


def pngs_to_pdf(png_dir, output_pdf_dir, output_pdf_name):
    if not os.path.exists(output_pdf_dir):
        os.makedirs(output_pdf_dir)
    png_files = [f for f in os.listdir(png_dir) if f.endswith('.png')]
    png_files.sort()
    images = [Image.open(os.path.join(png_dir, f)).convert('RGB') for f in png_files]
    if images:
        output_pdf_path = os.path.join(output_pdf_dir, output_pdf_name)
        images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
        print(f"已生成PDF：{output_pdf_path}")
        return output_pdf_path
    else:
        print("未找到PNG文件")
        return None

def download_album_to_pdf(album_id):
    print(f"[info] 开始下载 {album_id}")
    option = jmcomic.create_option_by_file("./option.yml")
    jmcomic.download_album(album_id, option)
    pngs_to_pdf(os.path.join(BASE_DIR,f"{album_id}"),PDF_DIR,f"{album_id}.pdf")
    
def removeCache(album_id):
    pdf_path = os.path.join(PDF_DIR,f"{album_id}.pdf")
    os.remove(pdf_path)
    comic_path = os.path.join(BASE_DIR,f"{album_id}")
    shutil.rmtree(comic_path)
    

def send_pdf_via_http(group_id, album_id):
    pdf_path = os.path.join(PDF_DIR,f"{album_id}.pdf")
    with open(pdf_path, "rb") as f:
        encoded_file = base64.b64encode(f.read()).decode('utf-8')
    token = os.getenv("http_server_token")
    url = HTTP_SERVER_ADD.rstrip() + '/send_group_msg'
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "group_id": group_id,
        "message": [
            {
                 "type": "file",
                 "data":{
                            "file": encoded_file
                        }
            }
        ]
    }
 
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        print(f"文件发送成功: {response.text}")
        return response.json()
    except Exception as e:
        print(f"文件发送失败: {e}")
        return None
    
    

    
def send_group_text_message(group_id: str, content: str):
    
    token = os.getenv("http_server_token")
    url = HTTP_SERVER_ADD.rstrip('/') + '/send_group_msg'
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "group_id": group_id,
        "message": [
            {
                 "type": "text",
                 "data":{
                            "text": content
                        }
            }
        ]
    }
 
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        print(f"消息发送成功: {response.text}")
        return response.json()
    except Exception as e:
        print(f"消息发送失败: {e}")
        return None
    


def on_message(ws, message):
    print("收到消息:", message)
    try:
        data = json.loads(message)
        # 假设 napcatqq 消息结构中有 'at' 字段、'text' 字段、'group_id' 字段
        if data.get('at'):
            text = data.get('text', '')
            group_id = data.get('group_id', '')
            # 解析本子id，例如：@机器人 422866
            parts = text.split()
            for part in parts:
                if part.isdigit():
                    album_id = part
                    pdf_path = download_album_to_pdf(album_id)
                    if pdf_path:
                        send_pdf_via_http(group_id, pdf_path)
                        print(f"已上传PDF: {pdf_path}")
                        ws.send(f"PDF已上传: {os.path.basename(pdf_path)}")
                    else:
                        ws.send("PDF生成失败")
    except Exception as e:
        print("消息处理异常:", e)

def on_error(ws, error):
    print("WebSocket 错误:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket 连接关闭")

def on_open(ws):
    print("WebSocket 连接已建立")

def run_ws():
    ws_url = "ws://47.122.117.204:3001" 
    ws = WebSocketApp(ws_url,
                      on_open=on_open,
                      on_message=on_message,
                      on_error=on_error,
                      on_close=on_close)
    ws.run_forever()



if __name__ == "__main__":
    load_dotenv()
    # send_group_text_message("779220091","sadad")
    # download_album_to_pdf(432232)
    send_pdf_via_http("779220091","432232")
    # removeCache(432232)
    run_ws()
