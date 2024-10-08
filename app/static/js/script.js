document.addEventListener("DOMContentLoaded", function() {
    const startBotButton = document.getElementById("start-bot-btn");
    const stopBotButton = document.getElementById("stop-bot-btn");
    const statusElement = document.getElementById("status");
    const removeKeywordButtons = document.querySelectorAll(".remove-keyword-btn");

    // Função para verificar o status do bot periodicamente
    async function atualizarStatusBot() {
        try {
            const response = await fetch('/status_bot', { method: 'GET' });
            const result = await response.json();
            statusElement.textContent = 'Status: ' + result.status;
        } catch (error) {
            console.error("Erro ao verificar o status do bot:", error);
            statusElement.textContent = 'Status: Erro ao verificar o status';
        }
    }

    // Atualiza o status do bot a cada 10 segundos
    setInterval(atualizarStatusBot, 10000); // 10 segundos

    // Atualiza o status imediatamente ao carregar a página
    atualizarStatusBot();

    // Função para iniciar o bot
    if (startBotButton) {
        startBotButton.addEventListener("click", async function() {
            try {
                const response = await fetch('/start_bot', { method: 'POST' });
                const result = await response.json();
                statusElement.textContent = 'Status: ' + result.status;

                // Verifica imediatamente o status após iniciar o bot
                atualizarStatusBot();
            } catch (error) {
                console.error("Erro ao iniciar o bot:", error);
                statusElement.textContent = 'Status: Erro ao iniciar o bot';
            }
        });
    }

    // Função para parar o bot
    if (stopBotButton) {
        stopBotButton.addEventListener("click", async function() {
            try {
                const response = await fetch('/stop_bot', { method: 'POST' });
                const result = await response.json();
                statusElement.textContent = 'Status: ' + result.status;

                // Verifica imediatamente o status após parar o bot
                atualizarStatusBot();
            } catch (error) {
                console.error("Erro ao parar o bot:", error);
                statusElement.textContent = 'Status: Erro ao parar o bot';
            }
        });
    }

    // Função para remover palavras-chave de forma assíncrona
    removeKeywordButtons.forEach(button => {
        button.addEventListener("click", async function(event) {
            event.preventDefault();  // Evita o envio padrão do formulário

            const keywordId = this.getAttribute("data-keyword-id");

            try {
                const response = await fetch(`/remove_keyword/${keywordId}`, { method: 'POST' });
                const result = await response.json();

                if (result.status === 'success') {
                    // Remove a palavra-chave da interface
                    this.closest("div.keyword-chip").remove();
                } else {
                    alert('Erro ao remover a palavra-chave.');
                }
            } catch (error) {
                console.error("Erro ao remover a palavra-chave:", error);
            }
        });
    });
});
