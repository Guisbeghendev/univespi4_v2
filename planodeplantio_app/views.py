from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST

# Importando o modelo Terreno (assumindo que o modelo está em agro_app)
from agro_app.models import Terreno

# Se você tiver um modelo PlanoPlantio, ele também seria importado daqui:
# from agro_app.models import PlanoPlantio

# --- API ENDPOINT ---

@login_required
def api_terrenos(request):
    """
    API: Retorna a lista de terrenos pertencentes ao usuário logado em formato JSON.
    Inclui o campo 'cidade' necessário para exibir a localização no frontend.
    """
    try:
        # 1. Busca todos os terrenos onde o proprietário é o usuário logado.
        terrenos = Terreno.objects.filter(usuario=request.user).order_by('nome')

        # 2. Serializa os dados.
        terrenos_data = []
        for terreno in terrenos:
            terrenos_data.append({
                'id': terreno.id,
                'nome': terreno.nome,
                'area_hectares': terreno.area_hectares,
                'cidade': terreno.cidade, # CAMPO CORRIGIDO/ADICIONADO
                'cultura_atual': terreno.cultura_atual,
            })

        # 3. Retorna a resposta JSON.
        return JsonResponse({'success': True, 'terrenos': terrenos_data})

    except Exception as e:
        # Em caso de erro, retorna uma resposta de erro.
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# --- ROTA DE AÇÃO ---

@login_required
@require_POST
def criar_plano_plantio(request):
    """
    Recebe o ID do terreno selecionado via POST e inicia a criação do Plano de Plantio.
    """
    terreno_id = request.POST.get('terreno_id')

    if not terreno_id:
        return JsonResponse({'success': False, 'error': 'ID do terreno não fornecido.'}, status=400)

    try:
        # 1. Verifica se o terreno existe e se pertence ao usuário (segurança).
        terreno = get_object_or_404(Terreno, id=terreno_id, usuario=request.user)

        # 2. Lógica para INICIAR o plano de plantio:
        # Aqui deve ser a lógica real de processamento e criação do PlanoPlantio.

        # Exemplo de lógica placeholder:
        # novo_plano = PlanoPlantio.objects.create(terreno=terreno, usuario=request.user, status='iniciado')

        # 3. Retorna sucesso para o JS.
        return JsonResponse({
            'success': True,
            'message': f'Terreno {terreno.nome} selecionado. Próxima etapa de configuração do plano.',
            # CORREÇÃO: Usando o prefixo '/plano/' na URL de redirecionamento
            'next_url': '/plano/proxima-etapa-do-plano/'
        })

    except Terreno.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Terreno não encontrado ou acesso negado.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro ao processar plano: {str(e)}'}, status=500)
