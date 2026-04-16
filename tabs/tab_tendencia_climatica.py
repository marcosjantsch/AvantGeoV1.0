from datetime import datetime
import streamlit as st


def render_tab_tendencia_climatica(
    gdf_filtered,
    selected_empresa=None,
    selected_fazenda=None,
    selected_municipio=None,
    selected_uf=None,
    logo_path=None,
):
    st.markdown('<div class="section-title">Tendência Climática</div>', unsafe_allow_html=True)

    if gdf_filtered is None or gdf_filtered.empty:
        st.warning("⚠️ Não há geometria filtrada para calcular o centróide.")
        return

    geom = _build_target_geometry(gdf_filtered)
    if geom is None or geom.is_empty:
        st.error("❌ Não foi possível obter a geometria da área selecionada.")
        return

    centroid = geom.centroid
    lat = float(centroid.y)
    lon = float(centroid.x)

    titulo_local = _descricao_local(
        selected_empresa=selected_empresa,
        selected_fazenda=selected_fazenda,
        selected_municipio=selected_municipio,
        selected_uf=selected_uf,
    )

    contexto = {
        "lat": lat,
        "lon": lon,
        "selected_empresa": selected_empresa,
        "selected_fazenda": selected_fazenda,
        "selected_municipio": selected_municipio,
        "selected_uf": selected_uf,
        "titulo_local": titulo_local,
        "nome_local": _nome_local_texto(
            selected_empresa=selected_empresa,
            selected_fazenda=selected_fazenda,
            selected_municipio=selected_municipio,
            selected_uf=selected_uf,
        ),
    }

    st.markdown(f"### {titulo_local}")
    st.caption(f"Consulta espacial baseada no centróide | Latitude: {lat:.6f} | Longitude: {lon:.6f}")

    with st.expander("Fonte dos dados", expanded=False):
        st.markdown(
            f"""
**Tipo de informação exibida:** tendência climática sazonal interpretativa  
**Área consultada:** centróide da geometria filtrada  
**Latitude:** `{lat:.6f}`  
**Longitude:** `{lon:.6f}`  

**Estrutura atual da aba:**  
Esta versão apresenta interpretação climática sazonal inicial baseada no contexto geográfico da área selecionada.

**Objetivo:**  
- apoiar planejamento florestal e operacional  
- destacar possibilidade de período mais seco ou mais úmido  
- sinalizar comportamento climático regional esperado  

**Observação importante:**  
O conteúdo exibido nesta aba deve ser interpretado como apoio ao planejamento,  
não como previsão diária determinística.
"""
        )

    dados_3_meses = _gerar_tendencia_3_meses(contexto)
    dados_6_meses = _gerar_tendencia_6_meses(contexto)

    st.markdown("---")
    st.markdown("#### Tendência Climática — Próximos 3 meses")
    _render_bloco_tendencia(
        titulo="Próximos 3 meses",
        texto=dados_3_meses["texto"],
        fonte=dados_3_meses["fonte"],
        data_referencia=dados_3_meses["data_referencia"],
        data_emissao=dados_3_meses["data_emissao"],
    )

    st.markdown("---")
    st.markdown("#### Tendência Climática — Próximos 6 meses")
    _render_bloco_tendencia(
        titulo="Próximos 6 meses",
        texto=dados_6_meses["texto"],
        fonte=dados_6_meses["fonte"],
        data_referencia=dados_6_meses["data_referencia"],
        data_emissao=dados_6_meses["data_emissao"],
    )

    st.markdown("---")
    st.markdown("#### Observação")
    st.caption(
        "A tendência climática apresentada nesta aba deve ser utilizada como suporte ao planejamento "
        "e interpretada em conjunto com a previsão do tempo de curto prazo."
    )

    if logo_path:
        st.markdown("---")
        st.image(logo_path, width=180)


def _build_target_geometry(gdf):
    try:
        return gdf.geometry.union_all()
    except Exception:
        try:
            return gdf.unary_union
        except Exception:
            return None


def _descricao_local(
    selected_empresa=None,
    selected_fazenda=None,
    selected_municipio=None,
    selected_uf=None,
):
    if selected_empresa and selected_fazenda:
        return f"Tendência climática para {selected_empresa} | {selected_fazenda}"
    if selected_empresa:
        return f"Tendência climática para {selected_empresa}"
    if selected_municipio and selected_uf:
        return f"Tendência climática para {selected_municipio}/{selected_uf}"
    if selected_municipio:
        return f"Tendência climática para {selected_municipio}"
    return "Tendência climática da área selecionada"


