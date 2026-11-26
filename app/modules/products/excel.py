import math
from io import BytesIO

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from app.common.errors import ApiError

XLSX_MIMETYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
TEMPLATE_FILENAME = 'product_import_template.xlsx'
PRODUCTS_SHEET_TITLE = 'Products'
MAX_IMPORT_ROWS = 1000
LAST_INPUT_ROW = MAX_IMPORT_ROWS + 1
CATEGORY_COLUMN_COUNT = 3
CATEGORY_HEADERS = [f'category_{index}' for index in range(1, CATEGORY_COLUMN_COUNT + 1)]
PRODUCT_HEADERS = ['name', 'description', 'price', 'quantity'] + CATEGORY_HEADERS

FONT_NAME = 'Arial'
BODY_FONT = Font(name=FONT_NAME, size=10)
BOLD_FONT = Font(name=FONT_NAME, size=10, bold=True)
TITLE_FONT = Font(name=FONT_NAME, size=14, bold=True)
HEADER_FILL = PatternFill('solid', fgColor='D9E1F2')
REQUIRED_HEADER_FILL = PatternFill('solid', fgColor='FFE699')
THIN_BORDER = Border(bottom=Side(style='thin', color='808080'))
WRAP_TOP = Alignment(wrap_text=True, vertical='top')

PRODUCT_COLUMNS = [
    {'header': 'name', 'width': 32, 'required': True, 'number_format': None},
    {'header': 'description', 'width': 40, 'required': False, 'number_format': None},
    {'header': 'price', 'width': 12, 'required': True, 'number_format': '#,##0.00'},
    {'header': 'quantity', 'width': 12, 'required': False, 'number_format': '0'},
] + [
    {'header': header, 'width': 18, 'required': False, 'number_format': None}
    for header in CATEGORY_HEADERS
]

# Các cột của file export (dạng báo cáo), theo thứ tự từ trái sang phải.
# number_format: cách Excel hiển thị số, None là để mặc định.
EXPORT_COLUMNS = [
    {'header': 'id', 'width': 8, 'number_format': '0'},
    {'header': 'name', 'width': 32, 'number_format': None},
    {'header': 'description', 'width': 40, 'number_format': None},
    {'header': 'price', 'width': 12, 'number_format': '#,##0.00'},
    {'header': 'quantity', 'width': 12, 'number_format': '0'},
    {'header': 'categories', 'width': 32, 'number_format': None},
]


def build_import_template(category_names, snapshot_date):
    workbook = Workbook()
    products_sheet = workbook.active
    instructions_sheet = workbook.create_sheet('Instructions')
    categories_sheet = workbook.create_sheet('Categories')

    category_range = fill_categories_sheet(categories_sheet, category_names)
    fill_products_sheet(products_sheet, category_range)
    fill_instructions_sheet(instructions_sheet, snapshot_date.strftime('%d/%m/%Y'))

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream


def fill_categories_sheet(sheet, category_names):
    sheet['A1'] = 'name'
    sheet['A1'].font = BOLD_FONT
    for row_index, category_name in enumerate(category_names, start=2):
        sheet.cell(row=row_index, column=1, value=category_name).font = BODY_FONT
    sheet.column_dimensions['A'].width = 24
    sheet.sheet_state = 'hidden'
    last_row = max(len(category_names) + 1, 2)
    return f'=Categories!$A$2:$A${last_row}'


def build_validation(column_letters, prompt, error=None, **rule):
    validation = DataValidation(allow_blank=True, **rule)
    validation.promptTitle = 'Tip'
    validation.prompt = prompt
    validation.showInputMessage = True
    if error:
        validation.errorTitle = 'Invalid value'
        validation.error = error
        validation.errorStyle = 'stop'
        validation.showErrorMessage = True
    for column_letter in column_letters:
        validation.add(f'{column_letter}2:{column_letter}{LAST_INPUT_ROW}')
    return validation


