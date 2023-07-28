from marshmallow import Schema, validate
from webargs import fields


class Foo(Schema):
    """
    Schema description here.
    """

    bar = fields.Integer(
        description="Lorem ipsum dolor...",
        required=True,
        validate=validate.OneOf(["SPLIFF", "DONK", "GENGJA"]),
    )

    spliff = fields.Integer(
        description="Lorem ipsum dolor...",
        required=True,
    )

    donk = fields.Float(
        description="Lorem ipsum dolor...",
        required=True,
    )


class Hemi(Schema):
    """
    Schema description here.
    """

    demi = fields.Integer(
        description="Lorem ipsum dolor...",
        required=True,
        validate=validate.OneOf(["1/2", "0.5", "HALF"]),
    )

    semi = fields.Integer(
        description="Lorem ipsum dolor...",
        required=True,
    )

    quasi = fields.Float(
        description="Lorem ipsum dolor...",
        required=True,
    )


class Error(Schema):
    message = fields.Str(required=True)
