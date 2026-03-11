import subprocess


def check_openssl_available() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["openssl", "version"],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except Exception as exc:
        return False, str(exc)