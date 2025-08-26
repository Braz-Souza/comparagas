import streamlit as st
import os
import pandas as pd
import json
from datetime import datetime
from utils.ragas_text_comparison import compare_texts_sync, ComparisonType
from utils.ragas_text_comparison import LABEL_OPTIONS, LABEL_FORMAT
from utils.llm import eval_llm, update_eval_llm
from utils.report_generator import generate_pdf_report, generate_docx_report
import streamlit.components.v1 as components

def add_localStorage_functions():
    """Adiciona funções JavaScript para gerenciar localStorage sem interferir na visualização"""
    # Usar um container invisível que não afeta o layout
    components.html(
        """
        <div style="display: none; position: absolute; top: -1000px; left: -1000px;">
            <script>
            // Função para salvar dados no localStorage
            function saveToLocalStorage(testType, data) {
                const key = `comparagas_${testType}`;
                localStorage.setItem(key, JSON.stringify(data));
                console.log(`Dados salvos para ${testType}:`, data);
            }
            
            // Função para carregar dados do localStorage
            function loadFromLocalStorage(testType) {
                const key = `comparagas_${testType}`;
                const data = localStorage.getItem(key);
                const result = data ? JSON.parse(data) : null;
                console.log(`Dados carregados para ${testType}:`, result);
                return result;
            }
            
            // Função para limpar dados do localStorage
            function clearLocalStorage(testType) {
                const key = `comparagas_${testType}`;
                localStorage.removeItem(key);
                console.log(`Dados limpos para ${testType}`);
            }
            
            // Função para listar todas as chaves salvas
            function listAllKeys() {
                const keys = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key.startsWith('comparagas_')) {
                        keys.push(key);
                    }
                }
                console.log('Chaves encontradas:', keys);
                return keys;
            }
            
            // Disponibilizar funções globalmente
            window.comparagasStorage = {
                save: saveToLocalStorage,
                load: loadFromLocalStorage,
                clear: clearLocalStorage,
                listKeys: listAllKeys
            };
            
            // Auto-executar ao carregar
            console.log('LocalStorage functions loaded');
            </script>
        </div>
        """,
        height=0,
        width=0
    )

def save_current_data_to_localStorage(test_type):
    """Salva os dados atuais no localStorage através de JavaScript sem interferir na visualização"""
    if not test_type:
        return
    
    # Obter dados dos campos de texto atuais
    reference_text = st.session_state.get(f'multi_ref_{test_type}', '')
    generated_text = st.session_state.get(f'multi_gen_{test_type}', '')
    selected_evaluations = st.session_state.get('multi_comparison_types', [])
    evaluation_configs = st.session_state.get('selected_evaluations_for_storage', [])
    
    data = {
        'reference_text': reference_text,
        'generated_text': generated_text,
        'selected_evaluations': selected_evaluations,
        'evaluation_configs': evaluation_configs
    }
    
    # Executar JavaScript para salvar com container invisível
    components.html(
        f"""
        <div style="display: none; position: absolute; top: -1000px; left: -1000px;">
            <script>
            if (window.comparagasStorage) {{
                window.comparagasStorage.save('{test_type}', {data});
            }}
            </script>
        </div>
        """,
        height=0,
        width=0
    )

def load_data_from_localStorage(test_type):
    """Carrega dados do localStorage e os coloca no session_state"""
    if not test_type:
        return
    
    # Chaves para os campos de texto
    reference_key = f'multi_ref_{test_type}'
    generated_key = f'multi_gen_{test_type}'
    temp_key = f'temp_data_{test_type}'
    
    # Sempre garantir que as chaves existam no session_state
    st.session_state.setdefault(reference_key, '')
    st.session_state.setdefault(generated_key, '')
    st.session_state.setdefault('multi_comparison_types', [ComparisonType.FACTUAL_CORRECTNESS.value])
    st.session_state.setdefault('selected_evaluations_for_storage', [])
    
    # Verificar se há dados salvos para restaurar
    if temp_key in st.session_state:
        saved_data = st.session_state[temp_key]
        
        # Restaurar dados apenas se tiverem conteúdo significativo
        if saved_data.get('reference_text'):
            st.session_state[reference_key] = saved_data['reference_text']
            
        if saved_data.get('generated_text'):
            st.session_state[generated_key] = saved_data['generated_text']
            
        # Restaurar configurações de avaliação
        if saved_data.get('selected_evaluations'):
            st.session_state['multi_comparison_types'] = saved_data['selected_evaluations']
        if saved_data.get('evaluation_configs'):
            st.session_state['selected_evaluations_for_storage'] = saved_data['evaluation_configs']

def save_data_automatically(test_type):
    """Salva dados automaticamente quando há mudanças"""
    if not test_type:
        return
    
    # Obter dados atuais dos campos usando setdefault para segurança
    reference_text = st.session_state.get(f'multi_ref_{test_type}', '')
    generated_text = st.session_state.get(f'multi_gen_{test_type}', '')
    selected_evaluations = st.session_state.get('multi_comparison_types', [ComparisonType.FACTUAL_CORRECTNESS.value])
    evaluation_configs = st.session_state.get('selected_evaluations_for_storage', [])
    
    # Salvar apenas se há algum conteúdo para salvar
    if reference_text or generated_text or evaluation_configs:
        st.session_state[f'temp_data_{test_type}'] = {
            'reference_text': reference_text,
            'generated_text': generated_text,
            'selected_evaluations': selected_evaluations,
            'evaluation_configs': evaluation_configs
        }

