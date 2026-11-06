"""Pruebas de registro, inicio de sesión y perfil."""

from fastapi.testclient import TestClient


def _registrar(client: TestClient, email: str = "ana@taller.co"):
    return client.post(
        "/api/v1/auth/registro",
        json={"nombre": "Ana", "email": email, "password": "clave-segura-1"},
    )


def test_registro_devuelve_token_y_usuario(client: TestClient) -> None:
    respuesta = _registrar(client, "Ana@Taller.co")

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["usuario"]["email"] == "ana@taller.co"
    assert cuerpo["usuario"]["rol"] == "EMPRESA"
    assert cuerpo["usuario"]["empresa_id"] is None
    assert "password" not in str(cuerpo["usuario"])


def test_registro_con_correo_repetido_responde_409(client: TestClient) -> None:
    _registrar(client)
    respuesta = _registrar(client, "ANA@taller.co")

    assert respuesta.status_code == 409


def test_registro_valida_password_corta(client: TestClient) -> None:
    respuesta = client.post(
        "/api/v1/auth/registro", json={"nombre": "Ana", "email": "a@b.co", "password": "123"}
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["detalles"][0]["campo"] == "body.password"


def test_login_correcto_e_incorrecto(client: TestClient) -> None:
    _registrar(client)

    ok = client.post(
        "/api/v1/auth/login", json={"email": "ana@taller.co", "password": "clave-segura-1"}
    )
    mal = client.post(
        "/api/v1/auth/login", json={"email": "ana@taller.co", "password": "otra-clave"}
    )

    assert ok.status_code == 200
    assert "access_token" in ok.cookies
    assert mal.status_code == 401
    assert mal.headers["www-authenticate"] == "Bearer"


def test_token_oauth2_para_swagger(client: TestClient) -> None:
    _registrar(client)

    respuesta = client.post(
        "/api/v1/auth/token", data={"username": "ana@taller.co", "password": "clave-segura-1"}
    )

    assert respuesta.status_code == 200


def test_perfil_requiere_sesion(client: TestClient) -> None:
    client.cookies.clear()
    assert client.get("/api/v1/usuarios/me").status_code == 401
    assert (
        client.get("/api/v1/usuarios/me", headers={"Authorization": "Bearer basura"}).status_code
        == 401
    )


def test_sesion_por_cookie_y_logout(client: TestClient) -> None:
    _registrar(client)

    assert client.get("/api/v1/usuarios/me").status_code == 200

    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/usuarios/me").status_code == 401


def test_actualizar_perfil_y_cambiar_password(client: TestClient, registrar) -> None:
    cabeceras = registrar()

    sin_actual = client.put(
        "/api/v1/usuarios/me", headers=cabeceras, json={"password_nueva": "nueva-clave-9"}
    )
    actual_mal = client.put(
        "/api/v1/usuarios/me",
        headers=cabeceras,
        json={"password_actual": "equivocada", "password_nueva": "nueva-clave-9"},
    )
    ok = client.put(
        "/api/v1/usuarios/me",
        headers=cabeceras,
        json={
            "nombre": "Ana María",
            "password_actual": "clave-segura-1",
            "password_nueva": "nueva-clave-9",
        },
    )

    assert sin_actual.status_code == 422
    assert actual_mal.status_code == 409
    assert ok.status_code == 200
    assert ok.json()["nombre"] == "Ana María"
    login = client.post(
        "/api/v1/auth/login", json={"email": "ana@taller.co", "password": "nueva-clave-9"}
    )
    assert login.status_code == 200


def test_listar_usuarios_solo_admin(client: TestClient, registrar) -> None:
    cabeceras = registrar()

    assert client.get("/api/v1/usuarios", headers=cabeceras).status_code == 403
