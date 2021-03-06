## _FastAPI Chat_

## Docker Compose

By default, port 8000 will be exposed, so change this within the
Dockerfile and docker-compose.yml if necessary.

```sh
git clone https://github.com/shogath/fastapi_chat.git
cd fastapi_chat
docker-compose up
```
Verify the deployment by navigating to your server address in
your preferred browser.

```sh
127.0.0.1:8000
```

## _OR_

## Without docker

```sh
git clone https://github.com/shogath/fastapi_chat.git
cd fastapi_chat
pip3 install -r requirements.txt
cd src
uvicorn main:app --host 0.0.0.0 --port 8000
```

Verify the deployment by navigating to your server address in
your preferred browser.

```sh
127.0.0.1:8000
```