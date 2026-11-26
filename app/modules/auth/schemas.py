from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)


class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)


class ResetPasswordSchema(Schema):
    # Mã nằm trong link đặt lại mật khẩu gửi cho user
    token = fields.String(required=True, validate=validate.Length(min=1))
    # Cùng luật độ dài với đổi mật khẩu
    new_password = fields.String(required=True, validate=validate.Length(min=8))


class LogoutSchema(Schema):
    refresh_token = fields.String()


class UpdateProfileSchema(Schema):
    name = fields.String(validate=validate.Length(min=1, max=255))
    address = fields.String(allow_none=True, validate=validate.Length(max=512))
    date_of_birth = fields.Date(allow_none=True)
    sex = fields.String(allow_none=True, validate=validate.Length(max=10))


class ChangePasswordSchema(Schema):
    current_password = fields.String(required=True)
    new_password = fields.String(required=True, validate=validate.Length(min=8))

    @validates_schema
    def reject_unchanged_password(self, data, **kwargs):
        if data.get('new_password') == data.get('current_password'):
            raise ValidationError(
                'New password must differ from the current one',
                'new_password',
            )