def export_session_data():
    """Exporta todos os dados da sessão atual para formato JSON"""
    export_data = {
        'metadata': {
            'export_timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'application': 'comparagas-ragas'
        },
        'test_types': st.session_state.get('test_types', {}),
        'test_results': st.session_state.get('test_results', {}),
        'current_configuration': {
            'current_test_type': st.session_state.get('current_test_type', None),
            'multi_comparison_types': st.session_state.get('multi_comparison_types', []),
            'selected_evaluations_for_storage': st.session_state.get('selected_evaluations_for_storage', [])
        },
        'temp_data': {}
    }
    
    # Incluir dados temporários salvos para cada tipo de teste
    for key, value in st.session_state.items():
        if key.startswith('temp_data_'):
            test_type = key.replace('temp_data_', '')
            export_data['temp_data'][test_type] = value
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)

def import_session_data(json_data):
    """Importa dados da sessão a partir de JSON"""
    try:
        data = json.loads(json_data)
        
        # Validar formato básico
        if 'metadata' not in data or 'test_types' not in data:
            return False, "Formato de arquivo inválido: campos obrigatórios ausentes"
        
        # Validar versão
        if data['metadata'].get('application') != 'comparagas-ragas':
            return False, "Arquivo não é de uma sessão do Comparagas"
        
        # Limpar dados existentes com confirmação implícita
        # (assumindo que o usuário já confirmou a importação)
        
        # Importar test_types
        if data['test_types']:
            st.session_state.test_types = data['test_types']
        
        # Importar test_results
        if data.get('test_results'):
            st.session_state.test_results = data['test_results']
        
        # Importar configuração atual
        config = data.get('current_configuration', {})
        if config.get('current_test_type'):
            st.session_state.current_test_type = config['current_test_type']
        if config.get('multi_comparison_types'):
            st.session_state.multi_comparison_types = config['multi_comparison_types']
        if config.get('selected_evaluations_for_storage'):
            st.session_state.selected_evaluations_for_storage = config['selected_evaluations_for_storage']
        
        # Importar dados temporários
        temp_data = data.get('temp_data', {})
        for test_type, temp_info in temp_data.items():
            st.session_state[f'temp_data_{test_type}'] = temp_info
            
            # Restaurar campos de texto se disponíveis
            if temp_info.get('reference_text'):
                st.session_state[f'multi_ref_{test_type}'] = temp_info['reference_text']
            if temp_info.get('generated_text'):
                st.session_state[f'multi_gen_{test_type}'] = temp_info['generated_text']
        
        return True, f"Sessão importada com sucesso! Data da exportação: {data['metadata'].get('export_timestamp', 'N/A')}"
        
    except json.JSONDecodeError as e:
        return False, f"Erro ao decodificar JSON: {str(e)}"
    except Exception as e:
        return False, f"Erro durante importação: {str(e)}"

def display_combined_results(available_results):
    """Função para exibir gráfico combinado com todos os tipos de teste"""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    if not available_results:
        return
    
    # Determinar todas as métricas únicas disponíveis
    all_evaluations = set()
    for test_type in available_results:
        result_data = st.session_state.test_results[test_type]
        all_evaluations.update(result_data['evaluations'])
    
    all_evaluations = sorted(list(all_evaluations))
    
    # Opção para visualização: subplots ou barras agrupadas
    viz_option = st.radio(
        "Tipo de Visualização:",
        ["📊 Barras Agrupadas", "📈 Subplots (um por métrica)"],
        horizontal=True
    )
    
    if viz_option == "📊 Barras Agrupadas":
        display_grouped_bar_chart(available_results, all_evaluations)
    else:
        display_subplots_chart(available_results, all_evaluations)

