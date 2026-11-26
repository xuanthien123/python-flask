from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.common.fields import TrimmedString


class CreateCategorySchema(Schema):
    name = TrimmedString(required=True, validate=validate.Length(min=1, max=120))
    description = fields.String(allow_none=True)


class UpdateCategorySchema(Schema):
    name = TrimmedString(validate=validate.Length(min=1, max=120))
    description = fields.String(allow_none=True)

    @validates_schema
    def reject_empty_update(self, data, **kwargs):
        if not data:
            raise ValidationError('Provide at least one field to update')
