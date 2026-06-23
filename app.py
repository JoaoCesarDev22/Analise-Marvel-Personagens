import json
import random
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

try:
    from flask import Flask, jsonify, render_template
except ModuleNotFoundError:
    Flask = None
    jsonify = None
    render_template = None


BASE_DIR = Path(__file__).resolve().parent
DADOS_PATH = BASE_DIR / "marvel_dados.json"


def carregar_herois():
    if not DADOS_PATH.exists():
        return []
    try:
        dados = json.loads(DADOS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(dados, list):
        return []
    return [
        item
        for item in dados
        if isinstance(item, dict)
        and item.get("nome")
        and item.get("url_imagem")
    ]


def heroi_aleatorio():
    herois = carregar_herois()
    if not herois:
        return None
    return random.choice(herois)


def renderizar_template_simples(nome_template, contexto=None):
    caminho = BASE_DIR / "templates" / nome_template
    conteudo = caminho.read_text(encoding="utf-8")
    contexto = contexto or {}
    for chave, valor in contexto.items():
        serializado = json.dumps(valor, ensure_ascii=False)
        conteudo = conteudo.replace(f"{{{{ {chave} | tojson }}}}", serializado)
        conteudo = conteudo.replace(f"{{{{{chave}|tojson}}}}", serializado)
    return conteudo.encode("utf-8")


def obter_porta():
    if len(sys.argv) > 1:
        try:
            porta = int(sys.argv[1])
        except ValueError:
            porta = 5000
        return max(1024, min(65535, porta))
    return 5000


def porta_disponivel(porta_inicial):
    for porta in range(porta_inicial, min(65535, porta_inicial + 20) + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as teste:
            teste.settimeout(0.2)
            if teste.connect_ex(("127.0.0.1", porta)) == 0:
                continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", porta))
            except OSError:
                continue
            return porta
    return porta_inicial


class ServidorMarvel(BaseHTTPRequestHandler):
    def do_GET(self):
        caminho = urlparse(self.path).path
        if caminho == "/":
            self.responder(renderizar_template_simples("index.html"))
            return
        if caminho == "/painel":
            self.responder(renderizar_template_simples("painel.html", {"herois": carregar_herois()}))
            return
        if caminho == "/api/random":
            personagem = heroi_aleatorio()
            if not personagem:
                corpo = json.dumps({"erro": "Base de dados indisponível"}, ensure_ascii=False).encode("utf-8")
                self.responder(corpo, "application/json; charset=utf-8", 503)
                return
            corpo = json.dumps(personagem, ensure_ascii=False).encode("utf-8")
            self.responder(corpo, "application/json; charset=utf-8")
            return
        self.responder("Não encontrado".encode("utf-8"), "text/plain; charset=utf-8", 404)

    def responder(self, corpo, tipo="text/html; charset=utf-8", status=200):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, formato, *argumentos):
        return


if Flask:
    app = Flask(__name__)

    @app.route("/")
    def introducao():
        return render_template("index.html")

    @app.route("/painel")
    def painel():
        return render_template("painel.html", herois=carregar_herois())

    @app.route("/api/random")
    def aleatorio():
        personagem = heroi_aleatorio()
        if not personagem:
            return jsonify({"erro": "Base de dados indisponível"}), 503
        return jsonify(personagem)
else:
    app = None


def iniciar_servidor():
    porta_solicitada = obter_porta()
    porta = porta_disponivel(porta_solicitada)
    if porta != porta_solicitada:
        print(f"Porta {porta_solicitada} ocupada. Usando http://127.0.0.1:{porta}")
    if Flask:
        app.run(host="127.0.0.1", port=porta, debug=False)
        return
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), ServidorMarvel)
    print(f"Servidor disponível em http://127.0.0.1:{porta}")
    servidor.serve_forever()


if __name__ == "__main__":
    iniciar_servidor()
