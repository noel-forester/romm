from fastapi import UploadFile
from fastapi.param_functions import Form
from pydantic import BaseModel


class UserForm(BaseModel):
    username: str | None = None
    password: str | None = None
    email: str | None = None
    role: str | None = None
    enabled: bool | None = None
    ra_username: str | None = None
    avatar: UploadFile | None = None


class OAuth2RequestForm:
    def __init__(
        self,
        grant_type: str = Form(default="password"),
        scope: str = Form(default=""),
        username: str | None = Form(default=None),
        password: str | None = Form(default=None),
        client_id: str | None = Form(default=None),
        client_secret: str | None = Form(default=None),
        refresh_token: str | None = Form(default=None),
    ):
        self.grant_type = grant_type
        self.scopes = scope.split()
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
