import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

API_BASE = "https://superheroapi.com/api/6318534121509930"
ESPELHO_PUBLICO = "https://cdn.jsdelivr.net/gh/akabab/superhero-api@0.3.0/api/all.json"
TOTAL_REGISTROS = 731
MAX_WORKERS = 18
TIMEOUT = 16
SAIDA = Path(__file__).with_name("marvel_dados.json")


def requisitar_json(url):
    pedido = Request(url, headers={"User-Agent": "MCU-Dashboard-Academico/1.0"})
    with urlopen(pedido, timeout=TIMEOUT) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def limpar_texto(valor, padrao="Não informado"):
    if isinstance(valor, list):
        valor = ", ".join(str(item) for item in valor if item and item != "-")
    if valor is None:
        return padrao
    texto = str(valor).strip()
    if not texto or texto == "-" or texto.lower() in {"null", "none"}:
        return padrao
    return texto


def pegar(dicionario, *chaves):
    for chave in chaves:
        if isinstance(dicionario, dict) and chave in dicionario:
            valor = dicionario[chave]
            if valor not in (None, "", "-"):
                return valor
    return None


def numero_poder(valor):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, numero))


def traduzir_alinhamento(valor):
    valor = limpar_texto(valor, "").lower()
    if valor == "good":
        return "Herói"
    if valor == "bad":
        return "Vilão"
    return "Neutro"


def url_imagem_valida(url):
    texto = limpar_texto(url, "")
    partes = urlparse(texto)
    if partes.scheme not in {"http", "https"} or not partes.netloc:
        return False
    caminho = partes.path.lower()
    if "image_not_available" in caminho:
        return False
    return caminho.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))


def detectar_equipe(dados):
    conexoes = dados.get("connections", {})
    grupos = limpar_texto(pegar(conexoes, "group-affiliation", "groupAffiliation"), "").lower()
    nome = limpar_texto(dados.get("name"), "").lower()
    referencias = f"{grupos} {nome}"
    mapas = [
        ("Vingadores", ["avengers", "new avengers", "secret avengers", "west coast avengers"]),
        ("X-Men", ["x-men", "x-force", "x-factor", "brotherhood of evil mutants", "mutants"]),
        ("Guardiões da Galáxia", ["guardians of the galaxy", "ravagers"]),
        ("Quarteto Fantástico", ["fantastic four", "future foundation"]),
        ("S.H.I.E.L.D.", ["s.h.i.e.l.d", "shield", "howling commandos"]),
        ("Defensores", ["defenders", "heroes for hire"]),
        ("Inumanos", ["inhumans"]),
        ("Thunderbolts", ["thunderbolts"]),
        ("Simbiontes", ["symbiote", "venom"]),
        ("Vilões Marvel", ["sinister", "masters of evil", "hydra", "aim", "brotherhood"]),
    ]
    for equipe, termos in mapas:
        if any(termo in referencias for termo in termos):
            return equipe
    return "Marvel"


def montar_descricao(dados, equipe):
    bio = dados.get("biography", {})
    trabalho = dados.get("work", {})
    conexoes = dados.get("connections", {})
    nome = limpar_texto(dados.get("name"))
    real = limpar_texto(pegar(bio, "full-name", "fullName"), nome)
    estreia = limpar_texto(pegar(bio, "first-appearance", "firstAppearance"), "")
    origem = limpar_texto(pegar(bio, "place-of-birth", "placeOfBirth"), "")
    ocupacao = limpar_texto(pegar(trabalho, "occupation"), "")
    base = limpar_texto(pegar(trabalho, "base"), "")
    afiliacao = limpar_texto(pegar(conexoes, "group-affiliation", "groupAffiliation"), equipe)
    partes = [f"{nome} tem identidade registrada como {real} e aparece associado a {equipe} no universo Marvel."]
    if estreia:
        partes.append(f"Primeira aparição registrada: {estreia}.")
    if origem:
        partes.append(f"Origem: {origem}.")
    if ocupacao:
        partes.append(f"Atuação principal: {ocupacao}.")
    if base:
        partes.append(f"Base conhecida: {base}.")
    if afiliacao and afiliacao != equipe:
        partes.append(f"Afiliações citadas: {afiliacao}.")
    return " ".join(partes)


