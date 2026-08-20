from core.access import access_is_authenticated, logout, verify_access_password


def test_access_password_requires_a_configured_secret() -> None:
    assert not verify_access_password("", "")
    assert not verify_access_password("anything", "")
    assert verify_access_password("private", "private")
    assert not verify_access_password("Private", "private")


def test_logout_removes_session_access() -> None:
    state = {"abayo_access_authenticated": True}
    assert access_is_authenticated(state)

    logout(state)

    assert not access_is_authenticated(state)
