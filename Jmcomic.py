import json
import os
from typing import Optional
from websocket import WebSocketApp
import jmcomic
import requests
from PIL import Image
import shutil
from dotenv import load_dotenv
import base64
import io

PDF_DIR = './pdf'
BASE_DIR = './comic'
HTTP_SERVER_ADD = 'http://47.122.117.204:3000'
QQ = '2107576525'


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
    
# def base64_encode_file(path, chunk_size=1024*1024):
#         b64_buffer = io.BytesIO()
#         with open(path, 'rb') as f:
#             while True:
#                 chunk = f.read(chunk_size)
#                 if not chunk:
#                     break
#                 b64_buffer.write(base64.b64encode(chunk))
#         return b64_buffer.getvalue().decode('utf-8')

# def send_pdf_via_http(group_id, album_id):
#     pdf_path = os.path.join(PDF_DIR, f"{album_id}.pdf")
#     encoded_file = base64_encode_file(pdf_path)
#     base64_file = f"data:application/pdf;base64,{encoded_file}"
#     token = os.getenv("http_server_token")
#     url = HTTP_SERVER_ADD.rstrip() + '/send_group_msg'
#     headers = {
#         "Authorization": f"Bearer {token}"
#     }
#     data = {
#         "group_id": group_id,
#         "message": [
#             {
#                  "type": "file",
#                  "data":{
#                             "file": encoded_file
#                         }
#             }
#         ]
#     }
 
#     try:
#         response = requests.post(url, json=data, headers=headers)
#         response.raise_for_status()
#         print(f"文件发送成功: {response.text}")
#         return response.json()
#     except Exception as e:
#         print(f"文件发送失败: {e}")
#         return None
    
    

    
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
    
    
import asyncio
import json
import base64
import hashlib
import os
import uuid
from typing import List, Optional
import websockets
from pathlib import Path
    
    
    

    
    
