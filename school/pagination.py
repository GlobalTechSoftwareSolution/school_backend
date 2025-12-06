from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class that supports page_size parameter
    """
    page_size_query_param = 'page_size'
    max_page_size = 100