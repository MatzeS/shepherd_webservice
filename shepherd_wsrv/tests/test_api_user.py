from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from shepherd_wsrv.api_instance import app
from shepherd_wsrv.api_user.models import User
from shepherd_wsrv.api_user.utils_mail import MailEngine
from shepherd_wsrv.api_user.utils_mail import mail_engine
from shepherd_wsrv.api_user.utils_misc import calculate_password_hash
from shepherd_wsrv.db_instance import db_client


@pytest.fixture
async def database_for_tests():
    await db_client()

    await User.delete_all()

    user = User(
        email="user@test.com",
        password=calculate_password_hash("password"),
        first_name="first name",
        last_name="last name",
        disabled=False,
        email_confirmed_at=datetime.now(),
    )

    working_user = user.model_copy(deep=True)
    await User.insert_one(working_user)

    unconfirmed_user = user.model_copy(deep=True)
    unconfirmed_user.email = "unconfirmed_mail@test.com"
    unconfirmed_user.email_confirmed_at = None
    await User.insert_one(unconfirmed_user)

    disabled_user = user.model_copy(deep=True)
    disabled_user.email = "disabled@test.com"
    disabled_user.disabled = True
    await User.insert_one(disabled_user)


@pytest.fixture
def client(database_for_tests):
    with TestClient(app) as client:
        yield client


@pytest.fixture
def authenticated_client(client: TestClient):
    # TODO might be more elegant to rework this into a different setup structure/process
    # instead of using a simple fixture
    response = client.post(
        "/auth/token",
        data={
            "username": "user@test.com",
            "password": "password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    client.headers["Authorization"] = f"Bearer {response.json()["access_token"]}"

    return client


def test_create_user_endpoint_requires_authentication(client: TestClient):
    response = client.post(
        "/user/register",
        json={
            "email": "new@test.com",
            "password": "password",
        },
    )
    assert response.status_code == 401


class MockMailEngine(MailEngine):
    def __init__(self):
        self.send_verification_email = AsyncMock()
        self.send_password_reset_email = AsyncMock()


@pytest.fixture
def mail_engine_mock():
    mock = MockMailEngine()
    app.dependency_overrides[mail_engine] = lambda: mock
    return mock


def test_unprivileged_user_cannot_create_new_users(
    authenticated_client: TestClient,
    mail_engine_mock,
):
    response = authenticated_client.post(
        "/user/register",
        json={
            "email": "new@test.com",
            "password": "password",
        },
    )
    assert response.status_code == 403


def test_user_can_query_account_data(authenticated_client: TestClient):
    response = authenticated_client.get("/user")
    assert response.status_code == 200
    assert response.json()["email"] == "user@test.com"
    assert response.json()["first_name"] == "first name"
    assert response.json()["last_name"] == "last name"


def test_user_account_data_endpoint_is_authenticated(client: TestClient):
    response = client.get("/user")
    assert response.status_code == 401
