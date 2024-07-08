from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from pydantic import EmailStr
from shepherd_core import local_now

from shepherd_wsrv.api_user.models import User
from shepherd_wsrv.api_user.models import UserAuth
from shepherd_wsrv.api_user.models import UserOut
from shepherd_wsrv.api_user.models import UserUpdate
from shepherd_wsrv.api_user.utils_mail import MailEngine
from shepherd_wsrv.api_user.utils_mail import mail_engine
from shepherd_wsrv.api_user.utils_misc import active_user_is_admin
from shepherd_wsrv.api_user.utils_misc import calculate_hash
from shepherd_wsrv.api_user.utils_misc import calculate_password_hash
from shepherd_wsrv.api_user.utils_misc import current_active_user

router = APIRouter(prefix="/user", tags=["User"])


# ###############################################################
# Own Data Access
# ###############################################################


@router.get("", response_model=UserOut)
async def user_info(user: User = Depends(current_active_user)):
    return user


@router.patch("", response_model=UserOut)
async def update_user(update: UserUpdate, user: User = Depends(current_active_user)):
    """Update allowed user fields."""
    fields = update.model_dump(exclude_unset=True)
    new_email = fields.pop("email", None)
    if isinstance(new_email, str) and new_email != user.email:
        if await User.by_email(new_email) is not None:
            raise HTTPException(400, "Email already exists")
        user.update_email(new_email)
    user = user.model_copy(update=fields)
    await user.save()
    return user


@router.delete("")
async def delete_user(
    user: User = Depends(current_active_user),
) -> Response:
    """Delete current user."""
    await User.find_one(User.email == user.email).delete()
    return Response(status_code=204)


# ###############################################################
# Registration
# ###############################################################


@router.post("/register", response_model=UserOut)
async def user_registration(
    user_auth: UserAuth,
    user: User = Depends(current_active_user),
    active_user_is_admin: None = Depends(active_user_is_admin),
    mail_engine: MailEngine = Depends(mail_engine),
):
    """Create a new user."""
    user = await User.by_email(user_auth.email)
    if user is not None:
        raise HTTPException(409, "User with that email already exists")
    pw_hash = calculate_password_hash(user_auth.password)
    token_verification = calculate_hash(user_auth.email + str(local_now()))[:10]
    await mail_engine.send_verification_email(user_auth.email, token_verification)
    user = User(
        email=user_auth.email,
        password=pw_hash,
        token_verification=token_verification,
        disabled=True,
    )
    await user.create()
    return user


@router.post("/forgot-password")
async def forgot_password(
    email: EmailStr = Body(embed=True),
    mail_engine: MailEngine = Depends(mail_engine),
) -> Response:
    """Send password reset email."""
    user = await User.by_email(email)
    if user is None:
        return Response(status_code=200)
    user.token_pw_reset = calculate_hash(user.email + str(local_now()))[:10]
    await mail_engine.send_password_reset_email(email, user.token_pw_reset)
    await user.save()
    return Response(status_code=200)


@router.post("/reset-password", response_model=UserOut)
async def reset_password(
    token: str = Body(embed=True),
    password: str = Body(embed=True),
):
    """Reset user password from token value."""
    user = await User.by_reset_token(token)
    if user is None:
        raise HTTPException(404, "Invalid password reset token")
    user.password = calculate_password_hash(password)
    await user.save()
    return user


# ###############################################################
# Verification
# ###############################################################


# why does this endpoint exist???
# TODO remove endpoint
@router.post("/verify")
async def request_verification_email(
    email: EmailStr = Body(embed=True),
    mail_engine: MailEngine = Depends(mail_engine),
) -> Response:
    """Send the user a verification email."""
    user = await User.by_email(email)
    if user is None:
        raise HTTPException(404, "No user found with that email")
    if user.email_confirmed_at is not None:
        raise HTTPException(409, "Email is already verified")
    user.token_verification = calculate_hash(user.email + str(local_now()))[:10]
    await mail_engine.send_verification_email(email, user.token_verification)
    await user.save()
    return Response(status_code=200)


@router.post("/verify/{token}")
async def verify_email(token: str) -> Response:
    """Verify the user's email with the supplied token."""
    user = await User.by_verification_token(token)
    if user is None:
        raise HTTPException(404, "Token not found")
    if user.email_confirmed_at is not None:
        # This should never happen,
        # because no verification token can be generated for verified accounts
        raise HTTPException(412, "Email is already verified")
    user.email_confirmed_at = local_now()
    user.token_verification = None
    await user.save()
    return Response(status_code=200)

@router.post("/approve")
async def approve(
    active_user_is_admin: None = Depends(active_user_is_admin),
    email: EmailStr = Body(embed=True),
):
    user = await User.by_email(email)
    if user is None:
        return Response(status_code=404)
    user.disabled = False
    await user.save()
    return Response(status_code=200)
