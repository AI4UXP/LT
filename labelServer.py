import tornado.ioloop
import tornado.web
from tornado.websocket import WebSocketHandler
import os
import time
import json
import socket
import base64
from io import BytesIO
from PIL import Image
import gc
import copy
import queue
import tornado.gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

import torch.nn.parallel
from torch.nn import functional as F
from torch.autograd import Variable
from model.funcs import load_transform, load_model, load_categories,load_categories_E

from lstmModel.models import *
from lstmModel.dataset import *
from lstmModel.extract_frames import extract_frames
import argparse
from server.dbserv import dbserv

from websocket import create_connection

ws_log = create_connection("ws://127.0.0.1:9000/getLogs")

# DB=dbserv()
# tagActions=DB.getAllLabel()
# print(tagActions)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

categories = load_categories()
categories_E=load_categories_E()
# print(len(categories))
model_id = 1
model = load_model(model_id, categories).to(DEVICE)
transform = load_transform()

myname = socket.gethostname()
myaddr = socket.gethostbyname(myname)


parser = argparse.ArgumentParser()
parser.add_argument(
    "--video_path", type=str, default="./test2.avi", help="Path to video"
)
parser.add_argument("--dataset_path", type=str, default="D:\\下载\\FINAL\\ActionRecognition\\data\\UCF-101-frames", help="Path to UCF-101 dataset")
parser.add_argument("--image_dim", type=int, default=112, help="Height / width dimension")
parser.add_argument("--channels", type=int, default=3, help="Number of image channels")
parser.add_argument("--latent_dim", type=int, default=512, help="Dimensionality of the latent representation")
parser.add_argument("--checkpoint_model", type=str, default="D:\\pyproject\\BYSJ\\lstmModel\\ConvLSTM_150.pth", help="Optional path to checkpoint model")
opt = parser.parse_args()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
input_shape = (opt.channels, opt.image_dim, opt.image_dim)

transform_lstm = transforms.Compose(
    [
        transforms.Resize(input_shape[-2:], Image.BICUBIC),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ]
)

labels = sorted(list(set(os.listdir(opt.dataset_path))))
print(labels)

m = torch.load(opt.checkpoint_model)
model_lstm = ConvLSTM(num_classes=len(labels), latent_dim=opt.latent_dim,bidirectional=False,attention=False)
model_lstm=model_lstm.to(device)
model_lstm.load_state_dict({str(k).replace('lstm.final','output_layers'):v for k,v in m.items()})
model_lstm.eval()

print("模型参数加载成功，等待服务中。。。。")

def getLabel(frames):
    print(frames)
    data = torch.stack([transform(frame) for frame in frames]).to(DEVICE)
    with torch.no_grad():
        input_var = Variable(data.view(-1, 3, data.size(2), data.size(3)))
    logits = model(input_var)
    h_x = F.softmax(logits, 1).mean(dim=0).data
    probs, idx = h_x.sort(0, True)
    return categories[idx[0]]+"("+categories_E[idx[0]]+")"


def run(coroutine, parament):
    try:
        coroutine(parament).send(None)
    except StopIteration as e:
        return e.value






class socketHandlersLabel(WebSocketHandler):
    users = set()
    executor = ThreadPoolExecutor(20)

    @run_on_executor
    def getLabel(self,frames):
        print(frames)
        data = torch.stack([transform(frame) for frame in frames]).to(DEVICE)
        with torch.no_grad():
            input_var = Variable(data.view(-1, 3, data.size(2), data.size(3))).to(device)
        logits = model(input_var)
        h_x = F.softmax(logits, 1).mean(dim=0).data
        probs, idx = h_x.sort(0, True)

        image_tensor = Variable(transform_lstm(frames[0])).to(device)
        image_tensor = image_tensor.view(1, 1, *image_tensor.shape)
        # print(image_tensor.shape)

        with torch.no_grad():
            prediction = model_lstm(image_tensor)
            predicted_label = labels[prediction.argmax(1).item()]

        # print(predicted_label)
        result=[]
        result.append(predicted_label)
        result.append(categories_E[idx[0]])
        result.append(probs[0].item())
        result.append(categories_E[idx[1]])
        result.append(probs[1].item())
        result.append(categories_E[idx[2]])
        result.append(probs[2].item())
        result.append(categories_E[idx[3]])
        result.append(probs[3].item())
        result.append(categories_E[idx[4]])
        result.append(probs[4].item())
        print(result)
        # for s in result:
        #     if s in tagActions:
        #         result.append(s)
        #         result.append(1232321)
        return result

        # return categories[idx[0]] + "(" + categories_E[idx[0]] + ")"


    def open(self):
        self.users.add(self)
        print(self.request.remote_ip, '申请服务得到允许！')
        # self.set_secure_cookie("cluster_name",categories_E)

    @tornado.gen.coroutine
    def on_message(self, message):

        # gc.collect()
        rsv_data = json.loads(message)
        log_data=dict()

        if rsv_data['type'] == 'frame':
            log_data['frame']=rsv_data['message']
            image = base64.b64decode(rsv_data['message'])

            # import cv2
            # import numpy as np
            # img_array = np.fromstring(image, np.uint8)  # 转换np序列
            # img = cv2.imdecode(img_array, cv2.COLOR_BGR2RGB)  # 转换Opencv格式
            # print(img)

            image = BytesIO(image)
            image = Image.open(image)
            jm_label = dict()
            label=yield self.getLabel([image])
            jm_label['label'] =label
            log_data['label'] =label
            log_data['type']='label'
            del image
            jm_label['key'] = 'label'
            # print(jm_label['label'])
            for u in self.users:
                if u is self:
                    continue
                u.write_message(json.dumps(jm_label))
            ws_log.send(json.dumps(log_data))




    # b"data:image/jpeg;base64,"+bytes(rsv_data['message'],encoding = "utf-8")
    def on_close(self):
        self.users.remove(self)

    def on_finish(self):
        pass

    def check_origin(self, origin):
        return True







class TestSocket(WebSocketHandler):

    def open(self):
        print("测试连接已建立，开始发生测试消息。")
        data = dict()

        data['key'] = 'label'
        data['label'] = 'bb'
        while True:
            self.write_message(json.dumps(data))
            time.sleep(0.5)

    def on_close(self):
        pass

    def on_message(self, message):
        pass

    def check_origin(self, origin):
        return True


if __name__ == '__main__':
    app = tornado.web.Application([
        (r'/LabelGet', socketHandlersLabel),
    ],
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        template_path=os.path.join(os.path.dirname(__file__), "template"),
        debug=True
    )

    app.listen(8889)
    tornado.ioloop.IOLoop.current().start()
