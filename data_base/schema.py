from peewee import Model, CharField, IntegerField, SqliteDatabase

db = SqliteDatabase("our_base.sqlite")


class BaseModel(Model):
    class Meta:
        database = db


class Preferences(BaseModel):
    user_id = IntegerField(unique=True)
    name = CharField(null=True)
    background = IntegerField(null=True)
    font_size = IntegerField(null=True)
    kerning = IntegerField(null=True)


db.create_tables([Preferences])
