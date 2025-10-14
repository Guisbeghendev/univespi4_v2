// Lógica de AJAX para o Bloco 3: Filtros de Consulta e Exibição da Ficha Técnica.

document.addEventListener('DOMContentLoaded', () => {
    // --------------------------------------------------------------------------
    // 1. Definição dos Elementos DOM e Extração de URLs Dinâmicas (Django)
    // --------------------------------------------------------------------------
    const stateSelect = document.getElementById('state-select-info');
    const citySelect = document.getElementById('city-select-info');
    const produtoSelect = document.getElementById('produto-select-info');
    const resultsDisplay = document.getElementById('results-display');
    const produtoError = document.getElementById('produto-error-message');
    const apiUrlsDiv = document.getElementById('api-urls');

    // ** CORREÇÃO CRÍTICA: Adicionar verificação para evitar erro de runtime **
    if (!apiUrlsDiv) {
        console.error("ERRO CRÍTICO: Elemento #api-urls não encontrado. O script não pode iniciar. Verifique sua template HTML.");
        if (stateSelect) {
            stateSelect.innerHTML = '<option value="">Erro de Configuração (HTML missing #api-urls)</option>';
            stateSelect.disabled = true;
        }
        return; // Encerra a execução do script se o elemento de configuração base falhar.
    }

    // Extrai as URLs dinâmicas do Django (Corrigido para usar os atributos do DOM)
    const statesUrl = apiUrlsDiv.getAttribute('data-states-url');
    const citiesBaseUrl = apiUrlsDiv.getAttribute('data-cities-base-url');
    const productsBaseUrl = apiUrlsDiv.getAttribute('data-products-base-url');
    const fichaBaseUrl = apiUrlsDiv.getAttribute('data-ficha-base-url');


    // Função utilitária para exibir mensagens de status e loading
    function updateResultsStatus(message, isError = false) {
        let style = isError ? "color: #dc3545; font-weight: bold;" : "color: #5D4037;";
        let spinner = '';

        if (message.includes('Carregando') || message.includes('Buscando')) {
            // Reutiliza o estilo de spinner do CSS global (necessário que este CSS esteja carregado no HTML)
            spinner = '<div class="spinner"></div>';
            style += ' text-align: center;';
        }
        resultsDisplay.innerHTML = `<div style="${style}">${spinner}<p>${message}</p></div>`;
    }

    /**
     * Limpa e preenche um <select> com novas opções.
     */
    function populateSelect(selectElement, data, defaultMessage, disable = false) {
        selectElement.innerHTML = '';
        selectElement.disabled = disable;
        // Adiciona um estilo leve para indicar estado desabilitado
        selectElement.style.backgroundColor = disable ? '#eee' : '#fff';

        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = defaultMessage;
        defaultOption.selected = true;
        selectElement.appendChild(defaultOption);

        data.forEach(item => {
            const option = document.createElement('option');
            // Para Produtos, o ID é o NOME do produto (string) no template original
            option.value = item.id || item.nome;
            option.textContent = item.nome;
            selectElement.appendChild(option);
        });
    }

    // --------------------------------------------------------------------------
    // 2. Funções de Carregamento de Dados (Usando as URLs Dinâmicas)
    // --------------------------------------------------------------------------

    /**
     * Busca os estados e preenche o select.
     */
    async function loadStates() {
        stateSelect.innerHTML = '<option value="">Carregando estados...</option>';
        stateSelect.disabled = true;

        try {
            const response = await fetch(statesUrl);
            if (!response.ok) throw new Error(`Falha ao carregar estados. Status: ${response.status}`);
            const states = await response.json();

            populateSelect(stateSelect, states, "Selecione o Estado", false);

        } catch (error) {
            console.error("Erro ao carregar estados:", error);
            stateSelect.innerHTML = '<option value="">Erro ao carregar</option>';
        }
    }

    /**
     * Busca as cidades e preenche o select.
     */
    async function loadCities(stateId) {
        // Usa a URL base e substitui o placeholder dinâmico '0' pelo ID do estado
        const url = citiesBaseUrl.replace('/0/', `/${stateId}/`);

        citySelect.innerHTML = '<option value="">Carregando cidades...</option>';
        citySelect.disabled = true;

        // Reset dos selects dependentes
        populateSelect(produtoSelect, [], "Selecione uma cidade primeiro", true);

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
        }
    }

    /**
     * Busca os produtos/cultivos e preenche o select.
     */
    async function loadProducts(cityId) {
        // Usa a URL base e substitui o placeholder dinâmico '0' pelo ID da cidade
        const url = productsBaseUrl.replace('/0/', `/${cityId}/`);

        produtoSelect.innerHTML = '<option value="">Carregando produtos...</option>';
        produtoSelect.disabled = true;
        updateResultsStatus('Selecione um estado, cidade e cultivo para ver os dados.');
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
                // Nota: O campo .id ou .nome do produto deve ser o nome (string) do produto
                populateSelect(produtoSelect, products, "Selecione o Cultivo", false);
            }

        } catch (error) {
            console.error(`Erro ao carregar produtos para a cidade ${cityId}:`, error);
            produtoError.textContent = "Erro ao conectar com o serviço de dados.";
            produtoError.style.display = 'block';
            produtoSelect.innerHTML = '<option value="">Erro ao carregar</option>';
        }
    }


    /**
     * Busca e exibe os dados completos da Ficha Técnica.
     */
    async function loadFichaTecnica() {
        const productName = produtoSelect.value;
        const cityId = citySelect.value;

        if (!productName || !cityId) {
            updateResultsStatus('Selecione um estado, cidade e cultivo para ver os dados.');
            return;
        }

        // O nome do produto deve ser URI-encoded para ser seguro na URL
        const encodedProductName = encodeURIComponent(productName);

        // Substitui o placeholder '__PRODUCT_NAME__' e o ID da cidade
        const url = fichaBaseUrl
            .replace('__PRODUCT_NAME__', encodedProductName)
            .replace('/0/', `/${cityId}/`);

        updateResultsStatus('Carregando Ficha Técnica...');

        try {
            const response = await fetch(url);

            if (response.status === 404) {
                updateResultsStatus('Erro: Ficha Técnica não encontrada para a seleção.', true);
                return;
            }
            if (!response.ok) {
                throw new Error(`Erro ${response.status}`);
            }

            const fichaData = await response.json();

            // Renderização da Ficha Técnica Completa
            const html = renderFichaTecnica(fichaData);
            resultsDisplay.innerHTML = html;

        } catch (error) {
            console.error("Erro ao buscar Ficha Técnica:", error);
            updateResultsStatus('Erro de conexão ao buscar os dados detalhados.', true);
        }
    }

    /**
     * Converte o objeto Ficha Técnica em HTML formatado, utilizando as classes CSS
     * específicas definidas no template para manter a separação de estilos.
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
                    { label: 'Temperatura Ideal (Média)', value: `${data.temperatura_ideal_c || 'N/A'} °C` },
                    { label: 'Precipitação Mínima', value: `${data.precipitacao_min_mm || 'N/A'} mm` },
                    { label: 'Altitude Média Ideal', value: `${data.altitude_media_m || 'N/A'} m` },
                    { label: 'Período de Plantio', value: data.periodo_plantio_sugerido || 'N/A' }
                ]
            },
            {
                title: 'Produtividade e Recursos',
                fields: [
                    { label: 'Produtividade Média', value: `${data.produtividade_media_kg_ha || 'N/A'} kg/ha` },
                    { label: 'Necessidade Hídrica Total', value: `${data.necessidade_hidrica_total_mm || 'N/A'} mm` },
                    { label: 'Fertilizante Essencial', value: data.fertilizante_essencial || 'Não especificado' },
                    { label: 'Tempo de Colheita', value: `${data.tempo_colheita_meses || 'N/A'} meses` }
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

        let htmlContent = `<h5 class="sub-title" style="font-size: 1.5em;">${product_name} em ${city_name}</h5>`;

        sections.forEach(section => {
            htmlContent += `<div class="ficha-detail-section">`;
            htmlContent += `<h6 class="ficha-detail-title">${section.title}</h6>`;
            // Aplica a classe de grid responsiva do template
            htmlContent += `<dl class="ficha-detail-grid">`;

            section.fields.forEach(field => {
                // Aplica a classe de item de detalhe do template
                htmlContent += `
                    <div class="ficha-detail-item">
                        <dt>${field.label}:</dt>
                        <dd>${field.value}</dd>
                    </div>
                `;
            });
            htmlContent += `</dl></div>`;
        });

        return htmlContent;
    }


    // --------------------------------------------------------------------------
    // 3. Configuração dos Event Listeners e Inicialização
    // --------------------------------------------------------------------------

    stateSelect.addEventListener('change', (e) => {
        const stateId = e.target.value;
        loadCities(stateId);
        // Reseta os demais selects e o display de resultados ao mudar o estado
        populateSelect(produtoSelect, [], "Selecione uma cidade primeiro", true);
        updateResultsStatus('Selecione um estado, cidade e cultivo para ver os dados.');
        produtoError.style.display = 'none';
    });

    citySelect.addEventListener('change', (e) => {
        const cityId = e.target.value;
        loadProducts(cityId);
        // Reseta o display de resultados ao mudar a cidade
        updateResultsStatus('Selecione um estado, cidade e cultivo para ver os dados.');
    });

    produtoSelect.addEventListener('change', () => {
        if (produtoSelect.value) {
            produtoError.style.display = 'none';
            loadFichaTecnica();
        }
    });

    // Inicialização: carrega os estados ao iniciar a página
    loadStates();
});
