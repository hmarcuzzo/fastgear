from fastapi import Query
from fastapi_pagination.links import Page


custom_page_query = Query(default=1, ge=1)
custom_size_query = Query(default=10, ge=1, le=100)

Page = Page.with_custom_options(
    page=custom_page_query,
    size=custom_size_query,
)
