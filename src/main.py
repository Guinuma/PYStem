from separator import separate_audio


def show_menu():
    print("\n========== PYStem ==========")
    print("1. Separate audio")
    print("2. Exit")
    print("============================")


def main():
    print("Welcome to PYStem!")
    print("AI-powered music source separation")

    while True:
        show_menu()

        option = input("Choose an option: ").strip()

        if option == "1":
            audio_path = input("Enter audio file path: ").strip().strip('"')
            separate_audio(audio_path)

        elif option == "2":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()