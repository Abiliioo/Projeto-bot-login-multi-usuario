document.addEventListener("DOMContentLoaded", function() {
    const startBotButton = document.getElementById("start-bot-btn");
    const stopBotButton = document.getElementById("stop-bot-btn");
    const statusElement = document.getElementById("status");
    const removeKeywordButtons = document.querySelectorAll(".remove-keyword-btn");

    // Função para iniciar o bot
    if (startBotButton) {
        startBotButton.addEventListener("click", async function() {
            const response = await fetch('/start_bot', {method: 'POST'});
            const result = await response.json();
            statusElement.textContent = 'Status: ' + result.status;
        });
    }

    // Função para parar o bot
    if (stopBotButton) {
        stopBotButton.addEventListener("click", async function() {
            const response = await fetch('/stop_bot', {method: 'POST'});
            const result = await response.json();
            statusElement.textContent = 'Status: ' + result.status;
        });
    }

    // Função para remover palavras-chave de forma assíncrona
    removeKeywordButtons.forEach(button => {
        button.addEventListener("click", async function(event) {
            event.preventDefault();  // Evita o envio padrão do formulário

            const keywordId = this.getAttribute("data-keyword-id");

            const response = await fetch(`/remove_keyword/${keywordId}`, { method: 'POST' });
            const result = await response.json();

            if (result.status === 'success') {
                // Remove a palavra-chave da interface
                this.closest("div.keyword-chip").remove();
            } else {
                alert('Erro ao remover a palavra-chave.');
            }
        });
    });
});