def _nome_local_texto(
    selected_empresa=None,
    selected_fazenda=None,
    selected_municipio=None,
    selected_uf=None,
):
    if selected_empresa and selected_fazenda:
        return f"{selected_empresa} / {selected_fazenda}"
    if selected_empresa:
        return str(selected_empresa)
    if selected_municipio and selected_uf:
        return f"{selected_municipio}/{selected_uf}"
    if selected_municipio:
        return str(selected_municipio)
    return "a área selecionada"


def _classificar_regiao(lat, lon):
    if lat < -23:
        return "Sul"
    elif lat < -15:
        return "Sudeste"
    elif lat < -8:
        return "Centro-Oeste"
    elif lat < -2:
        return "Nordeste"
    else:
        return "Norte"


def _gerar_icones_tendencia(texto: str) -> str:
    texto_lower = str(texto).lower()
    icones = []

    if any(p in texto_lower for p in [
        "seca", "estiagem", "déficit hídrico", "deficit hídrico",
        "mais seco", "período seco", "periodo seco",
        "restrição hídrica", "restricao hídrica",
        "estresse hídrico", "estresse hidrico"
    ]):
        icones.append("🔥")

    if any(p in texto_lower for p in [
        "chuva", "chuvas", "precipitação", "precipitacao",
        "úmido", "umido", "úmidas", "umidas",
        "mais úmido", "mais umido"
    ]):
        icones.append("🌧")

    if any(p in texto_lower for p in [
        "temperatura", "temperaturas", "calor",
        "acima da média", "acima da media", "temperaturas elevadas"
    ]):
        icones.append("🌡")

    return " ".join(icones) if icones else "🌍"