def fill_products_sheet(sheet, category_range):
    sheet.title = PRODUCTS_SHEET_TITLE
    for column_index, column in enumerate(PRODUCT_COLUMNS, start=1):
        header_cell = sheet.cell(row=1, column=column_index, value=column['header'])
        header_cell.font = BOLD_FONT
        header_cell.fill = REQUIRED_HEADER_FILL if column['required'] else HEADER_FILL
        header_cell.border = THIN_BORDER
        sheet.column_dimensions[header_cell.column_letter].width = column['width']
        for row_index in range(2, LAST_INPUT_ROW + 1):
            cell = sheet.cell(row=row_index, column=column_index)
            cell.font = BODY_FONT
            if column['number_format']:
                cell.number_format = column['number_format']
    sheet.freeze_panes = 'A2'

    category_letters = [chr(ord('E') + index) for index in range(CATEGORY_COLUMN_COUNT)]
    validations = [
        build_validation(
            ['A'],
            'Required. 1-255 characters.\nBắt buộc. 1-255 ký tự.',
            'Name must be 1-255 characters.\nTên phải dài 1-255 ký tự.',
            type='textLength', operator='between', formula1='1', formula2='255',
        ),
        build_validation(
            ['B'],
            'Optional. Leave blank if none.\nKhông bắt buộc. Không có thì để trống.',
        ),
        build_validation(
            ['C'],
            'Required. Number, 0 or more.\nBắt buộc. Số, từ 0 trở lên.',
            'Price must be a number, 0 or more.\nGiá phải là số, từ 0 trở lên.',
            type='decimal', operator='greaterThanOrEqual', formula1='0',
        ),
        build_validation(
            ['D'],
            'Whole number, 0 or more. Blank means 0.\nSố nguyên, từ 0 trở lên. Để trống là 0.',
            'Quantity must be a whole number, 0 or more.\n'
            'Số lượng phải là số nguyên, từ 0 trở lên.',
            type='whole', operator='greaterThanOrEqual', formula1='0',
        ),
        build_validation(
            category_letters,
            'Pick a category from the list.\nChọn category trong danh sách.',
            'Pick a category from the list.\nHãy chọn category trong danh sách.',
            type='list', formula1=category_range,
        ),
    ]
    for validation in validations:
        sheet.add_data_validation(validation)


def write_instruction_row(sheet, row_index, values, font=BODY_FONT, text_widths=None):
    for column_index, value in enumerate(values, start=1):
        cell = sheet.cell(row=row_index, column=column_index, value=value)
        cell.font = font
        cell.alignment = WRAP_TOP
    # Excel giữ chiều cao một dòng cho ô xuống dòng trong file tạo bằng code
    if text_widths:
        line_count = max(
            math.ceil(len(str(value)) / width)
            for value, width in zip(values, text_widths) if width and value
        )
        sheet.row_dimensions[row_index].height = 14 * line_count


