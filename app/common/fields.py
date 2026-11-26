from marshmallow import fields


class TrimmedString(fields.String):
    def _deserialize(self, value, attr, data, **kwargs):
        return super()._deserialize(value, attr, data, **kwargs).strip()
