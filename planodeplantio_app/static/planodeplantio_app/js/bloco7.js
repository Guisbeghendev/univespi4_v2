// Variáveis Globais
// URLs para as APIs do Django
const apiTerrenosUrl = '/plano/api/terrenos/'; // CORREÇÃO: Deve incluir o prefixo '/plano/' para a rota principal
const criarPlanoUrl = '/plano/criar_plano_plantio/'; // CORREÇÃO: Deve incluir o prefixo '/plano/' para a rota principal

let allTerrenos = []; // Armazena a lista completa de terrenos
const DURATION_SUCCESS_REDIRECT = 1500; // 1.5 segundos para redirecionamento após sucesso

// Referências DOM
const terrenoSelect = document.getElementById('terrenoSelect');
const terrenoDetails = document.getElementById('terrenoDetails');
const selecionarBtn = document.getElementById('selecionarBtn');
const messageBox = document.getElementById('messageBox');
const btnText = document.getElementById('btnText');
const loadingSpinner = document.getElementById('loadingSpinner');

// Funções Auxiliares
const showLoading = (isLoading) => {
    selecionarBtn.disabled = isLoading;
    loadingSpinner.classList.toggle('hidden', !isLoading);
    btnText.textContent = isLoading ? 'Processando...' : 'Continuar Planejamento';
};

const displayMessage = (message, type = 'error') => {
    messageBox.textContent = message;
    // Define a cor da mensagem baseada no tipo (sucesso ou erro/info)
    const colorClass = type === 'success' ? 'text-green-600' :
                       type === 'info' ? 'text-blue-600' :
                       'text-red-600';
    messageBox.className = `text-sm text-center mt-3 font-semibold ${colorClass}`;
};

// Obtém o token CSRF do cookie (necessário para requisições POST seguras no Django)
const getCsrfToken = () => {
    return document.cookie.split('; ').find(row => row.startsWith('csrftoken'))?.split('=')[1];
};

// 1. Carregar Terrenos da API
const loadTerrenos = async () => {
    displayMessage('Carregando terrenos...', 'info');

    try {
        // CORREÇÃO: A URL agora usa o prefixo /plano/
        const response = await fetch(apiTerrenosUrl);

        if (!response.ok) {
            throw new Error(`Erro de rede: ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.terrenos) {
            allTerrenos = data.terrenos;

            // Limpa e popula o SELECT
            terrenoSelect.innerHTML = '';

            const hasTerrenos = allTerrenos.length > 0;

            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = hasTerrenos ? 'Selecione um Terreno' : 'Nenhum terreno cadastrado.';
            defaultOption.disabled = true;
            defaultOption.selected = true;
            terrenoSelect.appendChild(defaultOption);

            allTerrenos.forEach(terreno => {
                const option = document.createElement('option');
                option.value = terreno.id;
                // Usa o campo 'cidade' que foi adicionado na views.py
                option.textContent = `${terreno.nome} (${terreno.area_hectares} ha) - ${terreno.cidade || 'Local Desconhecido'}`;
                terrenoSelect.appendChild(option);
            });

            displayMessage(''); // Limpa a mensagem de carregamento
            selecionarBtn.disabled = !hasTerrenos;
            if (!hasTerrenos) {
                btnText.textContent = 'Nenhum Terreno Disponível';
            }

        } else {
            displayMessage(data.error || 'Erro desconhecido ao carregar terrenos.');
            terrenoSelect.innerHTML = '<option value="" disabled selected>Erro ao carregar</option>';
            selecionarBtn.disabled = true;
        }

    } catch (error) {
        console.error('Erro na requisição da API de terrenos:', error);
        displayMessage(`Erro de conexão/servidor: ${error.message}`);
        terrenoSelect.innerHTML = '<option value="" disabled selected>Erro de Rede</option>';
        selecionarBtn.disabled = true;
    }
};

// 2. Atualizar Detalhes do Terreno Selecionado
const updateDetails = () => {
    const selectedId = terrenoSelect.value;

    if (selectedId) {
        const selectedTerreno = allTerrenos.find(t => t.id.toString() === selectedId);

        if (selectedTerreno) {
            document.getElementById('detailNome').textContent = selectedTerreno.nome;
            document.getElementById('detailTamanho').textContent = `${selectedTerreno.area_hectares} ha`;
            // Usa o campo 'cidade' que agora deve vir do backend
            document.getElementById('detailLocalizacao').textContent = selectedTerreno.cidade || 'Não informada';

            // terrenoDetails.classList.remove('hidden'); // Removido pois o HTML não tem hidden inicialmente
            selecionarBtn.disabled = false;
            btnText.textContent = 'Continuar Planejamento';
            displayMessage('');
        }
    } else {
        document.getElementById('detailNome').textContent = 'N/A';
        document.getElementById('detailTamanho').textContent = '0 ha';
        document.getElementById('detailLocalizacao').textContent = 'N/A';
        // terrenoDetails.classList.add('hidden');
        selecionarBtn.disabled = true;
        btnText.textContent = 'Selecione um Terreno';
        displayMessage('');
    }
};

// 3. Enviar Plano de Plantio
const submitPlano = async () => {
    const selectedId = terrenoSelect.value;

    if (!selectedId) {
        displayMessage('Por favor, selecione um terreno antes de continuar.', 'error');
        return;
    }

    const csrftoken = getCsrfToken();
    if (!csrftoken) {
        displayMessage('Erro de segurança: Token CSRF não encontrado.', 'error');
        return;
    }

    showLoading(true);
    displayMessage('Iniciando plano de plantio, aguarde...', 'info');

    try {
        const formData = new FormData();
        formData.append('terreno_id', selectedId);

        // CORREÇÃO: A URL agora usa o prefixo /plano/
        const response = await fetch(criarPlanoUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken, // Inclui o token para Django
            },
            body: formData,
        });

        const data = await response.json();

        if (data.success) {
            displayMessage(data.message || 'Plano de plantio iniciado com sucesso!', 'success');

            // Redireciona para a próxima etapa se a URL for fornecida
            if (data.next_url) {
                setTimeout(() => {
                    window.location.href = data.next_url;
                }, DURATION_SUCCESS_REDIRECT);
            }
        } else {
            // Em caso de erro de validação ou lógico no Django
            displayMessage(data.error || 'Falha ao iniciar o plano. Tente novamente.');
        }

    } catch (error) {
        console.error('Erro no envio do plano:', error);
        displayMessage('Erro de rede ou servidor ao tentar criar o plano.');
    } finally {
        showLoading(false);
    }
};

// 4. Inicialização e Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadTerrenos();

    terrenoSelect.addEventListener('change', updateDetails);
    selecionarBtn.addEventListener('click', submitPlano);
});
