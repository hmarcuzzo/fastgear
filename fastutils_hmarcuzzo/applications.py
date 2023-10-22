from typing import List

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from fastutils_hmarcuzzo.handlers.http_exceptions_handler import HttpExceptionsHandler


UTILS_CALLABLES = {
    "http_exceptions_handler": lambda app: HttpExceptionsHandler(app),
    "pagination": lambda app: add_pagination(app),
}


def apply_utils(app: FastAPI, utils: List[str]):
    for util in utils:
        try:
            UTILS_CALLABLES[util](app)
        except KeyError:
            print(f"Utils {util} does not exist")
