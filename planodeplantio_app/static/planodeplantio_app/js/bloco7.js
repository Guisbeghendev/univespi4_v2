// Script para carregar dinamicamente a lista de terrenos e planos no Bloco 7 (Dashboard)
// Este arquivo depende das variáveis API_TERRENOS_URL, WIZARD_START_URL,
// API_LISTA_PLANOS_URL e PLANO_VISUALIZACAO_URL definidas no template HTML antes de sua execução.

document.addEventListener('DOMContentLoaded', () => {
    // 1. Definição dos elementos do DOM - Terrenos
    const terrenoSelect = document.getElementById('terrenoSelect');
    const selecionarBtn = document.getElementById('selecionarBtn');
    const btnText = document.getElementById('btnText');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const messageBox = document.getElementById('messageBox');

    const detailNome = document.getElementById('detailNome');
    const detailTamanho = document.getElementById('detailTamanho');
    const detailLocalizacao = document.getElementById('detailLocalizacao');

    // 1B. Definição dos elementos do DOM - Planos (NOVOS)
    const planosListContainer = document.getElementById('planosListContainer');
    const planosLoading = document.getElementById('planosLoading');
    const planosEmpty = document.getElementById('planosEmpty');
    const planosList = document.getElementById('planosList'); // Novo UL para a lista

    // Variável global para armazenar os dados dos terrenos
    let terrenosData = [];

    // Função auxiliar para exibir mensagens de status
    const showMessage = (message, isError = false, targetBox = messageBox) => {
        // Verifica se o targetBox existe, protegendo contra erros de DOM
        if (targetBox) {
            targetBox.textContent = message;
            // Usando estilos inline simples para substituir as classes Tailwind
            targetBox.style.marginTop = '10px';
            targetBox.style.fontSize = '0.9em';
            targetBox.style.color = isError ? '#dc3545' : '#666'; // Vermelho ou Cinza
            targetBox.style.fontWeight = isError ? 'bold' : 'normal';
            targetBox.style.textAlign = 'center';
        }
    };

    // 2. Função principal para carregar os terrenos (INALTERADA NA LÓGICA)
    const loadTerrenos = async () => {
        if (typeof API_TERRENOS_URL === 'undefined' || typeof WIZARD_START_URL === 'undefined') {
            showMessage("Erro: As URLs do Django não foram injetadas corretamente no HTML.", true);
            if (selecionarBtn) selecionarBtn.disabled = true;
            if (loadingSpinner) loadingSpinner.classList.add('hidden');
            return;
        }

        showMessage('Carregando terrenos...', false);
        if (selecionarBtn) selecionarBtn.disabled = true;
        if (loadingSpinner) loadingSpinner.classList.remove('hidden');

        try {
            const response = await fetch(API_TERRENOS_URL);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Erro HTTP: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            terrenosData = data.terrenos || [];

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
            showMessage(error.message || 'Erro desconhecido ao carregar terrenos. Tente novamente.', true);
            if (terrenoSelect) terrenoSelect.innerHTML = '<option value="" disabled selected>Erro ao carregar</option>';
        } finally {
            if (loadingSpinner) loadingSpinner.classList.add('hidden');
        }
    };

    // 3. Função para renderizar um único item de plano
    const renderPlanoItem = (plano) => {
        const li = document.createElement('li');
        // Estilo básico para o item da lista (reaproveita 'terreno-item' do main.css, mas com ajustes)
        li.className = 'terreno-item';
        li.style.padding = '10px 0';
        li.style.borderBottom = '1px solid #eee';
        li.style.alignItems = 'flex-start'; // Garante alinhamento superior para o texto

        // Link de visualização
        // Substitui o placeholder '0' pelo ID real do plano
        const viewUrl = PLANO_VISUALIZACAO_URL.replace('0', plano.id);

        let statusColor = '#2196F3'; // Azul para 'Em Andamento'
        if (plano.status === 'Concluído') {
            statusColor = '#4CAF50'; // Verde
        } else if (plano.status === 'Cancelado') {
            statusColor = '#dc3545'; // Vermelho
        }

        li.innerHTML = `
            <div style="flex-grow: 1; margin-bottom: 5px;">
                <a href="${viewUrl}" style="font-weight: bold; color: #5D4037; text-decoration: none; font-size: 1em;">
                    ${plano.nome}
                </a>
                <p style="font-size: 0.85em; color: #666; margin: 2px 0;">
                    Cultivo: ${plano.produto_nome} | Terreno: ${plano.terreno_nome}
                </p>
                <p style="font-size: 0.85em; color: #666; margin: 2px 0;">
                    Local: ${plano.localizacao_display} | Início: ${plano.data_inicio}
                </p>
            </div>
            <div class="terreno-actions" style="margin-left: auto;">
                <span style="font-size: 0.9em; font-weight: bold; color: ${statusColor}; border: 1px solid ${statusColor}; padding: 3px 6px; border-radius: 4px;">
                    ${plano.status}
                </span>
                <a href="${viewUrl}" class="edit-btn" style="background-color: #2196F3; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;">
                    Detalhes
                </a>
            </div>
        `;
        return li;
    };

    // 4. Função para carregar a lista de planos (NOVA)
    const loadPlanos = async () => {
        if (typeof API_LISTA_PLANOS_URL === 'undefined') {
            // Este erro deve ser capturado na seção de terrenos, mas reforçamos aqui
            console.error("Erro fatal: API_LISTA_PLANOS_URL indefinida.");
            if (planosLoading) planosLoading.innerHTML = '<p style="color: #dc3545; font-weight: bold;">Erro ao carregar URLs de planos.</p>';
            return;
        }

        // 1. Mostrar loading e esconder tudo mais
        if (planosLoading) planosLoading.style.display = 'block';
        if (planosEmpty) planosEmpty.classList.add('hidden'); // Usa a classe 'hidden' do CSS fornecido
        if (planosList) planosList.innerHTML = '';


        try {
            const response = await fetch(API_LISTA_PLANOS_URL);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Erro HTTP: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            const planosData = data.planos || [];

            if (planosData.length === 0) {
                // Nenhum plano encontrado
                if (planosEmpty) planosEmpty.classList.remove('hidden');
            } else {
                // Renderiza os planos
                planosData.forEach(plano => {
                    const item = renderPlanoItem(plano);
                    if (planosList) planosList.appendChild(item);
                });
            }

        } catch (error) {
            console.error('Falha ao carregar planos:', error);
            if (planosListContainer) {
                planosListContainer.innerHTML = `<p style="color: #dc3545; font-weight: bold; text-align: center;">
                    Erro ao buscar planos: ${error.message}.
                </p>`;
            }
        } finally {
            // Esconder o loading
            if (planosLoading) planosLoading.style.display = 'none';
        }
    };


    // 5. Eventos de Terrenos (MANTIDOS)
    if (terrenoSelect) {
        terrenoSelect.addEventListener('change', (event) => {
            const selectedId = event.target.value;
            const selectedTerreno = terrenosData.find(t => String(t.id) === selectedId);

            if (selectedTerreno) {
                if (detailNome) detailNome.textContent = selectedTerreno.nome;
                if (detailTamanho) detailTamanho.textContent = `${selectedTerreno.area_total} ${selectedTerreno.unidade_area}`;
                if (detailLocalizacao) detailLocalizacao.textContent = selectedTerreno.localizacao_display;

                if (selecionarBtn) selecionarBtn.disabled = false;
                if (btnText) btnText.textContent = `Iniciar Plano para ${selectedTerreno.nome}`;
                showMessage('Pronto para iniciar o plano.', false);
            } else {
                if (detailNome) detailNome.textContent = 'N/A';
                if (detailTamanho) detailTamanho.textContent = '0 ha';
                if (detailLocalizacao) detailLocalizacao.textContent = 'N/A';
                if (selecionarBtn) selecionarBtn.disabled = true;
                if (btnText) btnText.textContent = 'Selecione um Terreno';
                showMessage('Nenhum detalhe encontrado para o item selecionado.', true);
            }
        });
    }

    if (selecionarBtn) {
        selecionarBtn.addEventListener('click', () => {
            if (!selecionarBtn.disabled) {
                const selectedId = terrenoSelect.value;
                const redirectUrl = `${WIZARD_START_URL}?terreno_id=${selectedId}`;

                if (btnText) btnText.textContent = 'Redirecionando...';
                selecionarBtn.disabled = true;
                if (loadingSpinner) loadingSpinner.classList.remove('hidden');

                window.location.href = redirectUrl;
            }
        });
    }

    // 6. Inicia o carregamento de Terrenos e Planos
    loadTerrenos();
    loadPlanos(); // <--- CHAMA A NOVA FUNÇÃO
});