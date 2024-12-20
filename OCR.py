import atexit
import wcocr
import os
import sys
from flask import Flask, request, jsonify
from werkzeug.datastructures.file_storage import FileStorage
import uuid
from gevent import pywsgi

# 创建 Flask 应用
app = Flask(__name__)

# 设置允许上传的文件类型
ALLOWED_EXTENSIONS = ("jpg", "jpeg", "png", "bmp", "tif")


def get_save_dir() -> str:
    # 图片保存目录
    if getattr(sys, "frozen", False):
        # 如果是打包后的可执行文件
        return os.path.join(os.path.dirname(sys.executable), "img")
    else:
        # 如果是脚本运行
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


def find_wechat_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    common_paths = os.path.join(script_dir, "path")
    if os.path.exists(common_paths):
        return common_paths
    else:
        print(f"The path folder does not exist at {common_paths}.")
        return None


def find_wechatocr_exe():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    wechatocr_path = os.path.join(script_dir, "path", "WeChatOCR", "WeChatOCR.exe")
    if os.path.isfile(wechatocr_path):
        return wechatocr_path
    else:
        print(f"The WeChatOCR.exe does not exist at {wechatocr_path}.")
        return None


def wechat_ocr_init():
    wechat_path = find_wechat_path()
    wechatocr_path = find_wechatocr_exe()
    if not wechat_path or not wechatocr_path:
        raise Exception("WeChatOCR.exe not found.")

    wcocr.init(wechatocr_path, wechat_path)


def wechat_ocr(image_path):

    result = wcocr.ocr(image_path)
    texts = []

    for temp in result["ocr_response"]:
        text = temp["text"]
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="ignore")
        texts.append(text)

    return texts


def save_file(file: FileStorage) -> str:

    # 检查文件类型
    if not file.filename.split(".")[-1] in ALLOWED_EXTENSIONS:
        return ""

    # 生成唯一文件名
    new_filename = uuid.uuid4().hex + "." + file.filename.split(".")[-1]

    save_dir = get_save_dir()

    # 保存图片
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    file_path = os.path.join(save_dir, new_filename)
    file.save(file_path)

    return file_path


# 定义上传图片路由
@app.route("/upload_ocr", methods=["POST"])
def upload_image():
    # 检查请求是否包含文件
    if "file" not in request.files:
        return jsonify({"code": 400, "msg": "没有上传文件"})

    # 获取上传的文件
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"code": 400, "msg": "没有选择文件"})

    file_path = save_file(file)
    if file_path == "":
        return jsonify({"code": 400, "msg": "不支持的文件类型"})

    texts = wechat_ocr(file_path)

    # 返回上传成功信息
    return jsonify({"code": 200, "msg": "上传成功", "data": texts})


# 释放
atexit.register(wcocr.destroy)

# if __name__ == "__main__":
#     wechat_ocr_init()
#     # 设置端口
#     app.run(host="0.0.0.0", port=5001)

if __name__ == "__main__":
    wechat_ocr_init()
    print("start listen 127.0.0.1:5000 0.0.0.0:5000")
    print("example : POST 127.0.0.1:5000/upload_ocr")
    server = pywsgi.WSGIServer(("127.0.0.1", 5000), app)
    server.serve_forever()
    server0 = pywsgi.WSGIServer(("0.0.0.0", 5000), app)
    server0.serve_forever()
