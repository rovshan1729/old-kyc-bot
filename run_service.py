import subprocess
import sys
import os
import signal
import time
fastapi_path = os.path.join(os.path.dirname(__file__), "backend/main.py")
print("fastapi", fastapi_path)
bot_path = os.path.join(os.path.dirname(__file__), "Verifier_bot/main.py")
print("bot_path", bot_path)


def start_fastapi():
    """Запуск FastAPI приложения."""
    fastapi_path = os.path.join(os.path.dirname(__file__), "backend/main.py")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=os.path.dirname(fastapi_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process


def start_bot():
    """Запуск Telegram-бота."""
    bot_path = os.path.join(os.path.dirname(__file__), "Verifier_bot/main.py")  # Измените, если бот в другом файле
    process = subprocess.Popen(
        [sys.executable, bot_path],
        cwd=os.path.dirname(bot_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process


def main():
    print("Запуск сервиса: FastAPI и Telegram-бот...")

    # Запуск процессов
    fastapi_process = start_fastapi()
    bot_process = start_bot()

    def signal_handler(sig, frame):
        print("\nОстановка сервиса...")
        if fastapi_process:
            fastapi_process.terminate()
        if bot_process:
            bot_process.terminate()
        sys.exit(0)

    # Обработка сигнала прерывания (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    # Мониторинг вывода процессов (опционально, для отладки)
    while True:
        time.sleep(1)
        if fastapi_process.poll() is not None or bot_process.poll() is not None:
            print("Один из процессов завершился. Остановка сервиса...")
            if fastapi_process.poll() is not None:
                print(f"FastAPI завершился с кодом {fastapi_process.poll()}")
            if bot_process.poll() is not None:
                print(f"Бот завершился с кодом {bot_process.poll()}")
            fastapi_process.terminate()
            bot_process.terminate()
            break


if __name__ == "__main__":
    main()