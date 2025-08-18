import streamlit as st
import os
from utils.ragas_text_comparison import LABEL_FORMAT, compare_texts_sync, ComparisonType
from utils.llm import eval_llm, update_eval_llm

st.set_page_config(page_title="RAGAS Text Comparison", layout="wide")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Mostrar informações do provedor atual
    provider_info = eval_llm.get_info()
    api_key_configured = provider_info.get('api_key_set', False)
    current_model = provider_info.get('model', 'N/A') if api_key_configured else 'N/A (API Key necessária)'
    
    st.info(f"**Provedor:** {provider_info.get('provider', 'OpenAI')}\n\n"
            f"**Modelo:** {current_model}\n\n"
            f"**API Key:** {'✅ Configurada' if api_key_configured else '❌ Não configurada'}")

    # Seleção do tipo de endpoint
    use_custom_endpoint = st.checkbox(
        "Usar endpoint personalizado",
        help="Marque para usar um endpoint diferente do OpenAI oficial"
    )

    openai_key = st.text_input(
        "API Key:",
        type="password",
        help="Necessário para usar RAGAS"
    )
    
    # Base URL apenas se usar endpoint personalizado
    if use_custom_endpoint:
        base_url = st.text_input(
            "Base URL:",
            value="https://api.openai.com/v1",
            help="URL base da API OpenAI ou provedor compatível"
        )
    else:
        base_url = "https://api.openai.com/v1"
    
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
            options=[ComparisonType.FACTUAL_CORRECTNESS.value, ComparisonType.SEMANTIC_SIMILARITY.value],
            format_func=lambda x: LABEL_FORMAT.get(x, x),
            help="Escolha o tipo de comparação a ser realizada",
            key="single_comparison_type"
        )

    mode, atomicity = None, None
    with col2:
        if comparison_type == ComparisonType.FACTUAL_CORRECTNESS.value:
            mode = st.selectbox("Mode: ", ["F1", "Precision", "Recall"], key="single_mode")
            if mode:
                st.session_state.mode = mode.lower()
    with col3:
        if comparison_type == ComparisonType.FACTUAL_CORRECTNESS.value:
            atomicity = st.selectbox("Atomicity: ", ["None", "High", "Low"], key="single_atomicity")
            if atomicity:
                st.session_state.atomicity = atomicity.lower()

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
                        atomicity,
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
    st.header("Comparação Múltipla - Lado a Lado")
    
    # Inicializar session state para comparações múltiplas
    if 'comparisons' not in st.session_state:
        st.session_state.comparisons = []
    
    # Configurações de avaliação múltipla
    st.subheader("⚙️ Configurações de Avaliação")
    
    # Comparison type selection for multiple evaluations
    comparison_types_multi = st.multiselect(
        "Tipos de Comparação:",
        options=[ComparisonType.FACTUAL_CORRECTNESS.value, ComparisonType.SEMANTIC_SIMILARITY.value],
        default=[ComparisonType.FACTUAL_CORRECTNESS.value],
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
            "Semantic Similarity - Default Configuration"
        ])
    
    # Definir opções de avaliação disponíveis
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
    
    selected_evaluations = st.multiselect(
        "Selecione os tipos de avaliação:",
        options=evaluation_options if evaluation_options else evaluation_options_original,
        default=["Factual Correctness - Mode: F1, Atomicity: None"] if evaluation_options else [],
        help="Escolha uma ou mais configurações de avaliação para aplicar a todas as comparações"
    )
    
    if not comparison_types_multi:
        st.warning("⚠️ Selecione pelo menos um tipo de comparação.")
    elif not selected_evaluations:
        st.warning("⚠️ Selecione pelo menos um tipo de avaliação.")
    
    # Input para nova iteração
    st.subheader("Adicionar Nova Iteração")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        new_reference = st.text_area(
            "Texto de Referência:",
            height=120,
            key="multi_ref"
        )
    
    with col2:
        new_generated = st.text_area(
            "Texto Gerado:",
            height=120,
            key="multi_gen"
        )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info(f"Próxima iteração será: Iteração {len(st.session_state.comparisons) + 1}")
    
    with col2:
        if st.button("➕ Adicionar Iteração", key="add_comparison"):
            if new_reference and new_generated:
                iteration_number = len(st.session_state.comparisons) + 1
                st.session_state.comparisons.append({
                    'iteration': iteration_number,
                    'reference': new_reference,
                    'generated': new_generated
                })
                st.success(f"Iteração {iteration_number} adicionada!")
                st.rerun()
            else:
                st.error("Preencha ambos os campos de texto")
    
    # Mostrar iterações adicionadas
    if st.session_state.comparisons:
        st.subheader(f"Iterações Adicionadas ({len(st.session_state.comparisons)})")
        
        # Mostrar lista das iterações
        for i, comp in enumerate(st.session_state.comparisons):
            with st.expander(f"Iteração {comp['iteration']}", expanded=False):
                col1, col2, col3 = st.columns([3, 3, 1])
                with col1:
                    st.text_area("Referência:", value=comp['reference'], height=80, disabled=True, key=f"ref_{i}")
                with col2:
                    st.text_area("Gerado:", value=comp['generated'], height=80, disabled=True, key=f"gen_{i}")
                with col3:
                    if st.button("❌", key=f"remove_{i}", help="Remover iteração"):
                        # Reorganizar números das iterações após remoção
                        st.session_state.comparisons.pop(i)
                        # Renumerar iterações
                        for j, item in enumerate(st.session_state.comparisons):
                            item['iteration'] = j + 1
                        st.rerun()
        
        # Botão para avaliar todas
        if st.button("🚀 Avaliar Todas as Iterações", type="primary", key="multi_compare"):
            if not openai_key:
                st.error("Por favor, insira sua OpenAI API Key.")
            elif not selected_evaluations:
                st.error("Por favor, selecione pelo menos um tipo de avaliação.")
            else:
                # Executar avaliações múltiplas
                import plotly.graph_objects as go
                import pandas as pd
                
                def parse_evaluation_config(eval_string):
                    # Parse "Factual Correctness - Mode: F1, Atomicity: None" or "Semantic Similarity - Default Configuration"
                    if eval_string.startswith("Factual Correctness"):
                        parts = eval_string.split(" - ")[1].split(", ")
                        mode = parts[0].split(": ")[1].lower()
                        atomicity = parts[1].split(": ")[1].lower()
                        return ComparisonType.FACTUAL_CORRECTNESS.value, mode, atomicity
                    elif eval_string.startswith("Semantic Similarity"):
                        return ComparisonType.SEMANTIC_SIMILARITY.value, None, None
                    else:
                        return ComparisonType.FACTUAL_CORRECTNESS.value, "f1", "none"
                
                os.environ["OPENAI_API_KEY"] = openai_key
                all_results = []
                
                total_evaluations = len(st.session_state.comparisons) * len(selected_evaluations)
                progress_bar = st.progress(0)
                status_text = st.empty()
                evaluation_count = 0
                
                # Para cada iteração
                for comp in st.session_state.comparisons:
                    comp_results = {'iteration': f"Iteração {comp['iteration']}"}
                    
                    # Para cada tipo de avaliação selecionado
                    for eval_config in selected_evaluations:
                        evaluation_count += 1
                        comparison_type, mode, atomicity = parse_evaluation_config(eval_config)
                        
                        status_text.text(f"Avaliando: Iteração {comp['iteration']} - {eval_config}")
                        
                        try:
                            score = compare_texts_sync(
                                comp['generated'],
                                comp['reference'],
                                comparison_type,
                                mode,
                                atomicity,
                                model,
                                base_url
                            )
                            comp_results[eval_config] = score
                        except Exception as e:
                            comp_results[eval_config] = f"Error: {str(e)}"
                        
                        progress_bar.progress(evaluation_count / total_evaluations)
                    
                    all_results.append(comp_results)
                
                status_text.text("Avaliação concluída!")
                
                # Visualizar resultados
                st.subheader("Resultados das Avaliações por Iteração")
                
                # Criar DataFrame para visualização
                df_results = pd.DataFrame(all_results)
                
                # Preparar dados para boxplot
                boxplot_data = []
                
                for eval_config in selected_evaluations:
                    scores = []
                    for result in all_results:
                        if isinstance(result[eval_config], (int, float)):
                            scores.append(result[eval_config])
                    
                    if scores:  # Se há scores válidos
                        # Clean up the evaluation name for display
                        clean_name = eval_config.replace("Factual Correctness - ", "FC - ").replace("Semantic Similarity - ", "SS - ")
                        boxplot_data.append({
                            'evaluation': clean_name,
                            'scores': scores
                        })
                
                # Criar boxplot
                fig = go.Figure()
                
                colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']
                
                for i, data in enumerate(boxplot_data):
                    fig.add_trace(go.Box(
                        y=data['scores'],
                        name=data['evaluation'],
                        marker_color=colors[i % len(colors)],
                        boxpoints='all',  # Mostrar todos os pontos
                        jitter=0.3,  # Espalhar pontos horizontalmente
                        pointpos=-1.8  # Posição dos pontos
                    ))
                
                fig.update_layout(
                    title="Distribuição de Scores por Tipo de Avaliação",
                    xaxis_title="Tipo de Avaliação",
                    yaxis_title="Score",
                    yaxis=dict(range=[0, 1]),
                    height=600,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar resumo estatístico
                st.subheader("Resumo Estatístico por Avaliação")
                
                summary_data = []
                for data in boxplot_data:
                    scores = data['scores']
                    if scores:
                        summary_data.append({
                            'Avaliação': data['evaluation'],
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
        st.info("Nenhuma iteração adicionada ainda. Use os campos acima para adicionar iterações.")

st.markdown("---")
st.markdown("*Powered by RAGAS - Factual Correctness Evaluation*")