from websocket import create_connection
import cv2
import base64
import json
import threading
import queue

try:
    ws = create_connection("ws://127.0.0.1:8888/MvGet")
    ws_label=create_connection("ws://127.0.0.1:8889/LabelGet")
except:
    raise Exception("服务未启动！！！")
# ws_pose=create_connection("ws://127.0.0.1:8890/PoseGet")
data=dict()
data['type']='frame'

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 256)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,256)

Q=queue.Queue(maxsize=30)

def send(w,data):
    w.send(data)


class CameraPro(threading.Thread):
    def run(self):
        while True:
            if cap.isOpened():
                isSuccess, frame = cap.read()
                if isSuccess:
                    base64_str = cv2.imencode('.jpeg', frame)[1].tostring()
                    base64_str = base64.b64encode(base64_str)
                    # print(type(base64_str))
                    data['message'] = str(base64_str, encoding="utf-8")
                    # print(data['message'])
                    dataa = json.dumps(data)
                    Q.put(dataa)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break


class Send2label(threading.Thread):
    def run(self):
        while True:
            data=Q.get()
            ws_label.send(data)

class Send2Mv(threading.Thread):
    def run(self):
        while True:
            data=Q.get()
            ws.send(data)

class Send2Pose(threading.Thread):
    def run(self):
        while True:
            data=Q.get()
            ws_pose.send(data)

try:
    CameraPro().start()
    Send2label().start()
    Send2Mv().start()
except:
    print("服务被断开！！！")
# Send2Pose().start()

# while True:
#     if cap.isOpened():
#         isSuccess, frame = cap.read()
#         if isSuccess:
#             base64_str = cv2.imencode('.jpeg', frame)[1].tostring()
#             base64_str = base64.b64encode(base64_str)
#             # print(type(base64_str))
#             data['message']=str(base64_str,encoding = "utf-8")
#             # print(data['message'])
#             dataa=json.dumps(data)
#             # ws.send(dataa)
#             # ws_label.send(dataa)
#
#             threading.Thread(target=send,args=(ws,dataa)).start()
#             threading.Thread(target=send, args=(ws_label, dataa)).start()
#
#             # del base64_str
#             # del frame
#             # gc.collect()
#
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break