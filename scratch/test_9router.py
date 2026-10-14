import urllib.request
import json

url = "http://localhost:20128/v1/chat/completions"
api_key = "sk-4c63780906a3c8d8-de7pfy-33201f8c"

payload = {
    "model": "arsenal",
    "messages": [
        {"role": "system", "content": "Você é um diretor de documentário. Responda exclusivamente em JSON válido."},
        {"role": "user", "content": "Gere um JSON com o campo 'status': 'sucesso' e 'tema': 'Pompeia'."}
    ],
    "stream": False
}

req = urllib.request.Request(
    url,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    },
    data=json.dumps(payload).encode("utf-8")
)

try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
        print("RESPOSTA RECEBIDA:")
        content = data["choices"][0]["message"]["content"]
        print(content)
        print("\nSUCESSO TOTAL NA CONEXÃO COM 9ROUTER!")
except Exception as e:
    print("ERRO:", e)