def fill_instructions_sheet(sheet, snapshot_text):
    for column_letter, width in zip('ABCDEFG', [22, 20, 48, 48, 12, 18, 18]):
        sheet.column_dimensions[column_letter].width = width

    sheet['A1'] = 'Product import template / Mẫu import sản phẩm'
    sheet['A1'].font = TITLE_FONT

    write_instruction_row(sheet, 3, ['English', '', 'Tiếng Việt'], BOLD_FONT)
    general_rules = [
        (
            'Fill in the Products sheet, one product per row, starting at row 2.',
            'Điền vào sheet Products, mỗi dòng một sản phẩm, bắt đầu từ dòng 2.',
        ),
        (
            'Do not change, move or delete the header row.',
            'Không sửa, di chuyển hay xoá dòng tiêu đề.',
        ),
        (
            'Yellow headers are required columns.',
            'Cột có tiêu đề màu vàng là cột bắt buộc.',
        ),
        (
            'Every filled row in the Products sheet is imported. The example below is only here.',
            'Mọi dòng có dữ liệu trong sheet Products đều được import. '
            'Ví dụ bên dưới chỉ nằm ở đây.',
        ),
        (
            f'The category list was taken from the system on {snapshot_text}. '
            'If a category is missing, download a new template.',
            f'Danh sách category lấy từ hệ thống ngày {snapshot_text}. '
            'Thiếu category thì tải file mẫu mới.',
        ),
    ]
    row_index = 4
    for english_text, vietnamese_text in general_rules:
        write_instruction_row(
            sheet, row_index, [english_text, '', vietnamese_text], text_widths=[40, 0, 46],
        )
        sheet.merge_cells(start_row=row_index, start_column=1, end_row=row_index, end_column=2)
        row_index += 1

    row_index += 1
    write_instruction_row(
        sheet, row_index, ['Column / Cột', 'Required / Bắt buộc', 'Rule', 'Quy tắc'], BOLD_FONT,
    )
    column_rules = [
        ('name', 'Yes / Có',
         'Product name, 1-255 characters. Spaces at both ends are removed.',
         'Tên sản phẩm, 1-255 ký tự. Khoảng trắng ở hai đầu sẽ bị bỏ.'),
        ('description', 'No / Không',
         'Free text. Leave blank if none.',
         'Mô tả tự do. Không có thì để trống.'),
        ('price', 'Yes / Có',
         'Number, 0 or more.',
         'Số, từ 0 trở lên.'),
        ('quantity', 'No / Không',
         'Whole number, 0 or more. Blank means 0.',
         'Số nguyên, từ 0 trở lên. Để trống là 0.'),
        (f'category_1 - category_{CATEGORY_COLUMN_COUNT}', 'No / Không',
         f'Pick from the list. Up to {CATEGORY_COLUMN_COUNT} categories per product. '
         'Leave blank if none.',
         f'Chọn trong danh sách. Tối đa {CATEGORY_COLUMN_COUNT} category cho mỗi sản phẩm. '
         'Không có thì để trống.'),
    ]
    for column_rule in column_rules:
        row_index += 1
        write_instruction_row(sheet, row_index, list(column_rule), text_widths=[20, 18, 46, 46])

    row_index += 2
    write_instruction_row(sheet, row_index, ['Example / Ví dụ'], BOLD_FONT)
    row_index += 1
    write_instruction_row(sheet, row_index, PRODUCT_HEADERS, BOLD_FONT)
    row_index += 1
    write_instruction_row(sheet, row_index, [
        'USB-C Charger 65W', 'Charges laptops and phones', 25, 100, 'Laptop', 'Phone', '',
    ], text_widths=[20, 18, 46, 46, 10, 16, 16])
    sheet.cell(row=row_index, column=3).number_format = '#,##0.00'


def raise_file_error(message):
    raise ApiError('Validation failed', 422, {'file': [message]})


def is_blank_cell(value):
    return value is None or (isinstance(value, str) and not value.strip())


def read_import_rows(file_bytes):
    try:
        workbook = load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    # File hỏng hay sai định dạng làm openpyxl ném nhiều loại lỗi khác nhau
    except Exception:
        raise_file_error('File must be an .xlsx workbook')

    try:
        if PRODUCTS_SHEET_TITLE not in workbook.sheetnames:
            raise_file_error(f'Sheet "{PRODUCTS_SHEET_TITLE}" not found')
        rows = workbook[PRODUCTS_SHEET_TITLE].iter_rows(
            max_row=LAST_INPUT_ROW + 1, max_col=len(PRODUCT_HEADERS), values_only=True,
        )
        header = [str(value).strip() if value is not None else '' for value in next(rows, ())]
        if header != PRODUCT_HEADERS:
            raise_file_error(f'Header row must be: {", ".join(PRODUCT_HEADERS)}')

        raw_rows = []
        for row_number, values in enumerate(rows, start=2):
            if all(is_blank_cell(value) for value in values):
                continue
            if row_number > LAST_INPUT_ROW:
                raise_file_error(f'At most {MAX_IMPORT_ROWS} products per file')
            raw_rows.append((row_number, dict(zip(PRODUCT_HEADERS, values))))
    finally:
        workbook.close()

    if not raw_rows:
        raise_file_error('No products to import')
    return raw_rows


