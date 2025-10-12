// planodeplantio_app/js/bloco7.js
// Script para carregar dinamicamente a lista de terrenos no Bloco 7 (Dashboard)

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
        messageBox.textContent = message;
        messageBox.className = isError ? 'text-sm mt-2 text-red-600' : 'text-sm mt-2 text-gray-500';
    };

    // Função para buscar a URL da API do Django (necessária para obter a rota correta)
    // No ambiente Django, a tag {% url 'plano:api_terrenos' %} deve ser renderizada no template HTML.
    // Assumimos que a URL base da API é /plano/api/terrenos/
    const getApiUrl = () => {
        // Tenta obter a URL do atributo data-url se for definido no HTML
        const scriptTag = document.querySelector('script[src*="bloco7.js"]');
        if (scriptTag && scriptTag.dataset.apiUrl) {
            return scriptTag.dataset.apiUrl;
        }
        // Fallback: assume que a URL é conhecida no contexto global.
        // Se a tag {% url %} foi usada no template, ela deve ter sido injetada de alguma forma.
        // Como não foi, usamos o padrão de rota conhecido:
        return '/plano/api/terrenos/';
    };

    // 2. Função principal para carregar os terrenos
    const loadTerrenos = async () => {
        showMessage('Carregando terrenos...', false);
        selecionarBtn.disabled = true;
        loadingSpinner.classList.remove('hidden');

        try {
            const apiUrl = getApiUrl();
            const response = await fetch(apiUrl);

            if (!response.ok) {
                // Se a resposta HTTP não for OK (ex: 404, 500), tenta ler o erro do JSON
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
            // Limpa e desabilita se algo der errado (o que não deve acontecer)
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
            // A view 'plano:criar_plano_plantio' espera receber um 'terreno_id' via GET
            const redirectUrl = `/plano/criar/?terreno_id=${selectedId}`;

            // Exibe que a ação está ocorrendo
            btnText.textContent = 'Redirecionando...';
            selecionarBtn.disabled = true;

            // Redireciona
            window.location.href = redirectUrl;
        }
    });


    // 5. Inicia o carregamento quando o script for executado
    loadTerrenos();
});
