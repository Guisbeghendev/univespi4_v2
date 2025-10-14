// Script para carregar dinamicamente a lista de terrenos no Bloco 7 (Dashboard)
// Este arquivo depende das variáveis API_TERRENOS_URL e WIZARD_START_URL
// definidas globalmente no template HTML antes de sua execução.

document.addEventListener('DOMContentLoaded', () => {
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
        // Verifica se messageBox existe, protegendo contra erros de DOM
        if (messageBox) {
            messageBox.textContent = message;
            messageBox.className = isError ? 'text-sm mt-2 text-red-600' : 'text-sm mt-2 text-gray-500';
        } else {
            console.warn("Elemento messageBox não encontrado.");
        }
    };

    // 2. Função principal para carregar os terrenos
    const loadTerrenos = async () => {
        // Verifica se as variáveis globais existem antes de usá-las (proteção, embora o HTML corrigido deva garantir isso)
        if (typeof API_TERRENOS_URL === 'undefined' || typeof WIZARD_START_URL === 'undefined') {
            showMessage("Erro: As URLs do Django não foram injetadas corretamente no HTML.", true);
            console.error("Erro fatal: API_TERRENOS_URL ou WIZARD_START_URL indefinida.");
            if (selecionarBtn) selecionarBtn.disabled = true;
            if (loadingSpinner) loadingSpinner.classList.add('hidden');
            return;
        }


        showMessage('Carregando terrenos...', false);
        if (selecionarBtn) selecionarBtn.disabled = true;
        if (loadingSpinner) loadingSpinner.classList.remove('hidden');

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
            if (terrenoSelect) {
                terrenoSelect.innerHTML = '<option value="" disabled selected>Selecione um terreno</option>';

                if (terrenosData.length === 0) {
                    showMessage('Nenhum terreno cadastrado. Crie um terreno antes de iniciar um plano.', true);
                    terrenoSelect.innerHTML = '<option value="" disabled selected>Nenhum terreno encontrado</option>';
                } else {
                    terrenosData.forEach(terreno => {
                        const option = document.createElement('option');
                        option.value = terreno.id;
                        option.textContent = `${terreno.nome} (${terreno.localizacao_display})`;
                        terrenoSelect.appendChild(option);
                    });
                    showMessage(`Foram encontrados ${terrenosData.length} terreno(s).`, false);
                }
            }

        } catch (error) {
            console.error('Falha ao carregar terrenos:', error);
            // Mensagem de erro amigável para o usuário
            showMessage(error.message || 'Erro desconhecido ao carregar terrenos. Tente novamente.', true);
            if (terrenoSelect) terrenoSelect.innerHTML = '<option value="" disabled selected>Erro ao carregar</option>';
        } finally {
            if (loadingSpinner) loadingSpinner.classList.add('hidden');
        }
    };

    // 3. Evento de seleção: Atualiza os detalhes
    if (terrenoSelect) {
        terrenoSelect.addEventListener('change', (event) => {
            const selectedId = event.target.value;
            // CORREÇÃO CRÍTICA: Converte o ID do Terreno para String, pois 'event.target.value'
            // é sempre uma string e o ID no JSON pode ser um número (integer PK do Django).
            const selectedTerreno = terrenosData.find(t => String(t.id) === selectedId);

            if (selectedTerreno) {
                // Atualiza o painel de detalhes
                if (detailNome) detailNome.textContent = selectedTerreno.nome;
                if (detailTamanho) detailTamanho.textContent = `${selectedTerreno.area_total} ${selectedTerreno.unidade_area}`;
                if (detailLocalizacao) detailLocalizacao.textContent = selectedTerreno.localizacao_display;

                // Habilita o botão
                if (selecionarBtn) selecionarBtn.disabled = false;
                if (btnText) btnText.textContent = `Iniciar Plano para ${selectedTerreno.nome}`;
                showMessage('Pronto para iniciar o plano.', false);
            } else {
                // Limpa e desabilita se algo der errado
                if (detailNome) detailNome.textContent = 'N/A';
                if (detailTamanho) detailTamanho.textContent = '0 ha';
                if (detailLocalizacao) detailLocalizacao.textContent = 'N/A';
                if (selecionarBtn) selecionarBtn.disabled = true;
                if (btnText) btnText.textContent = 'Selecione um Terreno';
                showMessage('Nenhum detalhe encontrado para o item selecionado.', true);
            }
        });
    }


    // 4. Evento do botão: Redireciona para a tela de criação do Plano
    if (selecionarBtn) {
        selecionarBtn.addEventListener('click', () => {
            if (!selecionarBtn.disabled) {
                const selectedId = terrenoSelect.value;

                // Redireciona para o ponto de partida do wizard, passando o ID via Query Parameter
                const redirectUrl = `${WIZARD_START_URL}?terreno_id=${selectedId}`;

                // Exibe que a ação está ocorrendo
                if (btnText) btnText.textContent = 'Redirecionando...';
                selecionarBtn.disabled = true;
                if (loadingSpinner) loadingSpinner.classList.remove('hidden');

                // Redireciona
                window.location.href = redirectUrl;
            }
        });
    }

    // 5. Inicia o carregamento quando o script for executado
    loadTerrenos();
});