class OneBotUpload:
    def __init__(self, ws_url: str = "ws://47.122.117.204:3001", access_token: Optional[str] = None):
        self.ws_url = ws_url
        self.access_token = access_token if access_token is not None else os.getenv("ws_server_token")
        self.websocket = None
        
    async def connect(self):
        """连接到 OneBot WebSocket"""
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
            
        print(f"连接到 {self.ws_url}")
        self.websocket = await websockets.connect(self.ws_url, additional_headers=headers)
        print("WebSocket 连接成功")
        
    async def disconnect(self):
        """断开 WebSocket 连接"""
        if self.websocket:
            await self.websocket.close()
            print("WebSocket 连接已断开")
            
    def calculate_file_chunks(self, file_path: str, chunk_size: int = 64) -> tuple[List[bytes], str, int]:
        """
        计算文件分片和 SHA256
        
        Args:
            file_path: 文件路径
            chunk_size: 分片大小（默认64KB）
            
        Returns:
            (chunks, sha256_hash, total_size)
        """
        chunks = []
        hasher = hashlib.sha256()
        total_size = 0
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
                hasher.update(chunk)
                total_size += len(chunk)
                
        sha256_hash = hasher.hexdigest()
        print(f"文件分析完成:")
        print(f"  - 文件大小: {total_size} 字节")
        print(f"  - 分片数量: {len(chunks)}")
        print(f"  - SHA256: {sha256_hash}")
        
        return chunks, sha256_hash, total_size
    
    async def send_action(self, action: str, params: dict, echo: Optional[str] = None) -> dict:
        if not self.websocket:
            raise RuntimeError("WebSocket 尚未连接或已断开，请先调用 connect()")
        """发送 OneBot 动作请求"""
        if not echo:
            echo = str(uuid.uuid4())
            
        message = {
            "action": action,
            "params": params,
            "echo": echo
        }
        
        print(f"发送请求: {action}")
        await self.websocket.send(json.dumps(message))
        
        # 等待响应
        while True:
            response = await self.websocket.recv()
            data = json.loads(response)
            
            # 检查是否是我们的响应
            if data.get("echo") == echo:
                return data
            else:
                # 可能是其他消息，继续等待
                print(f"收到其他消息: {data}")
                continue
    
    async def upload_file_stream_batch(self, file_path: str,album_id : str , chunk_size: int = 64) -> str:
        """
        一次性批量上传文件流
        
        Args:
            file_path: 要上传的文件路径
            chunk_size: 分片大小
            
        Returns:
            上传完成后的文件路径
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"文件不存在: {file_path_obj}")
            
        # 分析文件
        chunks, sha256_hash, total_size = self.calculate_file_chunks(str(file_path_obj), chunk_size)
        stream_id = str(uuid.uuid4())
        
        print(f"\n开始上传文件: {file_path_obj.name}")
        print(f"流ID: {stream_id}")
        
        # 一次性发送所有分片
        total_chunks = len(chunks)
        
        for chunk_index, chunk_data in enumerate(chunks):
            # 将分片数据编码为 base64
            chunk_base64 = base64.b64encode(chunk_data).decode('utf-8')
            
            # 构建参数
            params = {
                "stream_id": stream_id,
                "chunk_data": chunk_base64,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "file_size": total_size,
                "expected_sha256": sha256_hash,
                "filename": f"{album_id}.pdf",
                "file_retention": 30 * 1000
            }
            
            # 发送分片
            response = await self.send_action("upload_file_stream", params)
            
            if response.get("status") != "ok":
                raise Exception(f"上传分片 {chunk_index} 失败: {response}")
                
            # 解析流响应
            stream_data = response.get("data", {})
            print(f"分片 {chunk_index + 1}/{total_chunks} 上传成功 "
                  f"(接收: {stream_data.get('received_chunks', 0)}/{stream_data.get('total_chunks', 0)})")
        
        # 发送完成信号
        print(f"\n所有分片发送完成，请求文件合并...")
        complete_params = {
            "stream_id": stream_id,
            "is_complete": True
        }
        
        response = await self.send_action("upload_file_stream", complete_params)
        
        if response.get("status") != "ok":
            raise Exception(f"文件合并失败: {response}")
            
        result = response.get("data", {})
        
        if result.get("status") == "file_complete":
            print(f"✅ 文件上传成功!")
            print(f"  - 文件路径: {result.get('file_path')}")
            print(f"  - 文件大小: {result.get('file_size')} 字节")
            print(f"  - SHA256: {result.get('sha256')}")
            return result.get('file_path')
        else:
            raise Exception(f"文件状态异常: {result}")


async def main():
    load_dotenv()
    OneBot = OneBotUpload()
    try:
        await OneBot.connect()
        if not OneBot.websocket:
            raise Exception(f"websocket为空")
        while True:
            raw_data = await OneBot.websocket.recv()
            data = json.loads(raw_data)
            if data["post_type"] == 'meta_event':
                continue
            
            if not data["message"]:
                pass
            else:
                if data["message"][0]["type"] == 'at' and data["message"][0]["data"]["qq"] ==QQ:
                    album_id = data["message"][1]["data"]["text"] if data["message"][1]["data"]["text"] else None
                    
                    
                    
            
            
            

            # 执行上传
        # uploaded_path = await OneBot.upload_file_stream_batch(file_path, chunk_size)
            
        # print(f"\n🎉 测试完成! 上传后的文件路径: {uploaded_path}")
            
    except Exception as e:
            print(f"❌ 测试失败: {e}")
            raise
    finally:
            await OneBot.disconnect()
    
    
    
    
    


if __name__ == "__main__":
    asyncio.run(main())
    # a= base64_encode_file("./pdf/123141.pdf")
    # print(a)
    # send_group_text_message("779220091","sadad")
    # download_album_to_pdf(123141)
    # send_pdf_via_http("779220091","123141")
    # removeCache(432232)
    # run_ws()
