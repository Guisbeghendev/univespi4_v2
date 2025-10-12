// Script para carregar dinamicamente a lista de terrenos no Bloco 7 (Dashboard)

document.addEventListener('DOMContentLoaded', () => {
    // As URLs API_TERRENOS_URL e WIZARD_START_URL são injetadas no template HTML.

    // Verifica se as URLs foram injetadas corretamente
    if (typeof API_TERRENOS_URL === 'undefined' || typeof WIZARD_START_URL === 'undefined') {
        console.error("Erro: As URLs do Django (API_TERRENOS_URL ou WIZARD_START_URL) não foram injetadas no HTML.");
        return;
    }

    // 1. Definição dos elementos do DOM
    const terrenoSelect = document.getElementById('terrenoSelect');
    const selecionarBtn = document.getElementById('selecionarBtn');
    const btnText = document.getElementById('btnText');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const messageBox = document.getElementById('messageBox');

    const detailNome = document.getElementById('detailNome');
    const detailTamanho = document.getElementById('detailTamanho');
    const detailLocalizacao = document.getElementById('detailLocalizacao');

    // Variável global para armazenar os dados dos terrenos
    let terrenosData = [];

    // Função auxiliar para exibir mensagens de status
    const showMessage = (message, isError = false) => {
        messageBox.textContent = message;
        messageBox.className = isError ? 'text-sm mt-2 text-red-600' : 'text-sm mt-2 text-gray-500';
    };

    // 2. Função principal para carregar os terrenos
    const loadTerrenos = async () => {
        showMessage('Carregando terrenos...', false);
        selecionarBtn.disabled = true;
        loadingSpinner.classList.remove('hidden');

        try {
            // Usa a URL injetada do Django
            const response = await fetch(API_TERRENOS_URL);

            if (!response.ok) {
                // Tenta ler o erro do JSON se a resposta HTTP não for OK
                const errorData = await response.json();
                throw new Error(errorData.error || `Erro HTTP: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            terrenosData = data.terrenos || []; // Garante que é um array, mesmo que vazio

            // Limpa as opções existentes
            terrenoSelect.innerHTML = '<option value="" disabled selected>Selecione um terreno</option>';

            if (terrenosData.length === 0) {
                showMessage('Nenhum terreno cadastrado. Crie um terreno antes de iniciar um plano.', true);
                terrenoSelect.innerHTML = '<option value="" disabled selected>Nenhum terreno encontrado</option>';
            } else {
                terrenosData.forEach(terreno => {
                    const option = document.createElement('option');
                    option.value = terreno.id;
                    option.textContent = `${terreno.nome} (${terreno.localizacao})`;
                    terrenoSelect.appendChild(option);
                });
                showMessage(`Foram encontrados ${terrenosData.length} terreno(s).`, false);
            }

        } catch (error) {
            console.error('Falha ao carregar terrenos:', error);
            // Mensagem de erro amigável para o usuário
            showMessage(error.message || 'Erro desconhecido ao carregar terrenos. Tente novamente.', true);
            terrenoSelect.innerHTML = '<option value="" disabled selected>Erro ao carregar</option>';
        } finally {
            loadingSpinner.classList.add('hidden');
        }
    };

    // 3. Evento de seleção: Atualiza os detalhes
    terrenoSelect.addEventListener('change', (event) => {
        const selectedId = event.target.value;
        const selectedTerreno = terrenosData.find(t => t.id === selectedId);

        if (selectedTerreno) {
            // Atualiza o painel de detalhes
            detailNome.textContent = selectedTerreno.nome;
            detailTamanho.textContent = `${selectedTerreno.area_total} ${selectedTerreno.unidade_area}`;
            detailLocalizacao.textContent = selectedTerreno.localizacao;

            // Habilita o botão
            selecionarBtn.disabled = false;
            btnText.textContent = `Iniciar Plano para ${selectedTerreno.nome}`;
            showMessage('Pronto para iniciar o plano.', false);
        } else {
            // Limpa e desabilita se algo der errado
            detailNome.textContent = 'N/A';
            detailTamanho.textContent = '0 ha';
            detailLocalizacao.textContent = 'N/A';
            selecionarBtn.disabled = true;
            btnText.textContent = 'Selecione um Terreno';
        }
    });

    // 4. Evento do botão: Redireciona para a tela de criação do Plano
    selecionarBtn.addEventListener('click', () => {
        if (!selecionarBtn.disabled) {
            const selectedId = terrenoSelect.value;

            // Redireciona para o ponto de partida do wizard, passando o ID via Query Parameter
            // A view 'plano:iniciar_wizard' fará a validação e o redirecionamento final.
            const redirectUrl = `${WIZARD_START_URL}?terreno_id=${selectedId}`;

            // Exibe que a ação está ocorrendo
            btnText.textContent = 'Redirecionando...';
            selecionarBtn.disabled = true;
            loadingSpinner.classList.remove('hidden');

            // Redireciona
            window.location.href = redirectUrl;
        }
    });


    // 5. Inicia o carregamento quando o script for executado
    loadTerrenos();
});
