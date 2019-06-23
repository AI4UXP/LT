from peewee import Model, SqliteDatabase, IntegerField, CharField, PrimaryKeyField, ForeignKeyField,BooleanField

db = SqliteDatabase("LookThere.db")

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    id = PrimaryKeyField()
    isowner=BooleanField(default=False)
    group = IntegerField(null=True)
    user_name = CharField(null=False, unique=True)
    passwd = CharField(null=False)

    class Meta:
        db_table = 'user'

class Group(BaseModel):
    id = PrimaryKeyField()
    owner = ForeignKeyField(User, to_field='id', related_name='user')

    class Meta:
        db_table = 'group'

class Camera(BaseModel):
    id = PrimaryKeyField()
    name = CharField(null=False)
    ip = CharField(null=False)
    group = ForeignKeyField(Group, to_field='id', related_name='group')

    class Meta:
        db_table = 'camera'

class Message(BaseModel):
    id = PrimaryKeyField()
    sender = ForeignKeyField(User, to_field='id', related_name='user')
    geter = ForeignKeyField(User, to_field='id', related_name='user')
    text = CharField(null=False)

    class Meta:
        db_table = 'message'

class Taglabel(BaseModel):
    id=PrimaryKeyField()
    label=CharField(null=False)

    class Meta:
        db_table='taglabel'

class FrameLogs(BaseModel):
    id=PrimaryKeyField()
    label=CharField(null=False)
    baseStr=CharField(null=False)

    class Meta:
        db_table='framelog'

if __name__ == '__main__':
    f=FrameLogs.select()
    for fs in f:
        print(fs.__dict__)
    # FrameLogs.create_table()
    # Taglabel.create_table()
    # User.create_table()
    # Group.create_table()
    # Camera.create_table()
    # Message.create_table()
    # User.create(user_name='yy',passwd='123',group='1')
    # User.create(user_name='jj', passwd='123', group='1')
    # User.create(user_name='zz', passwd='123', group='1')
    # User.create(user_name='hh', passwd='123', group='1')
    # User.create(user_name='cc', passwd='123')
    # us=User.select()
    # for u in us:
    #     print(u.__dict__)
    # print(u.__dict__)
    # Group.create(owner=u)
    # g = Group.get()
    # u.group=g
    # u.save()
    # print(u.__dict__)
    # print(g.owner)
