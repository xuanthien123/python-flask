from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate, validates_schema

from app.common.fields import TrimmedString

# Giá trị ?sort= được nhận. Có dấu '-' phía trước là xếp giảm dần
PRODUCT_SORT_KEYS = ('id', 'name', 'price', '-id', '-name', '-price')


class ListProductsQuerySchema(Schema):
    class Meta:
        # Bỏ qua tham số lạ như ?page=, ?per_page= vì phân trang được đọc ở chỗ khác
        unknown = EXCLUDE

    # Không gửi q thì là chuỗi rỗng, nghĩa là không lọc theo tên
    q = TrimmedString(load_default='')
    category_id = fields.Integer(validate=validate.Range(min=1))
    min_price = fields.Float(validate=validate.Range(min=0))
    max_price = fields.Float(validate=validate.Range(min=0))
    # Không gửi sort thì xếp theo id tăng dần
    sort = fields.String(load_default='id', validate=validate.OneOf(PRODUCT_SORT_KEYS))

    # Kiểm tra cần so nhiều field với nhau thì đặt ở @validates_schema.
    # Hàm này chỉ chạy khi không field nào bị lỗi.
    @validates_schema
    def reject_inverted_price_range(self, data, **kwargs):
        has_both_prices = 'min_price' in data and 'max_price' in data
        if has_both_prices and data['min_price'] > data['max_price']:
            raise ValidationError(
                'min_price must not be greater than max_price', field_name='min_price',
            )


class CreateProductSchema(Schema):
    # TrimmedString cắt khoảng trắng hai đầu trước khi kiểm độ dài, nên "   " bị từ chối
    name = TrimmedString(required=True, validate=validate.Length(min=1, max=255))
    # allow_none: cho phép gửi "description": null
    description = fields.String(allow_none=True)
    price = fields.Float(required=True, validate=validate.Range(min=0))
    # strict=True: từ chối số lẻ như 2.5. Không có nó marshmallow tự cắt 2.5 thành 2
    quantity = fields.Integer(strict=True, load_default=0, validate=validate.Range(min=0))
    # Không gửi thì là list rỗng. Truyền list (không có ngoặc) để mỗi lần load
    # tạo một list mới, không dùng chung một list giữa các request
    category_ids = fields.List(
        fields.Integer(strict=True, validate=validate.Range(min=1)),
        load_default=list,
    )


class UpdateProductSchema(Schema):
    # Field nào cũng không bắt buộc: gửi field nào thì sửa field đó.
    # Luật kiểm tra từng field giống lúc tạo product.
    # Không đặt load_default: field không gửi phải giữ giá trị cũ, không bị đổi về 0.
    name = TrimmedString(validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True)
    price = fields.Float(validate=validate.Range(min=0))
    quantity = fields.Integer(strict=True, validate=validate.Range(min=0))
    # Gửi category_ids thì thay toàn bộ category cũ, gửi [] là bỏ hết category
    category_ids = fields.List(
        fields.Integer(strict=True, validate=validate.Range(min=1)),
    )

    @validates_schema
    def reject_empty_update(self, data, **kwargs):
        # Body {} thì không có gì để sửa, báo lỗi để client biết là gửi thiếu
        if not data:
            raise ValidationError('Provide at least one field to update')
