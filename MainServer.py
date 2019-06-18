import tornado.ioloop
import tornado.web
from tornado.websocket import WebSocketHandler
import os
import time
import json
import gc
import uuid
from server.dbserv import dbserv
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
import tornado.gen
from model.funcs import load_categories_E

from websocket import create_connection

ws_log = create_connection("ws://127.0.0.1:9000/getLogs")

DB=dbserv()
dict_sessions={}
cats=load_categories_E()
cats.sort()
# print(cats)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("session_id")
        # return dict_sessions.get(session_id)

class GetLabelHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = dict_sessions[str(self.get_current_user(), encoding="utf8")]
        self.render("editAction.html",
                    labels=cats,
                    user=DB.selectUser(username),
                    groups=DB.GroupMembers(username),
                    tagLabels=DB.getAllLabel(),
                    hidValue='None'
                    )


class AddLabelHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        new_action=self.get_argument("action")
        DB.addLabel(new_action)
        d=dict()
        d['type']='update'
        ws_log.send(json.dumps(d))
        self.redirect("/editAct")

class DeleteLabelHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        old_action=self.get_argument("action")
        DB.deletLabel(old_action)
        d = dict()
        d['type'] = 'update'
        ws_log.send(json.dumps(d))
        self.redirect("/editAct")

class DeleteLogHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        action = self.get_argument("action")
        DB.deleteFrame(action)
        self.redirect("/editAct")



class GetLogHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = dict_sessions[str(self.get_current_user(), encoding="utf8")]
        action = self.get_argument("action")
        self.render("editAction.html",
                    labels=cats,
                    user=DB.selectUser(username),
                    groups=DB.GroupMembers(username),
                    tagLabels=DB.getAllLabel(),
                    hidValue=action
                    )

class IndexHandlers(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username=dict_sessions[str(self.get_current_user(),encoding="utf8")]
        self.render("index.html",
                    user=DB.selectUser(username),
                    groups=DB.GroupMembers(username)
                    )

class LoginHandler(BaseHandler):
    def get(self):
        if self.get_current_user() is not None:
            self.redirect("/")
        else:
            self.render("login.html")

    def post(self):
        username=self.get_argument("username")
        passwd=self.get_argument("passwd")
        if DB.Login(username,passwd) is True:
            session_id = str(uuid.uuid1())
            dict_sessions[session_id] = username
            self.set_secure_cookie("session_id", session_id)
            print(dict_sessions)
            self.redirect("/")
        else:
            self.redirect("/login")


class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            print(self.get_secure_cookie("cluster_name"))
            dict_sessions.pop(str(self.get_secure_cookie("session_id"),encoding="utf8"))
        except:
            print("error")
            pass
        self.clear_cookie("session_id")
        self.redirect("/login")


def run(coroutine, parament):
    try:
        coroutine(parament).send(None)
    except StopIteration as e:
        return e.value


class TestHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("test.html")

class AboutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = dict_sessions[str(self.get_current_user(), encoding="utf8")]
        self.render("about.html",
                    user=DB.selectUser(username),
                    groups=DB.GroupMembers(username)
                    )



class AddMember(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = dict_sessions[str(self.get_current_user(), encoding="utf8")]
        new_member=self.get_argument("new_member")
        DB.AddMember(username,new_member)
        self.redirect("/editgroup")


class EditHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = dict_sessions[str(self.get_current_user(), encoding="utf8")]
        self.render("editgroup.html",
                    user=DB.selectUser(username),
                    groups=DB.GroupMembers(username)
                    )

class DeleteMemberHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        username = dict_sessions[str(self.get_current_user(), encoding="utf8")]
        user = DB.selectUser(username)
        if user.isowner:
            # print(self.get_argument("username"))
            DB.deleteMember(self.get_argument("membername"))
            self.redirect("/editgroup")


class socketHandlers(WebSocketHandler):
    users = set()
    executor = ThreadPoolExecutor(20)

    @run_on_executor
    def send_frames(self,message):
        rsv_data = json.loads(message)

        if rsv_data['type'] == 'frame':
            # print(self.frames)
            p = b"data:image/jpeg;base64," + bytes(rsv_data['message'], encoding="utf-8")
            jm = dict()
            jm['frame'] = str(p, encoding='utf-8')
            jm['key'] = 'frame'
            for u in self.users:
                if u is self:
                    continue
                u.write_message(json.dumps(jm))
                print(jm)


    def open(self):
        self.users.add(self)
        print(self.request.remote_ip, '加入')

    # @tornado.gen.coroutine
    def on_message(self, message):
        # gc.collect()
        # yield self.send_frames(message)
        rsv_data = json.loads(message)


        if rsv_data['type'] == 'frame':
            # print(self.frames)
            p = b"data:image/jpeg;base64," +  bytes(rsv_data['message'], encoding="utf-8")
            jm = dict()
            jm['frame'] = str(p, encoding='utf-8')
            jm['key'] = 'frame'
            for u in self.users:
                if u is self:
                    continue
                u.write_message(json.dumps(jm))


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
    settings={
        "static_path":os.path.join(os.path.dirname(__file__), "static"),
        "template_path":os.path.join(os.path.dirname(__file__), "template"),
        "debug":True,
        "cookie_secret":"wer45367thd3et54g3234srt7",
        "login_url":"/login"
    }
    app = tornado.web.Application(
        [
            (r'/', IndexHandlers),
            (r'/MvGet', socketHandlers),
            (r'/login',LoginHandler),
            (r'/logout',LogoutHandler),
            (r'/about',AboutHandler),
            (r'/editgroup',EditHandler),
            (r'/delete',DeleteMemberHandler),
            (r'/addmember',AddMember),
            (r'/editAct',GetLabelHandler),
            (r'/addAction',AddLabelHandler),
            (r'/deleteAction',DeleteLabelHandler),
            (r'/getLog',GetLogHandler),
            (r'/deleteLog',DeleteLogHandler)
        ],
        **settings
    )

    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
