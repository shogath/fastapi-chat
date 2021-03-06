import jwt
import secrets
from passlib.hash import bcrypt
from datetime import datetime, timedelta

from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect, Request,
    Depends, HTTPException, status, Form
)

from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException

from tortoise.contrib.fastapi import register_tortoise

from helpers.socket_manager import SocketManager
from models.models import (
    User, Message, User_Pydantic,
    Message_Pydantic, MessageIn_Pydantic
)

# Generate secret for JWT token
# JWT_SECRET = secrets.token_hex(32)
JWT_SECRET = "my_secret_token"

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

manager = LoginManager(JWT_SECRET, tokenUrl="/auth/login", use_cookie=True)
manager.cookie_name = "Authorization"

# locate templates
templates = Jinja2Templates(directory="templates")

socket_helper = SocketManager()


# Get user by username from database
@manager.user_loader
async def load_user(username: str):
    user = await User.get(username=username)
    return user


# Get user from JWT token
async def get_current_user(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user = await User.get(username=payload.get('sub'))
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Invalid username or password')

    return await User_Pydantic.from_tortoise_orm(user)


@app.post("/auth/login")
async def login(data: OAuth2PasswordRequestForm = Depends()):
    username = data.username
    password = data.password

    # Get user from db
    user = await load_user(username)
    if not user:
        raise InvalidCredentialsException
    elif not user.verify_password(password):
        raise InvalidCredentialsException

    # Generate access token for the user and set expiration time to 2 hours
    access_token = manager.create_access_token(
        data={"sub": username},
        expires=timedelta(hours=2)
    )
    resp = RedirectResponse(url="/chat", status_code=status.HTTP_302_FOUND)

    # Set cookie with access token
    manager.set_cookie(resp, access_token)
    return resp


@app.post('/auth/signup')
async def create_user(username: str = Form(...), password: str = Form(...)):
    user_obj = User(username=username,
                    password_hash=bcrypt.hash(password))
    try:
        await user_obj.save()
    except:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT)

    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


@app.get("/logout")
async def route_logout_and_remove_cookie():
    response = RedirectResponse(url="/")
    response.delete_cookie("Authorization")
    return response


@app.get("/openapi.json")
async def get_open_api_endpoint(current_user: User = Depends(manager)):
    return JSONResponse(get_openapi(title="FastAPI", version=1, routes=app.routes))


@app.get("/docs")
async def get_documentation(current_user: User = Depends(manager)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get('/users/me')
async def get_user(user: User_Pydantic = Depends(manager)):
    return user.username


@app.get("/")
async def get_home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/signup")
async def get_home(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/chat")
async def get_chat(request: Request, user: User_Pydantic = Depends(manager)):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.get("/history")
async def get_history(message: Message_Pydantic = Depends(manager)):
    # TODO implement groups logic. Hardcode 'group_id' for now
    return await MessageIn_Pydantic.from_queryset(Message.filter(group_id=1))


@app.websocket("/api/chat")
async def chat(websocket: WebSocket):
    # Get current user from cookie
    user = await get_current_user(websocket.cookies.get('Authorization'))
    sender = user.username
    if sender:
        await socket_helper.connect(websocket, sender)
        response = {
            "time": datetime.now().strftime("%I:%M:%S %p"),
            "sender": sender,
            "message": "got connected"
        }
        # User connected message
        await socket_helper.broadcast(response)
        try:
            while True:
                # Message that user sent
                data = await websocket.receive_json()
                # TODO implement groups logic. Hardcode 'group_id' for now
                message_obj = Message(group_id=1,
                                      data=data)
                await socket_helper.broadcast(data)
                await message_obj.save()
        except WebSocketDisconnect:
            socket_helper.disconnect(websocket, sender)
            response['message'] = "disconnected"
            # User disconnected message
            await socket_helper.broadcast(response)


# Create database and generate schemas from models
register_tortoise(
    app,
    db_url='sqlite://../test.sqlite3',
    modules={'models': ['models.models']},
    generate_schemas=True,
    add_exception_handlers=True
)
