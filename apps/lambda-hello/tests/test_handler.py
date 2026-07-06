from lambda_hello.handler import handler


def test_handler_returns_greeting() -> None:
    result = handler({}, None)
    assert result["statusCode"] == 200
    assert result["body"] == "Hello, world!"
