from typing import Callable


def convert_dict_to_string(args: dict[str, int | float | str]) -> str:
    list_of_args: list[str] = []
    for arg, value in args.items():
        list_of_args.append(f"{arg}:{value}")
    return " ".join(list_of_args)


def convert_func_name_and_args_to_str(prefix: str, func: Callable, **kwargs) -> str:
    list_of_args: list[str] = []
    for arg, value in kwargs.items():
        list_of_args.append(f"{arg}:{value}")
    args_string = "-".join(list_of_args)

    return f"{prefix}/{func.__name__}/{args_string}"
