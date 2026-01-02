def clean_string_value(value):
    if not isinstance(value, str):
        return value
    return value.replace('"', "").strip()