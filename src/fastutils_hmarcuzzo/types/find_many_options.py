from fastutils_hmarcuzzo.types.find_one_options import FindOneOptions


class FindManyOptions(FindOneOptions, total=False):
    skip: int
    take: int
