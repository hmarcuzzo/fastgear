from fastapi import Query
from fastapi_pagination.links import Page


Page = Page.with_custom_options(
    size=Query(default=10, ge=1, le=100),
)
