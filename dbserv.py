from server.DataBaseModels import User, Group, Camera, Message,Taglabel,FrameLogs


class dbserv:
    def AddUser(self, username, passwd) -> None:
        User.create(user_name=username, passwd=passwd)

    def AddGroup(self, owner) -> None:
        Group.create(owner=owner)

    def AddCamera(self, name, ip, group) -> None:
        Camera.create(name=name, ip=ip, group=group)

    def AddMessage(self, sender, geter, text) -> None:
        Message.create(sender=sender, geter=geter, text=text)

    def Login(self, username, passwd) -> bool:
        try:
            res = User.select().where(User.user_name == username).where(User.passwd == passwd).get()
            return True
        except:
            return False

    def selectUser(self, username) -> User:
        return User.select().where(User.user_name == username).get()

    def GroupMembers(self, usename) -> list:
        u=self.selectUser(usename)
        gs=User.select().where(User.group==u.group)
        grs=[]
        for g in gs:
            grs.append(g)

        return grs

    def AddMember(self,username,new_member)->None:
        u=self.selectUser(username)
        new_u=self.selectUser(new_member)
        new_u.group=u.group
        new_u.save()

    def deleteUser(self,username) -> None:
        User.delete().where(User.user_name==username).execute()

    def deleteMember(self,username):
        u=self.selectUser(username)
        u.group=None
        u.save()

    def addLabel(self,action)->None:
        if action in self.getAllLabel():
            return
        Taglabel.create(label=action)

    def getAllLabel(self):
        res=[]
        labels=Taglabel.select()
        for label in labels:
            res.append(label.label)
        return  res

    def deletLabel(self,action):
        if action not in self.getAllLabel():
            return
        Taglabel.delete().where(Taglabel.label==action).execute()

    def addLog(self,action,frame):
        FrameLogs.create(label=action,baseStr=frame)


    def getFrames(self,action):
        res=[]
        fs=FrameLogs.select().where(FrameLogs.label==action)
        for f in fs:
            res.append(f.baseStr)
        return res

    def deleteFrame(self,action):
        FrameLogs.delete().where(FrameLogs.label==action).execute()






if __name__ == '__main__':
    DB=dbserv()
    fs=DB.getFrames("drinking")
    print(type(fs[0]))
    # print(len(DB.getFrames("drinking")))
    # DB.addLabel("drinking")
    # DB.deletLabel("drinking")
    # print(DB.getAllLabel())
    # DB.deleteUser("yy")
    # u=DB.selectUser("xp")
    # u.user_name="xupeng"
    # u.save()
    # u = DB.selectUser("zz")
    # u.user_name="xiaoming"
    # u.save()
    # print(u.__dict__)
    # u.isowner=True
    # u.save()
    # print([u.__dict__ for u in DB.GroupMembers("xp")])
    # print(Login("xp21","123"))