def extrair_imagem(dados):
    imagem_api = pegar(dados.get("image", {}), "url")
    imagem_espelho = pegar(dados.get("images", {}), "lg", "md", "sm", "xs")
    return limpar_texto(imagem_api or imagem_espelho, "")


def consolidar_dados(dados, indice=None):
    if dados.get("response") == "error":
        return None

    bio = dados.get("biography", {})
    publisher = limpar_texto(pegar(bio, "publisher"), "")
    if "marvel" not in publisher.lower():
        return None

    imagem = extrair_imagem(dados)
    if not url_imagem_valida(imagem):
        return None

    equipe = detectar_equipe(dados)
    stats = dados.get("powerstats", {})
    nome = limpar_texto(dados.get("name"))
    real_name = limpar_texto(pegar(bio, "full-name", "fullName"), nome)

    return {
        "id": int(dados.get("id") or indice),
        "nome": nome,
        "real_name": real_name,
        "alinhamento": traduzir_alinhamento(pegar(bio, "alignment")),
        "equipe": equipe,
        "descricao": montar_descricao(dados, equipe),
        "forca": numero_poder(pegar(stats, "strength")),
        "inteligencia": numero_poder(pegar(stats, "intelligence")),
        "velocidade": numero_poder(pegar(stats, "speed")),
        "durabilidade": numero_poder(pegar(stats, "durability")),
        "url_imagem": imagem,
    }


def consolidar_personagem_api(indice):
    try:
        dados = requisitar_json(f"{API_BASE}/{indice}")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as erro:
        return None, f"{indice}: falha na API ({erro})"

    if dados.get("response") != "success":
        return None, None

    return consolidar_dados(dados, indice), None


def salvar(personagens, inicio, origem, falhas=None):
    falhas = falhas or []
    personagens.sort(key=lambda item: item["nome"].lower())
    SAIDA.write_text(json.dumps(personagens, ensure_ascii=False, indent=2), encoding="utf-8")
    duracao = time.perf_counter() - inicio
    print(f"{len(personagens)} personagens Marvel salvos em {SAIDA.name} via {origem} em {duracao:.1f}s.")
    if falhas:
        print(f"{len(falhas)} chamadas falharam, mas a base foi gerada com os registros válidos.")


def baixar_api_principal():
    personagens = []
    falhas = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tarefas = {executor.submit(consolidar_personagem_api, indice): indice for indice in range(1, TOTAL_REGISTROS + 1)}
        for tarefa in as_completed(tarefas):
            personagem, erro = tarefa.result()
            if personagem:
                personagens.append(personagem)
            if erro:
                falhas.append(erro)
    return personagens, falhas


def baixar_espelho_publico():
    dados = requisitar_json(ESPELHO_PUBLICO)
    personagens = []
    for item in dados:
        try:
            identificador = int(item.get("id") or 0)
        except (TypeError, ValueError):
            continue
        if 1 <= identificador <= TOTAL_REGISTROS:
            personagem = consolidar_dados(item, identificador)
            if personagem:
                personagens.append(personagem)
    return personagens


def baixar_personagens():
    inicio = time.perf_counter()
    try:
        teste = requisitar_json(f"{API_BASE}/1")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError):
        teste = {"response": "error", "error": "indisponível"}

    if teste.get("response") == "success":
        personagens, falhas = baixar_api_principal()
        if personagens:
            salvar(personagens, inicio, "endpoint principal", falhas)
            return

    personagens = baixar_espelho_publico()
    salvar(personagens, inicio, "mirror público", [])


if __name__ == "__main__":
    baixar_personagens()
