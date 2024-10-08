import threading
import json
import random
from datetime import datetime
from lxml import html
import asyncio
import aiohttp
from .models import User
from . import db

# Constantes e Configurações
URL_BASE = "https://www.99freelas.com.br/projects?page="
MENSAGEM_BASE = "Os seguintes projetos foram encontrados:\n\n"
INTERVALO_MIN = 2 * 60  # 2 minutos
INTERVALO_MAX = 5 * 60  # 5 minutos
ARQUIVO_PROJETOS = 'projetos_enviados.json'


class VerificadorDeProjetos:
    def __init__(self):
        self.deve_continuar = False
        self.projetos_enviados = self.carregar_projetos_enviados()
        self.logs = []  # Armazena logs
        self.thread = None
        self.bot_ativo = False  # Adicionando um estado para o status do bot

    def carregar_projetos_enviados(self):
        """
        Carrega os projetos já enviados de um arquivo JSON para evitar duplicidade.
        """
        try:
            with open(ARQUIVO_PROJETOS, 'r', encoding='utf-8') as json_file:
                return set(json.load(json_file))
        except FileNotFoundError:
            return set()
        except Exception as e:
            self.logs.append(f"Erro ao carregar projetos enviados: {e}")
            return set()

    def salvar_projetos_enviados(self):
        """
        Salva os projetos já enviados em um arquivo JSON.
        """
        try:
            with open(ARQUIVO_PROJETOS, 'w', encoding='utf-8') as json_file:
                json.dump(list(self.projetos_enviados), json_file, ensure_ascii=False)
        except Exception as e:
            self.logs.append(f"Erro ao salvar projetos enviados: {e}")

    async def obter_titulos_links_projetos(self, page, session):
        """
        Busca os títulos e links dos projetos na página específica.
        """
        try:
            async with session.get(f"{URL_BASE}{page}") as response:
                tree = html.fromstring(await response.text())
                titulos = tree.xpath('//h1[@class="title"]/a/text()')
                links = tree.xpath('//h1[@class="title"]/a/@href')
                return list(zip(titulos, links))
        except Exception as e:
            self.logs.append(f"Erro ao obter projetos da página {page}: {e}")
            return []

    def projeto_corresponde(self, titulo_projeto, keywords):
        """
        Verifica se o título do projeto contém alguma das palavras-chave do usuário.
        """
        return any(keyword.lower() in titulo_projeto.lower() for keyword in keywords)

    async def enviar_mensagem_telegram(self, texto, bot_token, chat_id):
        """
        Envia uma mensagem para o Telegram usando aiohttp.
        """
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

    async def verificar_e_salvar_chat_id(self, phone_number, chat_id):
        """
        Verifica se o número de telefone é de um assinante e salva o chat_id.
        """
        user = User.query.filter_by(phone_number=phone_number, is_subscriber=True).first()
        if user:
            user.chat_id = chat_id
            db.session.commit()
            self.logs.append(f"Chat ID salvo para o assinante: {user.username}")
            return True
        else:
            self.logs.append(f"Usuário com telefone {phone_number} não é assinante.")
            return False

    async def executar_verificacao(self, total_pages, keywords, bot_token, chat_id):
        """
        Executa a verificação dos projetos em várias páginas e envia notificações.
        """
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

    def run_schedule(self, total_pages, keywords, bot_token, chat_id):
        """
        Executa a verificação em intervalos aleatórios.
        """
        while self.deve_continuar:
            intervalo_aleatorio = random.randint(INTERVALO_MIN, INTERVALO_MAX)
            asyncio.run(self.executar_verificacao(total_pages, keywords, bot_token, chat_id))
            threading.Event().wait(intervalo_aleatorio)

    def iniciar_verificacao(self, total_pages, keywords, bot_token, chat_id):
        """
        Inicia a verificação em uma thread separada.
        """
        self.deve_continuar = True
        self.bot_ativo = True  # Define o bot como ativo
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run_schedule, args=(total_pages, keywords, bot_token, chat_id))
            self.thread.start()

    def parar_verificacao(self):
        """
        Para a verificação.
        """
        self.deve_continuar = False
        self.bot_ativo = False  # Define o bot como inativo
        if self.thread:
            self.thread.join()

    def status_bot(self):
        """
        Retorna o status do bot (ativo ou inativo).
        """
        return 'Ativo' if self.bot_ativo else 'Verificação não iniciada'
