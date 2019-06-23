import tornado.ioloop
import tornado.web
from tornado.websocket import WebSocketHandler
import os
import json
from websocket import create_connection
from server.dbserv import dbserv
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
import tornado.gen
import time

DB=dbserv()
# tagActions=DB.getAllLabel()
# print(tagActions)
framelog=dict()
sended=dict()


class socketHandlersLogo(WebSocketHandler):
    users=set()
    executor = ThreadPoolExecutor(20)
    tagActions = DB.getAllLabel()


    @run_on_executor
    def logAction(self,logs):
        for action in logs['label']:
            if action in self.tagActions:
                # framelog[action]=logs['frame']
                DB.addLog(action,logs['frame'])
                print("出现告警动作： ",action)
                if action in sended.keys() and sended[action] is True:
                    return -1
                return action
        return -1

    @run_on_executor
    def send_log(self,action):
        frames=DB.getFrames(action)
        for f in frames:
            p = b"data:image/jpeg;base64," + bytes(f, encoding="utf-8")
            jm = dict()
            jm['frame'] = str(p, encoding='utf-8')
            jm['key'] = 'frame'
            self.write_message(jm)
        return 1

    def open(self):
        self.users.add(self)
        print("{}申请服务得到允许！".format(self))
        data=dict()
        data['type']='history'
        data['history']=[s for s in sended.keys()]
        self.write_message(json.dumps(data))

    def on_close(self):
        pass

    @tornado.gen.coroutine
    def on_message(self, message):
        logs = json.loads(message)
        if logs['type']=='getLog':
            log_action=logs['action']
            print("收到日志请求：",log_action)
            frames = DB.getFrames(log_action)
            for f in frames:
                p = b"data:image/jpeg;base64," + bytes(f, encoding="utf-8")
                jm = dict()
                jm['frame'] = str(p, encoding='utf-8')
                jm['key'] = 'frame'
                self.write_message(jm)
                time.sleep(0.05)

            return
        if logs['type']=='update':
            self.tagActions = DB.getAllLabel()
            print("接收到动作列表更新请求，并已经处理成功！")
            print(self.tagActions)
            return
        action=yield self.logAction(logs)
        if action!=-1:
            print("记录成功！")
            s_data = dict()
            s_data['type']='new_taged'
            s_data['new_taged'] = action
            for u in self.users:
                if u is self:
                    continue
                sended[action]=True
                try:
                    u.write_message(json.dumps(s_data))
                except:
                    print(u,"已关闭！")
        # logs=json.loads(message)
        # print(json.loads(message))

    def check_origin(self, origin):
        return True


if __name__ == '__main__':
    app = tornado.web.Application([
        (r'/getLogs', socketHandlersLogo),
    ],
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        template_path=os.path.join(os.path.dirname(__file__), "template"),
        debug=True
    )

    app.listen(9000)
    tornado.ioloop.IOLoop.current().start()
