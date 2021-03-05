from passlib.hash import bcrypt
from tortoise import fields
from tortoise.models import Model
from tortoise.contrib.pydantic import pydantic_model_creator


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(20, unique=True)
    password_hash = fields.CharField(128)

    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)


class Message(Model):
    id = fields.IntField(pk=True)
    group_id = fields.IntField()
    data = fields.JSONField()


# Pydantic models
User_Pydantic = pydantic_model_creator(User, name='User')
UserIn_Pydantic = pydantic_model_creator(
    User, name='UserIn', exclude_readonly=True
)
Message_Pydantic = pydantic_model_creator(Message, name='Message')
MessageIn_Pydantic = pydantic_model_creator(
    Message, name='MessageIn', exclude_readonly=True, exclude=('group_id',)
)
