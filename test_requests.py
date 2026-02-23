import requests


def main() -> None:
    url = "https://httpbin.org/post"
    payload = {"name": "test"}

    response = requests.post(url, json=payload)
    print(response.status_code)
    print(response.json())


if __name__ == "__main__":
    main()
