def pascal_to_snake(pascal: str) -> str:
    snake = ""
    for i, char in enumerate(pascal):
        if ord(char) >= ord("A") and ord(char) <= ord("Z"):
            if i > 0:
                snake += "_"
            snake += char.lower()
            continue
        snake += char
    return snake