def display_grouped_bar_chart(available_results, all_evaluations):
    """Exibe gráfico de barras agrupadas com avaliações unidas e modelos separados"""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']
    
    # Preparar nomes limpos das avaliações para o eixo X
    clean_evaluation_names = []
    for eval_config in all_evaluations:
        clean_name = eval_config.replace("Factual Correctness - ", "FC - ").replace("Semantic Similarity - ", "SS - ")
        clean_evaluation_names.append(clean_name)
    
    # Para cada tipo de teste (modelo)
    for i, test_type in enumerate(available_results):
        result_data = st.session_state.test_results[test_type]
        all_results = result_data['results']
        
        y_values = []
        
        # Para cada avaliação disponível
        for eval_config in all_evaluations:
            if eval_config in result_data['evaluations']:
                scores = []
                for result in all_results:
                    if isinstance(result.get(eval_config), (int, float)):
                        scores.append(result[eval_config])
                
                if scores:
                    y_values.append(sum(scores) / len(scores))
                else:
                    y_values.append(0)
            else:
                # Métrica não avaliada para este tipo de teste
                y_values.append(0)
        
        # Adicionar barra para este tipo de teste (modelo)
        fig.add_trace(go.Bar(
            name=test_type,
            x=clean_evaluation_names,
            y=y_values,
            marker_color=colors[i % len(colors)],
            text=[f"{val:.3f}" if val > 0 else "N/A" for val in y_values],
            textposition='outside'
        ))
    
    fig.update_layout(
        title="Comparação de Médias: Avaliações Unidas por Modelo",
        xaxis_title="Métricas de Avaliação",
        yaxis_title="Score Médio",
        yaxis=dict(range=[0, 1.1]),
        barmode='group',
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title="Modelos/Tipos de Teste"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_subplots_chart(available_results, all_evaluations):
    """Exibe subplots com um modelo por subplot, mostrando todas as avaliações"""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    if not available_results:
        st.warning("Nenhum resultado encontrado para visualizar")
        return
    
    # Calcular layout dos subplots - um subplot por modelo
    n_models = len(available_results)
    cols = min(2, n_models)  # Máximo 2 colunas
    rows = (n_models + cols - 1) // cols  # Calcular número de linhas necessárias
    
    fig = make_subplots(
        rows=rows, 
        cols=cols,
        subplot_titles=available_results,
        vertical_spacing=0.12,
        horizontal_spacing=0.15
    )
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']
    
    # Para cada modelo, criar um subplot
    for idx, test_type in enumerate(available_results):
        row = (idx // cols) + 1
        col = (idx % cols) + 1
        
        result_data = st.session_state.test_results[test_type]
        all_results = result_data['results']
        
        evaluation_names = []
        scores = []
        
        # Para cada avaliação disponível
        for eval_config in all_evaluations:
            if eval_config in result_data['evaluations']:
                metric_scores = []
                for result in all_results:
                    if isinstance(result.get(eval_config), (int, float)):
                        metric_scores.append(result[eval_config])
                
                if metric_scores:
                    clean_name = eval_config.replace("Factual Correctness - ", "FC - ").replace("Semantic Similarity - ", "SS - ")
                    evaluation_names.append(clean_name)
                    scores.append(sum(metric_scores) / len(metric_scores))
        
        if evaluation_names and scores:
            fig.add_trace(
                go.Bar(
                    x=evaluation_names,
                    y=scores,
                    name=test_type,
                    marker_color=[colors[i % len(colors)] for i in range(len(evaluation_names))],
                    text=[f"{score:.3f}" for score in scores],
                    textposition='outside',
                    showlegend=False
                ),
                row=row, col=col
            )
            
            # Configurar eixos para cada subplot
            fig.update_yaxes(range=[0, 1.1], row=row, col=col)
            fig.update_xaxes(tickangle=45, row=row, col=col)
    
    fig.update_layout(
        title="Comparação Detalhada: Avaliações por Modelo",
        height=300 * rows,  # Altura dinâmica baseada no número de linhas
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_results_for_test_type(test_type):
    """Função para exibir resultados de um tipo de teste específico"""
    if test_type not in st.session_state.test_results:
        return
    
    result_data = st.session_state.test_results[test_type]
    all_results = result_data['results']
    selected_evaluations = result_data['evaluations']
    timestamp = result_data['timestamp']
    
    st.info(f"🕒 Última avaliação: {timestamp}")
    
    # Criar DataFrame para visualização
    df_results = pd.DataFrame(all_results)
    
    # Preparar dados para gráfico de barras com médias
    bar_data = []
    
    for eval_config in selected_evaluations:
        scores = []
        for result in all_results:
            if isinstance(result[eval_config], (int, float)):
                scores.append(result[eval_config])
        
        if scores:  # Se há scores válidos
            # Clean up the evaluation name for display
            clean_name = eval_config.replace("Factual Correctness - ", "FC - ").replace("Semantic Similarity - ", "SS - ")
            media_scores = sum(scores) / len(scores)
            bar_data.append({
                'evaluation': clean_name,
                'media': media_scores
            })
    
    # Criar gráfico de barras
    import plotly.graph_objects as go
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']
    
    evaluations = [data['evaluation'] for data in bar_data]
    medias = [data['media'] for data in bar_data]
    
    fig.add_trace(go.Bar(
        x=evaluations,
        y=medias,
        marker_color=[colors[i % len(colors)] for i in range(len(evaluations))],
        text=[f"{media:.3f}" for media in medias],
        textposition='outside'
    ))
    
    fig.update_layout(
        title=f"Média dos Scores - {test_type}",
        xaxis_title="Tipo de Avaliação",
        yaxis_title="Score Médio",
        yaxis=dict(range=[0, max(1, max(medias) * 1.1) if medias else 1]),
        height=600,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar resumo estatístico
    st.subheader("Resumo Estatístico por Avaliação")
    
    summary_data = []
    for eval_config in selected_evaluations:
        scores = []
        for result in all_results:
            if isinstance(result[eval_config], (int, float)):
                scores.append(result[eval_config])
        
        if scores:  # Se há scores válidos
            # Clean up the evaluation name for display
            clean_name = eval_config.replace("Factual Correctness - ", "FC - ").replace("Semantic Similarity - ", "SS - ")
            summary_data.append({
                'Avaliação': clean_name,
                'Média': f"{sum(scores) / len(scores):.3f}",
                'Mediana': f"{sorted(scores)[len(scores)//2]:.3f}",
                'Mínimo': f"{min(scores):.3f}",
                'Máximo': f"{max(scores):.3f}",
                'Desvio Padrão': f"{(sum([(x - sum(scores)/len(scores))**2 for x in scores]) / len(scores))**0.5:.3f}",
                'Iterações': len(scores)
            })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)
    
    # Tabela detalhada por iteração
    st.subheader("Resultados Detalhados por Iteração")
    
    # Preparar dados para exibição
    display_df = df_results.copy()
    
    # Formatar colunas numéricas
    for col in display_df.columns:
        if col != 'iteration':
            display_df[col] = display_df[col].apply(
                lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else str(x)
            )
    
    st.dataframe(display_df, use_container_width=True)

st.set_page_config(page_title="RAGAS Text Comparison", layout="wide")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Provider selection
    PROVIDERS = {
        "OpenAI": "https://api.openai.com/v1",
        "OpenRouter": "https://openrouter.ai/api/v1",
        "DeepSeek": "https://api.deepseek.com/v1"
    }
    
    selected_provider = st.selectbox(
        "Provedor:",
        options=list(PROVIDERS.keys()),
        help="Selecione o provedor de LLM",
        index=0
    )
    
    base_url = PROVIDERS[selected_provider]

    openai_key = st.text_input(
        "API Key:",
        type="password",
        help="Necessário para usar RAGAS"
    )
    
    # Botão para buscar modelos
    if st.button("🔄 Buscar Modelos", help="Busca modelos disponíveis no endpoint"):
        if openai_key:
            with st.spinner("Buscando modelos..."):
                try:
                    # Atualizar eval_llm temporariamente para buscar modelos
                    update_eval_llm(api_key=openai_key, base_url=base_url)
                    models = eval_llm.get_available_models()
                    st.session_state.available_models = models
                    st.session_state.current_api_key = openai_key
                    st.session_state.current_base_url = base_url
                    st.success(f"Encontrados {len(models)} modelos")
                except Exception as e:
                    st.error(f"Erro ao buscar modelos: {str(e)}")
                    st.session_state.available_models = []
        else:
            st.warning("Insira a API Key primeiro")
    
    # Lista de modelos - apenas mostrar se há API key
    model = None
    if openai_key and openai_key.strip():
        if 'available_models' not in st.session_state:
            st.session_state.available_models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        
        model = st.selectbox(
            "Modelo:",
            st.session_state.available_models,
            help="Modelo a ser usado para avaliação"
        )
    else:
        st.info("ℹ️ Insira uma API Key para selecionar modelos")
    
    # Aplicar configurações - apenas mostrar se há API key e modelo
    if openai_key and openai_key.strip() and model:
        if st.button("💾 Aplicar Configurações", type="primary"):
            try:
                update_eval_llm(api_key=openai_key, model=model, base_url=base_url)
                os.environ["OPENAI_API_KEY"] = openai_key
                st.success("Configurações aplicadas com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao aplicar configurações: {str(e)}")
    elif openai_key and openai_key.strip() and not model:
        st.info("🔄 Clique em 'Buscar Modelos' para carregar os modelos disponíveis")
    elif not openai_key or not openai_key.strip():
        st.info("🔑 Configure uma API Key para continuar")
    
    # Mostrar informações do provedor atual (no final da sidebar)
    st.markdown("---")
    provider_info = eval_llm.get_info()
    api_key_configured = provider_info.get('api_key_set', False)
    current_model = provider_info.get('model', 'N/A') if api_key_configured else 'N/A (API Key necessária)'
    
    st.info(f"**Provedor:** {selected_provider}\n\n"
            f"**Modelo:** {current_model}\n\n"
            f"**API Key:** {'✅ Configurada' if api_key_configured else '❌ Não configurada'}")

st.title("Comparação de Textos com RAGAS")

# Tabs para diferentes modos
tab1, tab2 = st.tabs(["Avaliação Simples", "Avaliação Múltipla"])

with tab1:
    st.header("Text Comparison Evaluation - Simples")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Texto de Referência")
        reference_text = st.text_area(
            "Insira o texto de referência:",
            height=150,
            placeholder="Ex: A capital do Brasil é Brasília...",
            key="single_ref"
        )
    
    with col2:
        st.subheader("Texto Gerado")
        generated_text = st.text_area(
            "Insira o texto a ser avaliado:",
            height=150,
            placeholder="Ex: Brasília é a capital brasileira...",
            key="single_gen"
        )
    
    
    # Comparison type selection
    col1, col2, col3 = st.columns(3)
    
    with col1:
        comparison_type = st.selectbox(
            "Tipo de Comparação:",
            options=LABEL_OPTIONS,
            format_func=lambda x: LABEL_FORMAT.get(x, x),
            help="Escolha o tipo de comparação a ser realizada",
            key="single_comparison_type"
        )

    mode, atomicity_or_type = None, None
    with col2:
        if comparison_type == ComparisonType.FACTUAL_CORRECTNESS.value:
            mode = st.selectbox("Mode: ", ["F1", "Precision", "Recall"], key="single_mode")
            if mode:
                st.session_state.mode = mode.lower()
        elif comparison_type == ComparisonType.ROUGE_SCORE.value:
            mode = st.selectbox("Mode: ", ["fmeasure", "precision", "recall"], key="single_mode")
            if mode:
                st.session_state.mode = mode.lower()
                
    with col3:
        if comparison_type == ComparisonType.FACTUAL_CORRECTNESS.value:
            atomicity_or_type = st.selectbox("Atomicity: ", ["None", "High", "Low"], key="single_atomicity")
            if atomicity_or_type:
                st.session_state.atomicity_or_type = atomicity_or_type.lower()
        elif comparison_type == ComparisonType.ROUGE_SCORE.value:
            atomicity_or_type = st.selectbox("Rouge Type: ", ["rouge1", "rougeL"], key="single_atomicity")
            if atomicity_or_type:
                st.session_state.atomicity_or_type = atomicity_or_type.lower()

    if st.button("Comparar Textos", type="primary", key="single_compare"):
        if not reference_text or not generated_text:
            st.error("Por favor, insira ambos os textos.")
        elif not openai_key:
            st.error("Por favor, insira sua OpenAI API Key.")
        else:
            with st.spinner("Avaliando..."):
                try:
                    os.environ["OPENAI_API_KEY"] = openai_key
                    score = compare_texts_sync(
                        generated_text, 
                        reference_text,
                        comparison_type,
                        mode,
                        atomicity_or_type,
                        model, 
                        base_url
                    )
                    
                    st.success("Avaliação concluída!")
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        # Dynamic label based on comparison type
                        label = LABEL_FORMAT.get(comparison_type, comparison_type)
                        st.metric(
                            label=label,
                            value=f"{score:.3f}",
                            help=f"Score de 0 a 1, onde 1 indica {label} perfeita"
                        )
                    
                    if score >= 0.8:
                        st.success(f"✅ Alta {label}")
                    elif score >= 0.6:
                        st.warning(f"⚠️ Moderada {label}")
                    else:
                        st.error(f"❌ Baixa {label}")

                except Exception as e:
                    st.error(f"Erro na avaliação: {str(e)}")

with tab2:
    st.header("Comparação Múltipla - Tipos de Teste")
    
    # Adicionar funções JavaScript do localStorage
    # add_localStorage_functions()
    
    # Inicializar session state para tipos de teste
    if 'test_types' not in st.session_state:
        st.session_state.test_types = {}
    if 'current_test_type' not in st.session_state:
        st.session_state.current_test_type = None
    if 'test_results' not in st.session_state:
        st.session_state.test_results = {}
    
    # Gerenciamento de Tipos de Teste
    st.subheader("📁 Gerenciamento de Tipos de Teste")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        new_test_type_name = st.text_input(
            "Nome do Novo Tipo de Teste:",
            placeholder="Ex: Claude vs Gemma3, Teste A/B, etc.",
            key="new_test_type"
        )
    
    with col2:
        if st.button("➕ Criar Tipo", key="create_test_type"):
            if new_test_type_name and new_test_type_name.strip():
                if new_test_type_name not in st.session_state.test_types:
                    st.session_state.test_types[new_test_type_name] = {
                        'comparisons': [],
                        'created_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    st.session_state.current_test_type = new_test_type_name
                    
                    # Inicializar campos para o novo tipo
                    ref_key = f"multi_ref_{new_test_type_name}"
                    gen_key = f"multi_gen_{new_test_type_name}"
                    st.session_state.setdefault(ref_key, "")
                    st.session_state.setdefault(gen_key, "")
                    
                    st.success(f"Tipo '{new_test_type_name}' criado!")
                    st.rerun()
                else:
                    st.error("Tipo de teste já existe!")
            else:
                st.error("Digite um nome para o tipo de teste")
    
    with col3:
        if st.session_state.test_types and st.session_state.current_test_type:
            if st.button("🗑️ Excluir Tipo", key="delete_test_type"):
                if st.session_state.current_test_type in st.session_state.test_types:
                    del st.session_state.test_types[st.session_state.current_test_type]
                    if st.session_state.current_test_type in st.session_state.test_results:
                        del st.session_state.test_results[st.session_state.current_test_type]
                    
                    # Selecionar próximo tipo disponível ou None
                    if st.session_state.test_types:
                        st.session_state.current_test_type = list(st.session_state.test_types.keys())[0]
                    else:
                        st.session_state.current_test_type = None
                    st.rerun()
    
    # Seletor de tipo de teste atual
    if st.session_state.test_types:
        current_test = st.selectbox(
            "Tipo de Teste Ativo:",
            options=list(st.session_state.test_types.keys()),
            index=list(st.session_state.test_types.keys()).index(st.session_state.current_test_type) if st.session_state.current_test_type in st.session_state.test_types else 0,
            key="test_type_selector"
        )
        
        if current_test != st.session_state.current_test_type:
            # Salvar dados do tipo anterior antes de trocar
            if st.session_state.current_test_type:
                save_data_automatically(st.session_state.current_test_type)
            
            st.session_state.current_test_type = current_test
            
            # Carregar dados do novo tipo selecionado
            load_data_from_localStorage(current_test)
            
            # Mostrar mensagem de dados restaurados se existirem
            temp_key = f'temp_data_{current_test}'
            if temp_key in st.session_state and st.session_state[temp_key]:
                st.session_state['show_restore_message'] = True
            
            st.rerun()
        
        # Mostrar mensagem de restauração se configurada
        if st.session_state.get('show_restore_message', False):
            st.success(f"✅ Dados salvos para '{current_test}' foram restaurados automaticamente!")
            st.session_state['show_restore_message'] = False
        
        # Informações do tipo de teste atual
        test_info = st.session_state.test_types[current_test]
        st.info(f"📊 **{current_test}** | Criado em: {test_info['created_at']} | Iterações: {len(test_info['comparisons'])}")
    else:
        st.warning("📝 Nenhum tipo de teste criado. Crie um tipo de teste para começar.")
        current_test = None
    
    # Só continuar se há um tipo de teste selecionado
    if not current_test:
        st.stop()
    
    st.divider()
    
    # Configurações de avaliação múltipla
    st.subheader("⚙️ Configurações de Avaliação")
    
    # Carregar dados salvos para o tipo atual
    if current_test:
        load_data_from_localStorage(current_test)
    
    # On change handler
    on_change_callback = lambda: save_data_automatically(current_test)
    
    # Comparison type selection for multiple evaluations
    comparison_types_multi = st.multiselect(
        "Tipos de Comparação:",
        options=LABEL_OPTIONS,
        default=st.session_state.get('multi_comparison_types', [ComparisonType.FACTUAL_CORRECTNESS.value]),
        on_change=on_change_callback,
        format_func=lambda x: LABEL_FORMAT.get(x, x),
        help="Escolha os tipos de comparação a serem aplicados",
        key="multi_comparison_types"
    )
    
    # Definir opções de avaliação disponíveis baseadas nos tipos selecionados
    evaluation_options = []
    
    if ComparisonType.FACTUAL_CORRECTNESS.value in comparison_types_multi:
        evaluation_options.extend([
            "Factual Correctness - Mode: F1, Atomicity: None",
            "Factual Correctness - Mode: F1, Atomicity: High", 
            "Factual Correctness - Mode: F1, Atomicity: Low",
            "Factual Correctness - Mode: Precision, Atomicity: None",
            "Factual Correctness - Mode: Precision, Atomicity: High",
            "Factual Correctness - Mode: Precision, Atomicity: Low",
            "Factual Correctness - Mode: Recall, Atomicity: None",
            "Factual Correctness - Mode: Recall, Atomicity: High",
            "Factual Correctness - Mode: Recall, Atomicity: Low"
        ])
    
    if ComparisonType.SEMANTIC_SIMILARITY.value in comparison_types_multi:
        evaluation_options.extend([
            "Semantic Similarity"
        ])
        
    if ComparisonType.NON_LLM_STRING_SIMILARITY.value in comparison_types_multi:
        evaluation_options.extend([
            "Non LLM String Similarity"
        ])
    
    if ComparisonType.BLEU_SCORE.value in comparison_types_multi:
        evaluation_options.extend([
            "BLEU Score"
        ])
        
    if ComparisonType.ROUGE_SCORE.value in comparison_types_multi:
        evaluation_options.extend([
            "ROUGE Score - Mode: Fmeasure, Rouge-Type: Rouge1",
            "ROUGE Score - Mode: Precision, Rouge-Type: Rouge1",
            "ROUGE Score - Mode: Recall, Rouge-Type: Rouge1",
            "ROUGE Score - Mode: Fmeasure, Rouge-Type: RougeL",
            "ROUGE Score - Mode: Precision, Rouge-Type: RougeL",
            "ROUGE Score - Mode: Recall, Rouge-Type: RougeL"
        ])
    
    # Definir opções de avaliação disponíveis (DEFAULT)
    evaluation_options_original = [
        "Factual Correctness - Mode: F1, Atomicity: None",
        "Factual Correctness - Mode: F1, Atomicity: High", 
        "Factual Correctness - Mode: F1, Atomicity: Low",
        "Factual Correctness - Mode: Precision, Atomicity: None",
        "Factual Correctness - Mode: Precision, Atomicity: High",
        "Factual Correctness - Mode: Precision, Atomicity: Low",
        "Factual Correctness - Mode: Recall, Atomicity: None",
        "Factual Correctness - Mode: Recall, Atomicity: High",
        "Factual Correctness - Mode: Recall, Atomicity: Low"
    ]
    
    # Definir valores padrão com base no que está salvo ou usar padrão
    default_evaluations = st.session_state.get('selected_evaluations_for_storage', 
                                              ["Factual Correctness - Mode: F1, Atomicity: None"] if evaluation_options else [])
    
    selected_evaluations = st.multiselect(
        "Selecione os tipos de avaliação:",
        options=evaluation_options if evaluation_options else evaluation_options_original,
        default=default_evaluations,
        on_change=on_change_callback,
        help="Escolha uma ou mais configurações de avaliação para aplicar a todas as comparações",
        key="selected_evaluations_multiselect"
    )
    
    # Salvar seleção atual no session_state
    st.session_state['selected_evaluations_for_storage'] = selected_evaluations
    
    if not comparison_types_multi:
        st.warning("⚠️ Selecione pelo menos um tipo de comparação.")
    elif not selected_evaluations:
        st.warning("⚠️ Selecione pelo menos um tipo de avaliação.")
    
    # Indicador de dados salvos e opção para limpar
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info(f"💾 Dados do tipo '{current_test}' são salvos automaticamente")
    with col2:
        if st.button("🗑️ Limpar Dados Salvos", key=f"clear_data_{current_test}"):
            # Limpar session_state
            temp_key = f'temp_data_{current_test}'
            if temp_key in st.session_state:
                del st.session_state[temp_key]
            
            # Limpar campos de texto
            st.session_state[f'multi_ref_{current_test}'] = ''
            st.session_state[f'multi_gen_{current_test}'] = ''
            
            # Não limpar as configurações globais, apenas para este tipo
            st.success(f"Dados do tipo '{current_test}' foram limpos!")
            st.rerun()
    with col3:
        # Botão para mostrar dados salvos (debug)
        if st.button("🔍 Ver Dados Salvos", key=f"show_data_{current_test}"):
            temp_key = f'temp_data_{current_test}'
            if temp_key in st.session_state:
                st.json(st.session_state[temp_key])
            else:
                st.info("Nenhum dado salvo encontrado")
    
    st.divider()
    
    # Input para nova iteração
    st.subheader(f"Adicionar Nova Iteração - {current_test}")
    
    col1, col2 = st.columns([1, 1])
    
    # Garantir que os campos existam no session_state antes de criar os widgets
    ref_key = f"multi_ref_{current_test}"
    gen_key = f"multi_gen_{current_test}"
    
    # Usar setdefault para garantir inicialização segura
    st.session_state.setdefault(ref_key, "")
    st.session_state.setdefault(gen_key, "")
    
    with col1:
        new_reference = st.text_area(
            "Texto de Referência:",
            height=120,
            on_change=on_change_callback,
            key=ref_key,
            help="Os dados serão salvos automaticamente quando você trocar de tipo de teste"
        )
    
    with col2:
        new_generated = st.text_area(
            "Texto Gerado:",
            height=120,
            on_change=on_change_callback,
            key=gen_key,
            help="Os dados serão salvos automaticamente quando você trocar de tipo de teste"
        )

    # Auto-save: Salvar automaticamente apenas quando trocar de tipo
    if current_test:
        save_data_automatically(current_test)
    
    col1, col2 = st.columns([2, 1])
    
    current_comparisons = st.session_state.test_types[current_test]['comparisons']
    with col1:
        st.info(f"Próxima iteração será: Iteração {len(current_comparisons) + 1}")
    
    with col2:
        if st.button("➕ Adicionar Iteração", key=f"add_comparison_{current_test}"):
            if new_reference and new_generated:
                iteration_number = len(current_comparisons) + 1
                st.session_state.test_types[current_test]['comparisons'].append({
                    'iteration': iteration_number,
                    'reference': new_reference,
                    'generated': new_generated
                })
                st.success(f"Iteração {iteration_number} adicionada ao tipo '{current_test}'!")
                st.rerun()
            else:
                st.error("Preencha ambos os campos de texto")
    
    # Mostrar iterações adicionadas
    if current_comparisons:
        st.subheader(f"Iterações do Tipo '{current_test}' ({len(current_comparisons)})")
        
        # Mostrar lista das iterações
        for i, comp in enumerate(current_comparisons):
            with st.expander(f"Iteração {comp['iteration']}", expanded=False):
                col1, col2, col3 = st.columns([3, 3, 1])
                with col1:
                    st.text_area("Referência:", value=comp['reference'], height=80, disabled=True, key=f"ref_{current_test}_{i}")
                with col2:
                    st.text_area("Gerado:", value=comp['generated'], height=80, disabled=True, key=f"gen_{current_test}_{i}")
                with col3:
                    if st.button("❌", key=f"remove_{current_test}_{i}", help="Remover iteração"):
                        # Reorganizar números das iterações após remoção
                        st.session_state.test_types[current_test]['comparisons'].pop(i)
                        # Renumerar iterações
                        for j, item in enumerate(st.session_state.test_types[current_test]['comparisons']):
                            item['iteration'] = j + 1
                        st.rerun()
        
        # Botão para avaliar todas
        if st.button("🚀 Avaliar Todas as Iterações", type="primary", key=f"multi_compare_{current_test}"):
            if not openai_key:
                st.error("Por favor, insira sua OpenAI API Key.")
            elif not selected_evaluations:
                st.error("Por favor, selecione pelo menos um tipo de avaliação.")
            else:
                # Executar avaliações múltiplas
                import plotly.graph_objects as go
                
                def parse_evaluation_config(eval_string):
                    # Parse "Factual Correctness - Mode: F1, Atomicity: None" or "Semantic Similarity - Default Configuration"
                    if eval_string.startswith("Factual Correctness"):
                        parts = eval_string.split(" - ")[1].split(", ")
                        mode = parts[0].split(": ")[1].lower()
                        atomicity = parts[1].split(": ")[1].lower()
                        return ComparisonType.FACTUAL_CORRECTNESS.value, mode, atomicity
                    elif eval_string.startswith("Semantic Similarity"):
                        return ComparisonType.SEMANTIC_SIMILARITY.value, None, None
                    elif eval_string.startswith("Non LLM String Similarity"):
                        return ComparisonType.NON_LLM_STRING_SIMILARITY.value, None, None
                    elif eval_string.startswith("BLEU Score"):
                        return ComparisonType.BLEU_SCORE.value, None, None
                    elif eval_string.startswith("ROUGE Score"):
                        parts = eval_string.split(" - ")[1].split(", ")
                        mode = parts[0].split(": ")[1].lower()
                        rouge_type = parts[1].split(": ")[1].lower()
                        return ComparisonType.ROUGE_SCORE.value, mode, rouge_type
                    else:
                        return ComparisonType.FACTUAL_CORRECTNESS.value, "f1", "none"
                
                os.environ["OPENAI_API_KEY"] = openai_key
                all_results = []
                
                total_evaluations = len(current_comparisons) * len(selected_evaluations)
                progress_bar = st.progress(0)
                status_text = st.empty()
                evaluation_count = 0
                
                # Para cada iteração
                for comp in current_comparisons:
                    comp_results = {'iteration': f"Iteração {comp['iteration']}"}
                    
                    # Para cada tipo de avaliação selecionado
                    for eval_config in selected_evaluations:
                        evaluation_count += 1
                        comparison_type, mode, atomicity_or_type = parse_evaluation_config(eval_config)
                        
                        status_text.text(f"Avaliando: Iteração {comp['iteration']} - {eval_config}")
                        
                        try:
                            score = compare_texts_sync(
                                comp['generated'],
                                comp['reference'],
                                comparison_type,
                                mode,
                                atomicity_or_type,
                                model,
                                base_url
                            )
                            comp_results[eval_config] = score
                        except Exception as e:
                            comp_results[eval_config] = f"Error: {str(e)}"
                        
                        progress_bar.progress(evaluation_count / total_evaluations)
                    
                    all_results.append(comp_results)
                
                status_text.text("Avaliação concluída!")
                
                # Armazenar resultados por tipo de teste
                st.session_state.test_results[current_test] = {
                    'results': all_results,
                    'evaluations': selected_evaluations,
                    'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Visualizar resultados
                st.subheader(f"Resultados das Avaliações - {current_test}")
                
                # Criar DataFrame para visualização
                df_results = pd.DataFrame(all_results)
                
                # Preparar dados para gráfico de barras com médias
                bar_data = []
                
                for eval_config in selected_evaluations:
                    scores = []
                    for result in all_results:
                        if isinstance(result[eval_config], (int, float)):
                            scores.append(result[eval_config])
                    
                    if scores:  # Se há scores válidos
                        # Clean up the evaluation name for display
                        clean_name = eval_config.replace("Factual Correctness - ", "FC - ").replace("Semantic Similarity - ", "SS - ")
                        media_scores = sum(scores) / len(scores)
                        bar_data.append({
                            'evaluation': clean_name,
                            'media': media_scores
                        })
                
                # Criar gráfico de barras
                fig = go.Figure()
                
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']
                
                evaluations = [data['evaluation'] for data in bar_data]
                medias = [data['media'] for data in bar_data]
                
                fig.add_trace(go.Bar(
                    x=evaluations,
                    y=medias,
                    marker_color=[colors[i % len(colors)] for i in range(len(evaluations))],
                    text=[f"{media:.3f}" for media in medias],
                    textposition='outside'
                ))
                
                fig.update_layout(
                    title="Média dos Scores por Tipo de Avaliação",
                    xaxis_title="Tipo de Avaliação",
                    yaxis_title="Score Médio",
                    yaxis=dict(range=[0, max(1, max(medias) * 1.1) if medias else 1]),
                    height=600,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar resumo estatístico
                st.subheader("Resumo Estatístico por Avaliação")
                
                summary_data = []
                for eval_config in selected_evaluations:
                    scores = []
                    for result in all_results:
                        if isinstance(result[eval_config], (int, float)):
                            scores.append(result[eval_config])
                    
                    if scores:  # Se há scores válidos
                        # Clean up the evaluation name for display
                        clean_name = eval_config.replace("Factual Correctness - ", "FC - ").replace("Semantic Similarity - ", "SS - ")
                        summary_data.append({
                            'Avaliação': clean_name,
                            'Média': f"{sum(scores) / len(scores):.3f}",
                            'Mediana': f"{sorted(scores)[len(scores)//2]:.3f}",
                            'Mínimo': f"{min(scores):.3f}",
                            'Máximo': f"{max(scores):.3f}",
                            'Desvio Padrão': f"{(sum([(x - sum(scores)/len(scores))**2 for x in scores]) / len(scores))**0.5:.3f}",
                            'Iterações': len(scores)
                        })
                
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
                
                # Tabela detalhada por iteração
                st.subheader("Resultados Detalhados por Iteração")
                
                # Preparar dados para exibição
                display_df = df_results.copy()
                
                # Formatar colunas numéricas
                for col in display_df.columns:
                    if col != 'iteration':
                        display_df[col] = display_df[col].apply(
                            lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else str(x)
                        )
                
                st.dataframe(display_df, use_container_width=True)
    
    else:
        st.info(f"Nenhuma iteração adicionada ao tipo '{current_test}'. Use os campos acima para adicionar iterações.")
    
    # Seção de visualização de resultados de diferentes tipos de teste
    if st.session_state.test_results:
        st.divider()
        st.subheader("📊 Comparação entre Tipos de Teste")
        
        # Seletor para visualizar resultados de diferentes tipos
        available_results = list(st.session_state.test_results.keys())
        
        # Gráfico combinado com todos os tipos de teste
        display_combined_results(available_results)
        
        st.divider()
        
        # Seção de geração de relatórios
        st.subheader("📄 Geração de Relatórios")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.info("Gere relatórios detalhados com todos os resultados das avaliações")
        
        with col2:
            if st.button("📥 Gerar Relatório PDF", type="primary"):
                try:
                    with st.spinner("Gerando relatório PDF..."):
                        pdf_content = generate_pdf_report(st.session_state.test_results, st.session_state.test_types)
                    
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_content,
                        file_name=f"relatorio_ragas_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                    st.success("Relatório PDF gerado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao gerar relatório PDF: {str(e)}")
        
        with col3:
            if st.button("📄 Gerar Relatório DOCX"):
                try:
                    with st.spinner("Gerando relatório DOCX..."):
                        docx_content = generate_docx_report(st.session_state.test_results, st.session_state.test_types)
                    
                    st.download_button(
                        label="⬇️ Download DOCX",
                        data=docx_content,
                        file_name=f"relatorio_ragas_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    st.success("Relatório DOCX gerado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao gerar relatório DOCX: {str(e)}")
        
        # Seção de Import/Export de Dados
        st.divider()
        st.subheader("💾 Importação/Exportação de Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📤 Exportar Sessão**")
            st.info("Salva todos os tipos de teste, iterações e resultados da sessão atual")
            
            if st.button("📥 Exportar Dados da Sessão", type="primary"):
                try:
                    json_data = export_session_data()
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json_data,
                        file_name=f"comparagas_sessao_{timestamp}.json",
                        mime="application/json"
                    )
                    st.success("✅ Dados da sessão exportados! Clique no botão acima para fazer download.")
                except Exception as e:
                    st.error(f"Erro ao exportar dados: {str(e)}")
        
        with col2:
            st.markdown("**📤 Importar Sessão**")
            st.info("Carrega uma sessão previamente exportada (substitui dados atuais)")
            
            uploaded_file = st.file_uploader(
                "Selecione o arquivo JSON da sessão:",
                type=['json'],
                accept_multiple_files=False,
                key="import_session_file"
            )
            
            if uploaded_file is not None:
                try:
                    # Lê o conteúdo do arquivo
                    json_content = uploaded_file.getvalue().decode('utf-8')
                    
                    # Preview dos dados
                    try:
                        preview_data = json.loads(json_content)
                        metadata = preview_data.get('metadata', {})
                        
                        st.info(f"""
                        **Preview do arquivo:**
                        - Data de exportação: {metadata.get('export_timestamp', 'N/A')}
                        - Versão: {metadata.get('version', 'N/A')}
                        - Tipos de teste: {len(preview_data.get('test_types', {}))}
                        - Resultados: {len(preview_data.get('test_results', {}))}
                        """)
                        
                        # Botão para confirmar importação
                        if st.button("🔄 Confirmar Importação", type="secondary", key="confirm_import"):
                            success, message = import_session_data(json_content)
                            if success:
                                st.success(f"✅ {message}")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                                
                    except json.JSONDecodeError:
                        st.error("❌ Arquivo JSON inválido")
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {str(e)}")
        
        st.divider()
        
        # Tabs para visualização detalhada individual
        st.subheader("📋 Detalhes por Tipo de Teste")
        
        if len(available_results) == 1:
            display_results_for_test_type(available_results[0])
        else:
            result_tabs = st.tabs([f"📈 {test_type}" for test_type in available_results])
            
            for i, test_type in enumerate(available_results):
                with result_tabs[i]:
                    display_results_for_test_type(test_type)

st.markdown("---")
st.markdown("*Powered by RAGAS - Factual Correctness Evaluation*")
