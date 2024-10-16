import threading
import random
from lxml import html
import asyncio
import aiohttp
from .models import User, Project
from . import db
from app import create_app

# Constantes e Configurações
URL_BASE = "https://www.99freelas.com.br/projects?page="
MENSAGEM_BASE = "Os seguintes projetos foram encontrados:\n\n"
INTERVALO_MIN = 2 * 60  # 2 minutos
INTERVALO_MAX = 5 * 60  # 5 minutos

class VerificadorDeProjetos:
    def __init__(self):
        self.deve_continuar = False
        self.logs = []  # Armazena logs
        self.thread = None
        self.bot_ativo = False  # Estado do bot

    async def obter_titulos_links_projetos(self, page, session):
        """
        Busca os títulos, links, data de publicação e número de propostas dos projetos na página específica.
        """
        try:
            async with session.get(f"{URL_BASE}{page}") as response:
                tree = html.fromstring(await response.text())
                titulos = tree.xpath('//h1[@class="title"]/a/text()')
                links = tree.xpath('//h1[@class="title"]/a/@href')

                # Retorna uma lista de dicionários com as informações do projeto
                projetos = []
                for i in range(len(titulos)):
                    projetos.append({
                        "titulo": titulos[i],
                        "link": links[i]
                    })

                return projetos
        except Exception as e:
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
                    response_data = await response.json()
                    return response_data
            except aiohttp.ClientError as e:
                return None

    async def executar_verificacao(self, total_pages, keywords, bot_token, chat_id, user_id, app):
        """
        Executa a verificação dos projetos em várias páginas e envia notificações.
        """
        async with aiohttp.ClientSession() as session:
            for current_page in range(1, total_pages + 1):
                projetos = await self.obter_titulos_links_projetos(current_page, session)
                for projeto in projetos:
                    # Usa o contexto da aplicação Flask para garantir que as consultas ao banco funcionem
                    with app.app_context():
                        projeto_existente = Project.query.filter_by(link=projeto['link'], user_id=user_id).first()

                        if projeto_existente:
                            pass  # Projeto já existe, não fazer nada
                        elif self.projeto_corresponde(projeto['titulo'], keywords):
                            # Salvar no banco de dados
                            novo_projeto = Project(title=projeto['titulo'], link=projeto['link'], user_id=user_id)
                            db.session.add(novo_projeto)
                            db.session.commit()

                            # Formatar a mensagem do projeto
                            mensagem_final = (
                                f"📋 <b>Novo Projeto Encontrado:</b>\n\n"
                                f"🔖 <b>{projeto['titulo']}</b>\n\n"
                                f"🌐 <a href='https://www.99freelas.com.br{projeto['link']}'>Acessar Projeto</a>\n\n"
                                "\n--------------------------------------------------------"
                            )

                            # Enviar mensagem formatada via Telegram
                            await self.enviar_mensagem_telegram(mensagem_final, bot_token, chat_id)


    def run_schedule(self, total_pages, keywords, bot_token, chat_id, user_id):
        """
        Executa a verificação em intervalos aleatórios.
        """
        app = create_app()
        while self.deve_continuar:
            intervalo_aleatorio = random.randint(INTERVALO_MIN, INTERVALO_MAX)
            asyncio.run(self.executar_verificacao(total_pages, keywords, bot_token, chat_id, user_id, app))
            threading.Event().wait(intervalo_aleatorio)

    def iniciar_verificacao(self, total_pages, keywords, bot_token, chat_id, user_id):
        """
        Inicia a verificação em uma thread separada.
        """
        self.deve_continuar = True
        self.bot_ativo = True  # Define o bot como ativo
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run_schedule, args=(total_pages, keywords, bot_token, chat_id, user_id))
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

    @staticmethod
    def limpar_projetos_antigos():
        """
        Chama o método estático para excluir projetos mais antigos que 12 horas.
        """
        Project.delete_old_projects()
