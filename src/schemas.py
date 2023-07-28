from marshmallow import Schema
from webargs import fields


class Error(Schema):
    message = fields.Str(required=True)
