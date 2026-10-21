"""Give admin access to an already registered user.

Usage (from the project folder):
    python scripts/make_admin.py user@example.com
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.repositories.user_repository import user_repository  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/make_admin.py <registered-email>")
        sys.exit(1)

    user = user_repository.get_by_email(sys.argv[1])
    if user is None:
        print("No user with that email. Register first from the app or /docs.")
        sys.exit(1)

    user_repository.set_role(user["id"], "admin")
    print(f"{user['name']} ({user['email']}) is now an admin. Login again to get an admin token.")


if __name__ == "__main__":
    main()
