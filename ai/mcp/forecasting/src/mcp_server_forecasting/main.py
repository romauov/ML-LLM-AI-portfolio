import click

from server import serve


@click.command()
@click.option("--url", type=str, help="адрес сервера с прогнозатором")
@click.option("--port", type=str, required=True, help="порт")
@click.option("--user", type=str, required=True, help="имя пользователя для http авторизации")
@click.option("--password", type=str, required=True, help="пароль пользователя для http авторизации")
def main(url, port, user, password) -> None:
    import asyncio

    asyncio.run(serve(f'{url}:{port}', user, password))


if __name__ == "__main__":
    main()
