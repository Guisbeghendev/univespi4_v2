// scripts/info_app_scripts.js
// Lógica de AJAX para o Bloco 3: Filtros de Consulta e Exibição da Ficha Técnica.

document.addEventListener('DOMContentLoaded', () => {
    // --------------------------------------------------------------------------
    // 1. Definição dos Elementos DOM (Usando IDs com -info para evitar conflito)
    // --------------------------------------------------------------------------
    const stateSelect = document.getElementById('state-select-info');
    const citySelect = document.getElementById('city-select-info');
    const produtoSelect = document.getElementById('produto-select-info');
    const resultsDisplay = document.getElementById('results-display');
    const produtoError = document.getElementById('produto-error-message');

    // Função auxiliar para buscar o CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // --------------------------------------------------------------------------
    // 2. Funções de Carregamento de Dados
    // --------------------------------------------------------------------------

    /**
     * Limpa e preenche um <select> com novas opções.
     * @param {HTMLElement} selectElement - O elemento <select> a ser preenchido.
     * @param {Array} data - Array de objetos {id: ..., nome: ...}.
     * @param {string} defaultMessage - Mensagem padrão.
     * @param {boolean} disable - Se o select deve ser desativado.
     */
    function populateSelect(selectElement, data, defaultMessage, disable = false) {
        selectElement.innerHTML = '';
        selectElement.disabled = disable;

        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = defaultMessage;
        selectElement.appendChild(defaultOption);

        data.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = item.nome;
            selectElement.appendChild(option);
        });
    }

    /**
     * Busca os estados na API do IBGE (via view do agro_app) e preenche o select.
     */
    async function loadStates() {
        // CORREÇÃO: Usando o prefixo /dashboard/ conforme o mapeamento do urls.py principal
        const url = "/dashboard/api/states/";
        stateSelect.innerHTML = '<option value="">Carregando estados...</option>';

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Falha ao carregar estados. Status: ${response.status}`);
            const states = await response.json();

            populateSelect(stateSelect, states, "Selecione o Estado", false);

        } catch (error) {
            console.error("Erro ao carregar estados:", error);
            stateSelect.innerHTML = '<option value="">Erro ao carregar</option>';
            stateSelect.disabled = true;
        }
    }

    /**
     * Busca as cidades na API do IBGE (via view do agro_app) e preenche o select.
     * @param {number} stateId - ID do estado selecionado.
     */
    async function loadCities(stateId) {
        // CORREÇÃO: Usando o prefixo /dashboard/
        const url = `/dashboard/api/cities/${stateId}/`;
        citySelect.innerHTML = '<option value="">Carregando cidades...</option>';
        citySelect.disabled = true;
        produtoSelect.innerHTML = '<option value="">Selecione uma cidade primeiro</option>';
        produtoSelect.disabled = true;

        if (!stateId) {
            populateSelect(citySelect, [], "Selecione um estado primeiro", true);
            return;
        }

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Falha ao carregar cidades.');
            const cities = await response.json();

            populateSelect(citySelect, cities, "Selecione a Cidade", false);

        } catch (error) {
            console.error(`Erro ao carregar cidades para o estado ${stateId}:`, error);
            citySelect.innerHTML = '<option value="">Erro ao carregar</option>';
            citySelect.disabled = true;
        }
    }

    /**
     * Busca os produtos/cultivos no serviço de dados (via view do info_app) e preenche o select.
     * Esta view usa a nova rota do info_app.
     * @param {number} cityId - ID da cidade selecionada.
     */
    async function loadProducts(cityId) {
        // Rota API do NOVO info_app (O prefixo /info/ está correto, pois está mapeado no urls.py principal)
        const url = `/info/api/products/${cityId}/`;
        produtoSelect.innerHTML = '<option value="">Carregando produtos...</option>';
        produtoSelect.disabled = true;
        resultsDisplay.innerHTML = '<p>Selecione um estado, cidade e cultivo para ver os dados.</p>';
        produtoError.style.display = 'none';

        if (!cityId) {
            populateSelect(produtoSelect, [], "Selecione uma cidade primeiro", true);
            return;
        }

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Falha ao carregar produtos.');
            const products = await response.json();

            if (products.length === 0) {
                produtoError.textContent = "Nenhum cultivo cadastrado para esta cidade na Ficha Técnica.";
                produtoError.style.display = 'block';
                populateSelect(produtoSelect, [], "Nenhum produto disponível", true);
            } else {
                populateSelect(produtoSelect, products, "Selecione o Cultivo", false);
            }

        } catch (error) {
            console.error(`Erro ao carregar produtos para a cidade ${cityId}:`, error);
            produtoError.textContent = "Erro ao conectar com o serviço de dados.";
            produtoError.style.display = 'block';
            produtoSelect.innerHTML = '<option value="">Erro ao carregar</option>';
            produtoSelect.disabled = true;
        }
    }


    /**
     * Busca e exibe os dados completos da Ficha Técnica.
     */
    async function loadFichaTecnica() {
        const productId = produtoSelect.value;
        const cityId = citySelect.value;

        if (!productId || !cityId) {
            resultsDisplay.innerHTML = '<p>Selecione um estado, cidade e cultivo para ver os dados.</p>';
            return;
        }

        // Rota API do NOVO info_app para a Ficha Técnica (O prefixo /info/ está correto)
        const url = `/info/api/ficha/${productId}/${cityId}/`;
        resultsDisplay.innerHTML = '<p class="text-center">Carregando Ficha Técnica...</p>';

        try {
            const response = await fetch(url);

            if (!response.ok) {
                // Se o servidor retornar 404 (Not Found) ou 500 (Server Error)
                resultsDisplay.innerHTML = '<p style="color: red;">Erro: Ficha Técnica não encontrada para a seleção.</p>';
                return;
            }

            const fichaData = await response.json();

            // --------------------------------------------------------
            // 3. Renderização da Ficha Técnica Completa
            // --------------------------------------------------------

            const html = renderFichaTecnica(fichaData);
            resultsDisplay.innerHTML = html;

        } catch (error) {
            console.error("Erro ao buscar Ficha Técnica:", error);
            resultsDisplay.innerHTML = '<p style="color: red;">Erro de conexão ao buscar os dados detalhados.</p>';
        }
    }

    /**
     * Converte o objeto Ficha Técnica em HTML formatado.
     * (Esta função exibirá o DOBRO dos dados, conforme a sua instrução)
     * @param {Object} data - Objeto contendo os dados da Ficha Técnica.
     * @returns {string} HTML formatado.
     */
    function renderFichaTecnica(data) {
        const product_name = data.produto || 'N/A';
        const city_name = data.city_name || 'N/A';

        // Mapeamento para garantir a ordem e tradução dos campos
        const sections = [
            {
                title: 'Informações Básicas e Identificação',
                fields: [
                    { label: 'Cultivo', value: product_name },
                    { label: 'Cidade/Estado', value: city_name },
                    { label: 'Tipo de Solo Preferido', value: data.tipo_solo || 'Não especificado' },
                    { label: 'Ciclo de Vida (Dias)', value: data.ciclo_vida_dias || 'N/A' }
                ]
            },
            {
                title: 'Dados Climáticos e de Cultivo',
                fields: [
                    { label: 'Temperatura Ideal (Média °C)', value: `${data.temperatura_ideal_c || 'N/A'} °C` },
                    { label: 'Precipitação Mínima (mm)', value: `${data.precipitacao_min_mm || 'N/A'} mm` },
                    { label: 'Altitude Média Ideal (m)', value: `${data.altitude_media_m || 'N/A'} m` },
                    { label: 'Período de Plantio (Sugestão)', value: data.periodo_plantio_sugerido || 'N/A' }
                ]
            },
            {
                title: 'Produtividade e Recursos',
                fields: [
                    { label: 'Produtividade Média (kg/ha)', value: `${data.produtividade_media_kg_ha || 'N/A'} kg/ha` },
                    { label: 'Necessidade Hídrica (Total mm)', value: `${data.necessidade_hidrica_total_mm || 'N/A'} mm` },
                    { label: 'Fertilizante Essencial', value: data.fertilizante_essencial || 'Não especificado' },
                    { label: 'Tempo de Colheita (Meses)', value: `${data.tempo_colheita_meses || 'N/A'} meses` }
                ]
            },
            {
                title: 'Condições Locais e Riscos',
                fields: [
                    { label: 'Vulnerabilidade a Pragas', value: data.vulnerabilidade_pragas || 'Não informado' },
                    { label: 'Condição Ideal de Colheita', value: data.condicao_ideal_colheita || 'N/A' },
                    { label: 'Anos de Estudo Local (IBGE)', value: data.anos_estudo_local_ibge || 'N/A' },
                    { label: 'Status de Sustentabilidade', value: data.status_sustentabilidade || 'Não avaliado' }
                ]
            }
        ];

        let htmlContent = `<h5 class="sub-title">${product_name} em ${city_name}</h5>`;

        sections.forEach(section => {
            htmlContent += `<div style="margin-top: 20px; padding-top: 10px; border-top: 1px dashed #ccc;">`;
            htmlContent += `<h6 style="color: #5D4037; font-weight: bold; margin-bottom: 10px;">${section.title}</h6>`;
            htmlContent += `<dl style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">`;

            section.fields.forEach(field => {
                htmlContent += `
                    <div style="padding: 5px; background-color: #f0f0f0; border-radius: 5px;">
                        <dt style="font-weight: 600; color: #4CAF50; font-size: 0.9em;">${field.label}:</dt>
                        <dd style="margin-left: 0; font-size: 1em;">${field.value}</dd>
                    </div>
                `;
            });
            htmlContent += `</dl></div>`;
        });

        return htmlContent;
    }


    // --------------------------------------------------------------------------
    // 4. Configuração dos Event Listeners
    // --------------------------------------------------------------------------

    // Ao selecionar um estado, carrega as cidades
    stateSelect.addEventListener('change', (e) => {
        const stateId = e.target.value;
        loadCities(stateId);
        // Reseta os demais selects e o display de resultados ao mudar o estado
        populateSelect(produtoSelect, [], "Selecione uma cidade primeiro", true);
        resultsDisplay.innerHTML = '<p>Selecione um estado, cidade e cultivo para ver os dados.</p>';
        produtoError.style.display = 'none';
    });

    // Ao selecionar uma cidade, carrega os produtos
    citySelect.addEventListener('change', (e) => {
        const cityId = e.target.value;
        loadProducts(cityId);
        // Reseta o display de resultados ao mudar a cidade
        resultsDisplay.innerHTML = '<p>Selecione um estado, cidade e cultivo para ver os dados.</p>';
    });

    // Ao selecionar um produto, carrega a Ficha Técnica
    produtoSelect.addEventListener('change', () => {
        loadFichaTecnica();
    });

    // --------------------------------------------------------------------------
    // 5. Inicialização
    // --------------------------------------------------------------------------
    loadStates();
});
