from django.core.exceptions import ValidationError

def validate_price(value):
    if value < 0:
        raise ValidationError("Цена не может быть отрицательной")


def validate_quantity(value):
    if value < 0:
        raise ValidationError("Товаров на складе не может быть меньше 0")