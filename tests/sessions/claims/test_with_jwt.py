import json

from fastapi import FastAPI
from fastapi.requests import Request
from pytest import fixture
from starlette.testclient import TestClient

from supertokens_python import init
from supertokens_python.framework.fastapi import get_middleware
from supertokens_python.recipe.session import JWTConfig
from supertokens_python.recipe.session.asyncio import (
    create_new_session,
    get_session_information,
    validate_claims_in_jwt_payload,
)
from supertokens_python.recipe.session.exceptions import ClaimValidationError
from supertokens_python.recipe.session.interfaces import ValidateClaimsOkResult
from supertokens_python.utils import utf_base64decode
from tests.sessions.claims.utils import get_st_init_args, NoneClaim, TrueClaim
from tests.utils import setup_function, teardown_function, start_st, min_api_version

_ = setup_function  # type:ignore
_ = teardown_function  # type:ignore


@fixture(scope="function")
async def fastapi_client():
    app = FastAPI()
    app.add_middleware(get_middleware())

    @app.post("/create")
    async def create_api(request: Request):  # type: ignore
        user_id = "userId"
        s = await create_new_session(request, user_id, {}, {})
        return {"session_handle": s.get_handle()}

    return TestClient(app)


@min_api_version("2.9")
async def test_should_create_the_right_access_token_payload_with_claims_and_JWT_enabled(
    fastapi_client: TestClient,
):
    init(**get_st_init_args(TrueClaim, jwt=JWTConfig(enable=True)))  # type:ignore
    start_st()

    create_res = fastapi_client.post(url="/create")
    session_handle = create_res.json()["session_handle"]

    session_info = await get_session_information(session_handle)
    assert session_info is not None
    access_token_payload = session_info.access_token_payload
    # TODO: .sub and .iss should be undefined as per node PR
    assert access_token_payload["jwt"] is not None
    assert access_token_payload["_jwtPName"] == "jwt"

    decoded_jwt = json.loads(utf_base64decode(access_token_payload["jwt"]))
    assert decoded_jwt == {
        "sub": "userId",
        "iss": "https://api.supertokens.io/auth",
        "_jwtPName": None,
    }

    assert TrueClaim.get_value_from_payload(access_token_payload) is True
    assert TrueClaim.get_value_from_payload(decoded_jwt) is True

    failing_validator = NoneClaim.validators.has_value(True)
    res = await validate_claims_in_jwt_payload(
        session_info.user_id,
        decoded_jwt,
        lambda _, __, ___: [
            TrueClaim.validators.has_fresh_value(True, 2),
            failing_validator,
        ],
    )

    assert isinstance(res, ValidateClaimsOkResult)
    assert res.invalid_claims == [
        ClaimValidationError(
            failing_validator.id,
            {"actualValue": None, "expectedValue": True, "message": "wrong value"},
        )
    ]
