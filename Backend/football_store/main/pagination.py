from rest_framework.pagination import CursorPagination

class ProductPaginateCursor(CursorPagination):

    page_size = 20  # сколько объектов на страницу
    ordering = "-created_at"  # поле сортировки
    page_size_query_param = None  # можно разрешить менять размер
    max_page_size = None  # максимум объектов
    cursor_query_param = "cursor"  # имя параметра в URL