def convert_import_row(raw_row, categories_by_name):
    payload = {}
    for header in ('name', 'description'):
        value = raw_row.get(header)
        if not is_blank_cell(value):
            payload[header] = value if isinstance(value, str) else str(value)
    for header in ('price', 'quantity'):
        value = raw_row.get(header)
        if not is_blank_cell(value):
            is_whole_float = isinstance(value, float) and value.is_integer()
            payload[header] = int(value) if is_whole_float else value

    categories = []
    errors = {}
    for header in CATEGORY_HEADERS:
        value = raw_row.get(header)
        if is_blank_cell(value):
            continue
        category_name = str(value).strip()
        category = categories_by_name.get(category_name.lower())
        if category is None:
            errors[header] = [f'Unknown category: {category_name}']
        elif category not in categories:
            categories.append(category)
    return payload, categories, errors


def build_export_filename(export_date):
    # Gắn ngày vào tên file (products_20261126.xlsx) để các lần tải không trùng tên
    date_text = export_date.strftime('%Y%m%d')
    return f'products_{date_text}.xlsx'


def build_export_row(product):
    # Một product có thể thuộc nhiều category, gộp tên lại thành một ô: "Laptop, Phone"
    category_names = []
    for category in product.categories:
        category_names.append(category.name)
    # Xếp theo ABC vì DB không hứa trả category theo thứ tự cố định,
    # không xếp thì mỗi lần export một product có thể ra thứ tự khác nhau
    category_names.sort()
    categories_text = ', '.join(category_names)

    # Thứ tự giá trị phải khớp thứ tự cột trong EXPORT_COLUMNS
    return [
        product.id,
        product.name,
        product.description,
        product.price,
        product.quantity,
        categories_text,
    ]


def build_products_export(products):
    # Tạo file Excel mới, chỉ dùng sheet có sẵn và đổi tên thành Products
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = PRODUCTS_SHEET_TITLE

    # Dòng 1: tiêu đề cột, in đậm, có màu nền và gạch chân
    for column_index, column in enumerate(EXPORT_COLUMNS, start=1):
        header_cell = sheet.cell(row=1, column=column_index, value=column['header'])
        header_cell.font = BOLD_FONT
        header_cell.fill = HEADER_FILL
        header_cell.border = THIN_BORDER
        # column_letter là chữ cái của cột (A, B, C...), cần nó để đặt độ rộng cột
        sheet.column_dimensions[header_cell.column_letter].width = column['width']

    # Từ dòng 2 trở đi: mỗi product một dòng
    row_index = 2
    for product in products:
        values = build_export_row(product)
        for column_index, column in enumerate(EXPORT_COLUMNS, start=1):
            value = values[column_index - 1]
            cell = sheet.cell(row=row_index, column=column_index, value=value)
            cell.font = BODY_FONT
            if column['number_format']:
                cell.number_format = column['number_format']
            # openpyxl tự coi chuỗi bắt đầu bằng "=" là công thức. Ai đó đặt tên
            # product là "=HYPERLINK(...)" thì Excel sẽ chạy nó khi mở file.
            # Ép ô chữ về kiểu text ('s') để Excel chỉ hiện ra, không chạy.
            if isinstance(value, str):
                cell.data_type = 's'
        row_index += 1

    # Giữ dòng tiêu đề đứng yên khi cuộn xuống
    sheet.freeze_panes = 'A2'

    # Lưu file vào bộ nhớ (BytesIO) thay vì ghi ra ổ đĩa.
    # seek(0): đưa vị trí đọc về đầu, để send_file đọc từ byte đầu tiên.
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream
