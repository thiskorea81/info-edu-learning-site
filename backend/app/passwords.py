"""표준 라이브러리만으로 만든 비밀번호 해시(pbkdf2-sha256).

교실 내 신뢰 관계를 전제로 한 4자리 숫자 비밀번호이므로 완벽한 방어가
목적은 아니지만, DB 파일을 열어 봐도 평문이 그대로 보이지 않도록 최소한의
안전장치를 둔다.
"""

import hashlib
import secrets

DEFAULT_PASSWORD = "1234"
_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$")
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS).hex()
    return secrets.compare_digest(check, digest)