def _render_bloco_tendencia(
    titulo: str,
    texto: str,
    fonte: str,
    data_referencia: str,
    data_emissao: str,
):
    icones = _gerar_icones_tendencia(texto)

    texto_html = str(texto).replace("\n", "<br><br>")
    fonte_html = str(fonte).replace("\n", "<br>")
    referencia_html = str(data_referencia).replace("\n", "<br>")
    emissao_html = str(data_emissao).replace("\n", "<br>")

    html = (
        f'<div style="background-color:#e8f5e9;'
        f'border-left:6px solid #2e7d32;'
        f'padding:18px 20px;'
        f'border-radius:10px;'
        f'margin-top:8px;'
        f'margin-bottom:8px;">'

        f'<div style="font-size:1.20rem;'
        f'font-weight:700;'
        f'color:#1b5e20;'
        f'margin-bottom:12px;">'
        f'{icones} {titulo}'
        f'</div>'

        f'<p style="font-size:1.10rem;'
        f'line-height:1.80;'
        f'color:#1f1f1f;'
        f'margin:0 0 14px 0;'
        f'text-align:justify;">'
        f'{texto_html}'
        f'</p>'

        f'<div style="font-size:0.96rem;'
        f'color:#2f4f2f;'
        f'border-top:1px solid #c8e6c9;'
        f'padding-top:10px;'
        f'line-height:1.65;">'
        f'<strong>Fonte:</strong> {fonte_html}<br>'
        f'<strong>Referência:</strong> {referencia_html}<br>'
        f'<strong>Data da emissão/geração:</strong> {emissao_html}'
        f'</div>'

        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def _data_execucao_formatada() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def _periodo_referencia_meses(qtd_meses: int) -> str:
    agora = datetime.now()
    mes = agora.month
    ano = agora.year

    nomes = {
        1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
        7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"
    }

    fim_mes = mes + qtd_meses - 1
    fim_ano = ano

    while fim_mes > 12:
        fim_mes -= 12
        fim_ano += 1

    return f"{nomes[mes]}/{ano} a {nomes[fim_mes]}/{fim_ano}"


def _gerar_tendencia_3_meses(contexto: dict) -> dict:
    nome_local = contexto.get("nome_local", "a área selecionada")
    lat = contexto.get("lat")
    lon = contexto.get("lon")
    regiao = _classificar_regiao(lat, lon)

    if regiao == "Sul":
        texto = (
            f"Para {nome_local}, a tendência climática para os próximos 3 meses indica maior variabilidade "
            f"na precipitação, com possibilidade de alternância entre períodos mais úmidos e intervalos secos. "
            f"Em termos operacionais, recomenda-se atenção à irregularidade hídrica, à condição do solo e ao "
            f"planejamento das atividades sensíveis à chuva."
        )
    elif regiao == "Sudeste":
        texto = (
            f"Para {nome_local}, a tendência para os próximos 3 meses aponta para redução gradual das chuvas "
            f"em parte do período, com possibilidade de temperaturas acima da média regional. "
            f"Do ponto de vista operacional, isso pode favorecer o avanço de estiagem e exigir monitoramento "
            f"mais próximo da disponibilidade hídrica."
        )
    elif regiao == "Centro-Oeste":
        texto = (
            f"Para {nome_local}, a tendência climática para os próximos 3 meses indica um padrão mais seco, "
            f"com menor frequência de chuvas e maior potencial de restrição hídrica. "
            f"A condição sugere atenção reforçada para déficit hídrico, risco operacional e sensibilidade "
            f"das atividades de campo ao comportamento da umidade."
        )
    elif regiao == "Nordeste":
        texto = (
            f"Para {nome_local}, a tendência climática para os próximos 3 meses aponta para irregularidade "
            f"na distribuição das chuvas, com possibilidade de volumes abaixo da média em parte do período. "
            f"Isso pode manter o risco de estresse hídrico e exigir acompanhamento constante das condições regionais."
        )
    else:
        texto = (
            f"Para {nome_local}, a tendência climática para os próximos 3 meses indica manutenção de temperaturas "
            f"elevadas, com regime de chuvas ainda presente, porém potencialmente irregular em parte da área. "
            f"Operacionalmente, recomenda-se observar a distribuição temporal das precipitações e a resposta "
            f"das condições de campo."
        )

    return {
        "texto": texto,
        "fonte": "Interpretação climática regional baseada em contexto geográfico da área selecionada",
        "data_referencia": f"Janela sazonal estimada: {_periodo_referencia_meses(3)}",
        "data_emissao": _data_execucao_formatada(),
    }


def _gerar_tendencia_6_meses(contexto: dict) -> dict:
    nome_local = contexto.get("nome_local", "a área selecionada")
    lat = contexto.get("lat")
    lon = contexto.get("lon")
    regiao = _classificar_regiao(lat, lon)

    if regiao == "Sul":
        texto = (
            f"Para {nome_local}, a leitura de tendência para os próximos 6 meses sugere continuidade de elevada "
            f"variabilidade climática, com alternância entre períodos mais úmidos e mais secos. "
            f"No horizonte estratégico, recomenda-se utilizar esta sinalização para planejar janelas operacionais "
            f"com maior flexibilidade."
        )
    elif regiao == "Sudeste":
        texto = (
            f"Para {nome_local}, a tendência de 6 meses indica consolidação de uma fase mais seca em parte do ciclo, "
            f"com retorno gradual das chuvas posteriormente. A manutenção de temperaturas elevadas pode intensificar "
            f"o déficit hídrico em determinados momentos, exigindo avaliação estratégica das operações."
        )
    elif regiao == "Centro-Oeste":
        texto = (
            f"Para {nome_local}, a tendência climática para 6 meses indica forte sazonalidade, com período seco "
            f"bem definido seguido por retomada das chuvas em momento posterior. "
            f"A leitura estratégica sugere atenção elevada ao risco de estresse hídrico e ao planejamento das janelas de campo."
        )
    elif regiao == "Nordeste":
        texto = (
            f"Para {nome_local}, a tendência climática de 6 meses aponta para manutenção de irregularidade na chuva, "
            f"com possibilidade de períodos secos mais prolongados em parte da área. "
            f"Essa condição reforça a necessidade de planejamento prudente em atividades dependentes da umidade."
        )
    else:
        texto = (
            f"Para {nome_local}, a tendência de 6 meses indica manutenção de temperaturas elevadas e comportamento "
            f"variável da precipitação, com possibilidade de redução em parte do horizonte analisado. "
            f"Como apoio estratégico, recomenda-se combinar esta leitura com a previsão de curto prazo e com o histórico climático local."
        )

    return {
        "texto": texto,
        "fonte": "Interpretação climática regional baseada em contexto geográfico da área selecionada",
        "data_referencia": f"Janela sazonal estimada: {_periodo_referencia_meses(6)}",
        "data_emissao": _data_execucao_formatada(),
    }