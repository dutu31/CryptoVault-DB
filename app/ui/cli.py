from app.db.init_db import initialize_database
from app.repositories.algorithm_repo import AlgorithmRepository
from app.repositories.framework_repo import FrameworkRepository
from app.services.openssl_service import check_openssl_available


def print_menu() -> None:
    print("\n=== Crypto Key Manager ===")
    print("1. Initialize database")
    print("2. List algorithms")
    print("3. List frameworks")
    print("4. Check OpenSSL")
    print("0. Exit")


def run_cli() -> None:
    algorithm_repo = AlgorithmRepository()
    framework_repo = FrameworkRepository()

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            initialize_database()
            print("Database initialized successfully.")

        elif choice == "2":
            algorithms = algorithm_repo.get_all()
            if not algorithms:
                print("No algorithms found. Initialize the database first.")
            else:
                print("\nAlgorithms:")
                for algorithm in algorithms:
                    print(
                        f"- [{algorithm.id}] {algorithm.name} | "
                        f"type={algorithm.type} | active={algorithm.is_active}"
                    )

        elif choice == "3":
            frameworks = framework_repo.get_all()
            if not frameworks:
                print("No frameworks found. Initialize the database first.")
            else:
                print("\nFrameworks:")
                for framework in frameworks:
                    print(
                        f"- [{framework.id}] {framework.name} | "
                        f"version={framework.version} | notes={framework.notes}"
                    )

        elif choice == "4":
            ok, message = check_openssl_available()
            if ok:
                print(f"OpenSSL found: {message}")
            else:
                print(f"OpenSSL not available: {message}")

        elif choice == "0":
            print("Exiting application.")
            break

        else:
            print("Invalid option. Try again.")