"""CLI Interactivo de IA para la Terminal (Local Ollama / OpenAI / ChatGPT).

Permite consultar tanto a tu IA local en GPU RTX 4080 (Ollama) como a OpenAI/ChatGPT.
Uso:
    python src/chat_cli.py
    python src/chat_cli.py "Tu pregunta directa aqui"
    python src/chat_cli.py --model qwen2.5-coder:7b
"""
import os
import sys
import json
import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_LOCAL_MODEL = "qwen2.5-coder:7b"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


def check_ollama_status():
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        if r.status_code == 200:
            models = [m.get("name") for m in r.json().get("models", [])]
            return True, models
    except Exception:
        pass
    return False, []


def query_ollama(prompt: str, model: str = DEFAULT_LOCAL_MODEL) -> str:
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    r = requests.post(url, json=payload, timeout=90)
    if r.status_code == 200:
        return r.json().get("response", "").strip()
    return f"Error Ollama ({r.status_code}): {r.text}"


def query_openai(prompt: str, api_key: str, model: str = "gpt-4o-mini") -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"].strip()
    return f"Error OpenAI ({r.status_code}): {r.text}"


def interactive_loop():
    is_ollama, models = check_ollama_status()
    print("=" * 60)
    print("🤖 TERMINAL IA CLI (Local GPU RTX 4080 / ChatGPT)")
    print("=" * 60)
    if is_ollama:
        print(f"✅ Motor Local: Ollama Activo en {OLLAMA_HOST}")
        print(f"📦 Modelos disponibles: {', '.join(models) if models else DEFAULT_LOCAL_MODEL}")
        selected_backend = "ollama"
        current_model = models[0] if models else DEFAULT_LOCAL_MODEL
    elif OPENAI_API_KEY:
        print("✅ Motor Cloud: OpenAI API Key detectada")
        selected_backend = "openai"
        current_model = "gpt-4o-mini"
    else:
        print("⚠️ Ollama no está escuchando y no hay OPENAI_API_KEY configurada.")
        print("💡 Iniciando intento con Ollama local...")
        selected_backend = "ollama"
        current_model = DEFAULT_LOCAL_MODEL

    print(f"⚙️ Modo activo: [{selected_backend.upper()}] Modelo: {current_model}")
    print("Comandos: '/exit' para salir, '/model <nombre>' para cambiar modelo, '/backend <ollama|openai>'")
    print("-" * 60)

    while True:
        try:
            user_input = input("\n👤 Tú > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("/exit", "exit", "quit", "/quit"):
                print("👋 ¡Hasta luego!")
                break
            if user_input.startswith("/model "):
                current_model = user_input.split(" ", 1)[1].strip()
                print(f"🔄 Modelo cambiado a: {current_model}")
                continue
            if user_input.startswith("/backend "):
                selected_backend = user_input.split(" ", 1)[1].strip().lower()
                print(f"🔄 Backend cambiado a: {selected_backend}")
                continue

            print(f"⏳ Procesando con [{selected_backend}]...", end="\r", flush=True)

            if selected_backend == "ollama":
                resp = query_ollama(user_input, model=current_model)
            else:
                key = OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
                if not key:
                    resp = "Error: Configura la variable de entorno OPENAI_API_KEY para usar ChatGPT."
                else:
                    resp = query_openai(user_input, api_key=key, model=current_model)

            print(" " * 40, end="\r")  # Limpiar estado de carga
            print(f"🤖 IA > {resp}")

        except (KeyboardInterrupt, EOFError):
            print("\n👋 Sesión terminada.")
            break


def main():
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        query = " ".join(sys.argv[1:])
        is_ollama, models = check_ollama_status()
        if is_ollama:
            model = models[0] if models else DEFAULT_LOCAL_MODEL
            print(query_ollama(query, model=model))
        elif OPENAI_API_KEY:
            print(query_openai(query, api_key=OPENAI_API_KEY))
        else:
            print(query_ollama(query, model=DEFAULT_LOCAL_MODEL))
    else:
        interactive_loop()


if __name__ == "__main__":
    main()
