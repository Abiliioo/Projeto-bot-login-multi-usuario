import threading
import json
import random
from datetime import datetime
from lxml import html
import requests
import asyncio
import aiohttp
import config
from flask import Flask, request, jsonify  # Importações necessárias
from .models import User  # Importa o modelo User para verificar assinantes
from . import db

# Criação da instância do Flask
app = Flask(__name__)

# Constantes e Configurações
URL_BASE = "https://www.99freelas.com.br/projects?page="
MENSAGEM_BASE = "Os seguintes projetos foram encontrados:\n\n"
INTERVALO_MIN = 2 * 60  # 2 minutos
INTERVALO_MAX = 5 * 60  # 5 minutos

class VerificadorDeProjetos:
    def __init__(self):
        self.deve_continuar = False
        self.projetos_enviados = self.carregar_projetos_enviados()
        self.logs = []  # Armazena logs
        self.thread = None

    # Carrega os projetos já enviados de um arquivo JSON
    def carregar_projetos_enviados(self):
        try:
            with open('projetos_enviados.json', 'r', encoding='utf-8') as json_file:
                return set(json.load(json_file))
        except FileNotFoundError:
            return set()
        except Exception as e:
            self.logs.append(f"Erro ao carregar projetos enviados: {e}")
            return set()

    # Salva os projetos enviados em um arquivo JSON
    def salvar_projetos_enviados(self):
        try:
            with open('projetos_enviados.json', 'w', encoding='utf-8') as json_file:
                json.dump(list(self.projetos_enviados), json_file, ensure_ascii=False)
        except Exception as e:
            self.logs.append(f"Erro ao salvar projetos enviados: {e}")

    # Busca e extrai os títulos e links dos projetos
    async def obter_titulos_links_projetos(self, page, session):
        try:
            async with session.get(URL_BASE + str(page)) as response:
                tree = html.fromstring(await response.text())
                titulos = tree.xpath('//h1[@class="title"]/a/text()')
                links = tree.xpath('//h1[@class="title"]/a/@href')
                return list(zip(titulos, links))
        except Exception as e:
            self.logs.append(f"Erro ao obter projetos da página {page}: {e}")
            return []

    # Verifica se o título do projeto contém alguma das palavras-chave do usuário
    def projeto_corresponde(self, titulo_projeto, keywords):
        return any(keyword.lower() in titulo_projeto.lower() for keyword in keywords)

    # Envia uma mensagem para o Telegram usando o aiohttp
    async def enviar_mensagem_telegram(self, texto, bot_token, chat_id):
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": texto,
            "parse_mode": "HTML"
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=payload) as response:
                    return await response.json()
            except aiohttp.ClientError as e:
                self.logs.append(f"Erro ao enviar mensagem: {e}")
                return None

    # Função para verificar se o usuário é assinante e salvar o chat_id
    async def verificar_e_salvar_chat_id(self, phone_number, chat_id):
        # Verifica se o número de telefone pertence a um assinante
        user = User.query.filter_by(phone_number=phone_number, is_subscriber=True).first()
        if user:
            # Se o usuário for assinante, salva o chat_id no banco de dados
            user.chat_id = chat_id
            db.session.commit()
            self.logs.append(f"Chat ID salvo para o assinante: {user.username}")
            return True
        else:
            self.logs.append(f"Usuário com telefone {phone_number} não é assinante.")
            return False

    # Executa a verificação dos projetos em várias páginas
    async def executar_verificacao(self, total_pages, keywords, bot_token, chat_id):
        self.logs.append("Iniciando verificação de projetos...")
        async with aiohttp.ClientSession() as session:
            for current_page in range(1, total_pages + 1):
                titulos_links = await self.obter_titulos_links_projetos(current_page, session)
                for titulo, link in titulos_links:
                    if self.projeto_corresponde(titulo, keywords) and link not in self.projetos_enviados:
                        mensagem_final = f"{MENSAGEM_BASE}{titulo}\n\nLink do projeto: https://www.99freelas.com.br{link}\n\n"
                        self.projetos_enviados.add(link)
                        self.logs.append(f"Projeto encontrado: {titulo}")
                        await self.enviar_mensagem_telegram(mensagem_final, bot_token, chat_id)

        self.salvar_projetos_enviados()
        self.logs.append("Verificação concluída.")

    # Função para executar a verificação em intervalos de tempo
    def run_schedule(self, total_pages, keywords, bot_token, chat_id):
        while self.deve_continuar:
            intervalo_aleatorio = random.randint(INTERVALO_MIN, INTERVALO_MAX)
            asyncio.run(self.executar_verificacao(total_pages, keywords, bot_token, chat_id))
            threading.Event().wait(intervalo_aleatorio)

    # Inicia a verificação em uma thread separada
    def iniciar_verificacao(self, total_pages, keywords, bot_token, chat_id):
        self.deve_continuar = True
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run_schedule, args=(total_pages, keywords, bot_token, chat_id))
            self.thread.start()

    # Para a verificação
    def parar_verificacao(self):
        self.deve_continuar = False
        if self.thread:
            self.thread.join()


# Webhook para capturar as interações do bot com o usuário
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if "message" in data:
        chat_id = data['message']['chat']['id']
        phone_number = data['message']['contact']['phone_number']  # Obtém o número de telefone se disponível

        # Verifica se o usuário com o número de telefone fornecido é um assinante
        verificador = VerificadorDeProjetos()
        if asyncio.run(verificador.verificar_e_salvar_chat_id(phone_number, chat_id)):
            return jsonify({"status": "Chat ID salvo com sucesso para o assinante."})
        else:
            return jsonify({"status": "Usuário não é assinante."})
    return jsonify({"status": "Erro: Nenhuma mensagem encontrada."})
