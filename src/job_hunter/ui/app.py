from pathlib import Path
from datetime import datetime
from dataclasses import replace
from zoneinfo import ZoneInfo
import os
import streamlit as st
from job_hunter.application.search import SearchService
from job_hunter.application.suggestions import SuggestionService, providers, compact_profile
from job_hunter.domain.locations import states, state_label, cities as state_cities
from job_hunter.domain.models import Profile, SearchConfig, MODES, SENIORITIES, STATES, fold
from job_hunter.storage.sqlite import Store
from job_hunter.exports.csv import export_csv


def lines(value):
    return list(dict.fromkeys(line.strip() for line in value.splitlines() if line.strip()))


def date(value):
    return datetime.fromisoformat(value).astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M") if value else "—"


@st.cache_resource
def resources(path):
    store = Store(path)
    return store, SearchService(store)


@st.cache_resource
def suggestions():
    return SuggestionService()


def profile_form(store):
    profile = store.load_profile()
    st.subheader("Usuário")
    st.caption("Reúna seus dados pessoais e profissionais. Revise os dados do currículo antes de usá-los nas buscas. Tudo é salvo localmente.")
    cadastro, curriculo = st.tabs(["Cadastro", "Currículo"])
    with curriculo:
        if profile.resume_text:
            st.caption(f"Documento registrado: {profile.resume_filename}. O texto original é preservado para consulta; edite os dados na aba Cadastro.")
            resume_path = store.path.parent / "curriculo" / "original.pdf"
            if resume_path.is_file():
                st.download_button("Baixar currículo original", resume_path.read_bytes(), profile.resume_filename or "curriculo.pdf", "application/pdf")
            st.text(profile.resume_text)
        else:
            st.info("Nenhum currículo registrado neste cadastro.")
    with cadastro:
        st.markdown("### Dados pessoais e contato")
        name = st.text_input("Nome (opcional)", profile.name)
        left, right = st.columns(2)
        email = left.text_input("E-mail", profile.email)
        phone = right.text_input("Telefone", profile.phone)
        ufs = [""] + states()
        uf = left.selectbox("Estado", ufs, index=ufs.index(profile.uf) if profile.uf in ufs else 0,
                            format_func=state_label, key="profile_uf")
        options = [""] + state_cities(uf)
        if profile.city and uf == profile.uf and profile.city not in options:
            options.append(profile.city)
        city = right.selectbox("Cidade", options, index=options.index(profile.city) if uf == profile.uf and profile.city in options else 0,
                               disabled=not uf, key="profile_city_" + uf,
                               format_func=lambda value: value or "Selecione uma cidade")
        linkedin = st.text_input("LinkedIn", profile.linkedin, placeholder="https://www.linkedin.com/in/seu-perfil")
        portfolio = st.text_input("Portfólio ou site pessoal", profile.portfolio)
        st.markdown("### Perfil profissional")
        headline = st.text_input("Título profissional", profile.headline)
        summary = st.text_area("Resumo profissional", profile.summary)
        education = st.text_area("Formação", profile.education)
        certifications = st.text_area("Cursos e certificações", profile.certifications)
        experience = st.text_area("Experiências e atividades realizadas", profile.experience)
        skills = st.text_area("Competências declaradas — uma por linha: competência: domínio", "\n".join(f"{k}: {v}" for k, v in profile.skills.items()),
                              placeholder="SQL: não informado\nPower BI: avançado", help="Domínio: não informado, básico, intermediário ou avançado. O currículo não determina automaticamente seu nível.")
        languages = st.text_area("Idiomas e níveis declarados", profile.languages)
        years_known = st.checkbox("Quero declarar meus anos de experiência", profile.years is not None)
        years = st.number_input("Anos de experiência", min_value=0.0, max_value=80.0, value=float(profile.years or 0), step=0.5)
        seniorities = st.multiselect("Senioridades em que possuo experiência (declaradas)", SENIORITIES[:-1], default=profile.seniorities)
        extra = st.text_area("Informações complementares", profile.extra)
        save = st.button("Salvar dados do usuário", type="primary", icon=":material/save:")
    if save:
        try:
            parsed = {}
            for line in lines(skills):
                skill, level = line.rsplit(":", 1)
                parsed[skill.strip()] = level.strip().lower()
            saved = Profile(name=name, education=education, experience=experience, skills=parsed, languages=languages,
                            years=years if years_known else None, seniorities=seniorities, extra=extra,
                            email=email.strip(), phone=phone.strip(), city=city.strip(), uf=uf.strip().upper(),
                            linkedin=linkedin.strip(), portfolio=portfolio.strip(), headline=headline, summary=summary,
                            certifications=certifications, resume_text=profile.resume_text, resume_filename=profile.resume_filename)
            store.save_profile(saved)
            st.success(f"Dados do usuário salvos — versão {saved.version}.")
        except ValueError as exc:
            st.error(f"Não foi possível salvar. Confira os campos e o formato competência: domínio. {exc}")


def search_form(store):
    st.subheader("Critérios de busca")
    names = store.search_names()
    selected = st.selectbox("Busca salva", ["Nova busca"] + names)
    c = store.load_search(selected) if selected != "Nova busca" else SearchConfig()
    st.markdown("### Onde você quer trabalhar?")
    ufs = st.multiselect("Estados da busca", states(), default=[uf for uf in states() if any(city.endswith("/" + uf) for city in c.cities)],
                         format_func=state_label, key="search_states_" + selected, placeholder="Selecione um ou mais estados")
    city_options = [f"{city}/{uf}" for uf in ufs for city in state_cities(uf)]
    city_options += [city for city in c.cities if city.rsplit("/", 1)[-1] in ufs and city not in city_options]
    cities = st.multiselect("Cidades da busca", city_options, default=[city for city in c.cities if city in city_options],
                            key="search_cities_" + selected, disabled=not ufs,
                            placeholder="Selecione as cidades" if ufs else "Escolha um estado primeiro",
                            help="Escolha estados e depois uma ou mais cidades. Obrigatório para híbrido/presencial.")
    st.caption("Catálogo do IBGE disponível offline. Para trabalhar de qualquer lugar, escolha a modalidade remoto.")
    with st.form("config:" + selected):
        name = st.text_input("Nome desta busca", c.name)
        terms = st.text_area("Cargos e termos — um por linha", "\n".join(c.terms), placeholder="Analista de Dados\nAnalista de BI\nPower BI")
        synonyms = st.text_area("Sinônimos opcionais — termo: alternativa, alternativa", "\n".join(f"{k}: {', '.join(v)}" for k, v in c.synonyms.items()),
                               help="Adicione alternativas também nos termos se quiser que sejam pesquisadas no portal.")
        seniorities = st.multiselect("Senioridades desejadas", SENIORITIES, c.seniorities)
        modes = st.multiselect("Modalidades", MODES, c.modes)
        loc_required = st.checkbox("Localização e modalidade são filtros obrigatórios", c.location_required)
        has_salary = st.checkbox("Configurar salário mínimo mensal em reais", c.min_salary is not None)
        salary = st.number_input("Salário mínimo BRL/mês", min_value=0.0, value=float(c.min_salary or 0), step=100.0)
        salary_required = st.checkbox("Salário publicado é filtro obrigatório", c.salary_required)
        missing = st.selectbox("Quando o salário não for publicado", ["pendência", "excluir"], index=["pendência", "excluir"].index(c.missing_salary))
        exclude = st.text_area("Termos para descarte obrigatório — um por linha", "\n".join(c.exclude_terms))
        avoid = st.text_area("Termos para menor prioridade — um por linha", "\n".join(c.deprioritize_terms))
        affirmative = st.selectbox("Vagas afirmativas", ["sinalizar", "excluir"], index=["sinalizar", "excluir"].index(c.affirmative),
                                   help="Sinalizar condições e confirmar elegibilidade. 'Também para PcD' não significa vaga exclusiva.")
        col1, col2, col3 = st.columns(3)
        pages = col1.number_input("Máximo de páginas por termo", 1, 10, c.max_pages)
        jobs = col2.number_input("Máximo de vagas únicas", 1, 100, c.max_jobs)
        seconds = col3.number_input("Tempo máximo (segundos)", 30, 900, c.max_seconds)
        st.caption("Pesos experimentais, ainda sem calibração humana. Soma deve ser 100. A nota ordena revisão e não prevê contratação.")
        w1, w2, w3 = st.columns(3)
        weights = [w1.number_input("Função/atividades", 0, 100, c.weights[0]), w2.number_input("Competências", 0, 100, c.weights[1]), w3.number_input("Senioridade/experiência", 0, 100, c.weights[2])]
        save = st.form_submit_button("Salvar critérios", type="primary")
    if save:
        try:
            aliases = {}
            for line in lines(synonyms):
                key, values = line.split(":", 1)
                aliases[key.strip()] = [v.strip() for v in values.split(",") if v.strip()]
            config = SearchConfig(name=name.strip() or "Minha busca", terms=lines(terms), synonyms=aliases,
                                  seniorities=seniorities, modes=modes, cities=cities, location_required=loc_required,
                                  min_salary=salary if has_salary else None, salary_required=salary_required,
                                  missing_salary=missing, exclude_terms=lines(exclude), deprioritize_terms=lines(avoid),
                                  affirmative=affirmative, max_pages=pages, max_jobs=jobs, max_seconds=seconds, weights=weights)
            store.save_search(config)
            st.session_state["chosen_search"] = config.name
            st.success("Critérios salvos. Abra Executar e revisar para iniciar.")
        except ValueError as exc:
            st.error(str(exc))


def results_view(store, run_id):
    rows = store.results(run_id)
    if not rows:
        st.info("Nenhum anúncio salvo nesta execução. Confira o status e as falhas acima.")
        return
    st.subheader("Resultados")
    a, b, c = st.columns(3)
    state_filter = a.multiselect("Filtrar por estado", STATES)
    mode_filter = b.multiselect("Filtrar modalidade", MODES)
    order = c.selectbox("Ordenar", ["Aderência", "Mais recentes", "Título"])
    query = st.text_input("Filtrar título ou empresa")
    show_excluded = st.checkbox("Mostrar vagas excluídas pelos critérios", value=False)
    filtered = [r for r in rows if (not state_filter or r["state"] in state_filter) and
                (not mode_filter or r["job"]["mode"] in mode_filter) and
                (not query or fold(query) in fold(r["job"]["title"] + " " + (r["job"]["company"] or ""))) and
                (show_excluded or r["evaluation"]["eligibility"] != "excluída")]
    if order == "Aderência":
        filtered.sort(key=lambda r: (len(r["evaluation"].get("preferences", [])), -(r["evaluation"].get("score") if r["evaluation"].get("score") is not None else -1)))
    elif order == "Mais recentes":
        filtered.sort(key=lambda r: r["job"].get("published_at") or "", reverse=True)
    else:
        filtered.sort(key=lambda r: fold(r["job"]["title"]))
    st.caption(f"{len(filtered)} de {len(rows)} anúncios. Prioridades são aplicadas antes da nota; score e cobertura são experimentais.")
    table = [{"Título": r["job"]["title"], "Empresa": r["job"]["company"], "Modalidade": r["job"]["mode"], "Local": r["job"]["location"],
              "Nota": r["evaluation"].get("score"), "Cobertura %": r["evaluation"].get("coverage"), "Estado": r["state"], "Link": r["job"]["url"]} for r in filtered]
    st.dataframe(table, width="stretch", hide_index=True, column_config={"Link": st.column_config.LinkColumn("Anúncio")})
    st.download_button("Exportar resultados filtrados (CSV)", export_csv(filtered), "vagas.csv", "text/csv")
    if not filtered:
        return
    by_key = {r["key"]: r for r in filtered}
    key = st.selectbox("Revisar anúncio", list(by_key), format_func=lambda k: by_key[k]["job"]["title"] + " — " + (by_key[k]["job"]["company"] or "empresa ausente"))
    row = by_key[key]
    job, ev = row["job"], row["evaluation"]
    st.link_button("Abrir anúncio na Gupy", job["url"])
    st.write(f"Salário mensal BRL: {job['salary'] if job['salary'] is not None else 'não publicado'} · Publicação: {job.get('published_at') or 'ausente'}")
    st.caption(f"Coleta inicial: {date(row['first_seen'])} · Último reencontro: {date(row['last_seen'])} · Avaliador: {ev['version']}")
    st.write("Elegibilidade:", ev["eligibility"])
    for reason in ev["reasons"] + ev["preferences"]:
        st.write("• " + reason)
    st.write("Pendências de confirmação")
    for item in ev["pending"]:
        st.write("• " + item)
    with st.expander("Evidências da avaliação"):
        for item in ev["evidence"]:
            st.write(f"{item['component']} — {item['points']:g} pontos")
            st.text("Anúncio: " + item["job"] + "\nPerfil/objetivo: " + item["profile"])
    with st.expander("Descrição e requisitos coletados"):
        st.text(job["description"] or "Descrição ausente; confira o link.")
        st.caption("Origem da extração: " + job["extraction"])
    with st.form("state:" + key):
        state = st.selectbox("Estado pessoal", STATES, index=STATES.index(row["state"]))
        notes = st.text_area("Observações privadas", row["notes"])
        if st.form_submit_button("Salvar acompanhamento"):
            store.set_state(key, state, notes)
            st.success("Acompanhamento salvo.")


def assistant_view(store, service, config):
    profile = store.load_profile()
    if st.session_state.get("suggestion_profile_version") != profile.version:
        st.session_state.pop("suggestion", None)
    with st.container(border=True):
        st.markdown("### Encontre cargos com seu perfil")
        st.caption("A IA sugere até quatro termos a partir de um resumo do cadastro e currículo salvos. Seus filtros e limites são mantidos.")
        with st.expander("Configurar Groq e conferir o resumo enviado"):
            st.text_input("Chave da API Groq", type="password", key="groq_key",
                          help="Opcional se GROQ_API_KEY estiver no ambiente. A chave digitada fica apenas nesta sessão.")
            if os.environ.get("GROQ_API_KEY"):
                st.caption("Chave Groq configurada no ambiente.")
            st.caption("Ao sugerir, o resumo abaixo será enviado ao provedor configurado. Contatos são removidos; o currículo completo não é enviado.")
            st.json(compact_profile(profile))
            st.link_button("Obter chave no Groq", "https://console.groq.com/keys")
        chain = providers(st.session_state.get("groq_key", ""))
        if not chain:
            st.info("Configure a chave Groq acima para usar IA. Sem chave, você pode usar sugestões locais do seu título e competências.")
        a, b = st.columns(2)
        suggest = a.button("Sugerir termos", disabled=service.active(), icon=":material/auto_awesome:")
        search = b.button("Sugerir e pesquisar", type="primary", disabled=service.active(), icon=":material/search:")
        if suggest or search:
            try:
                replace(config, terms=["validar filtros"]).validate()
                with st.spinner("Preparando sugestões do seu perfil…"):
                    result = suggestions().suggest(profile, chain)
                st.session_state["suggestion"] = result
                st.session_state["suggestion_profile_version"] = profile.version
                st.session_state["suggested_terms"] = "\n".join(result["terms"])
                if search:
                    suggested = replace(config, name=config.name if config.name.endswith(" · sugerida") else config.name + " · sugerida", terms=result["terms"])
                    run_id = service.start(store.load_profile(), suggested)
                    store.save_search(suggested)
                    st.session_state.update(current_run=run_id, monitoring_run=run_id, chosen_search=suggested.name)
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        result = st.session_state.get("suggestion")
        if result:
            st.caption("Origem: " + result["source"] + (" · reutilizada, sem nova chamada" if result["cached"] else ""))
            if result["usage"].get("total_tokens"):
                st.caption(f"Tokens da resposta original: {result['usage']['total_tokens']}.")
            if result["failures"]:
                st.warning("O provedor principal falhou; a sugestão veio do fallback. " + " ".join(result["failures"]))
            st.text_area("Termos sugeridos — você pode editar", key="suggested_terms", height=120)
            if st.button("Salvar termos sugeridos", disabled=service.active()):
                try:
                    updated = replace(config, terms=lines(st.session_state["suggested_terms"]))
                    store.save_search(updated)
                    st.session_state["chosen_search"] = updated.name
                    st.success("Termos salvos. Inicie a busca abaixo quando quiser.")
                except ValueError as exc:
                    st.error(str(exc))


def execution_view(store, service):
    st.subheader("Executar e revisar")
    names = store.search_names()
    if names:
        preferred = st.session_state.get("chosen_search")
        selected = st.selectbox("Critérios para executar", names, index=names.index(preferred) if preferred in names else 0)
        assistant_view(store, service, store.load_search(selected))
        if st.button("Iniciar busca", type="primary", disabled=service.active()):
            try:
                run_id = service.start(store.load_profile(), store.load_search(selected))
                st.session_state["current_run"] = run_id
                st.session_state["monitoring_run"] = run_id
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    else:
        st.info("Salve os critérios para definir localização, salário e limites antes de pesquisar.")

    @st.fragment(run_every=1 if service.active() else None)
    def monitor():
        if st.session_state.get("monitoring_run") and not service.active():
            del st.session_state["monitoring_run"]
            st.rerun(scope="app")
        runs = store.runs()
        if not runs:
            return
        by_id = {r["id"]: r for r in runs}
        current = st.session_state.get("current_run")
        ids = list(by_id)
        selected = st.selectbox("Histórico de execuções", ids, index=ids.index(current) if current in ids else 0,
                                format_func=lambda k: f"{date(by_id[k]['started_at'])} — {by_id[k]['config']['name']} — {by_id[k]['status']}")
        run = by_id[selected]
        labels = {"running": "Em execução", "completed": "Concluída", "partial": "Parcial, com falhas", "failed": "Falhou", "cancelled": "Cancelada", "limited": "Limite atingido", "interrupted": "Interrompida pelo reinício"}
        st.write(labels[run["status"]] + " · " + run["stage"])
        cols = st.columns(5)
        for column, label, field in zip(cols, ["Termos", "Páginas", "Vagas únicas", "Duplicatas", "Falhas"], ["terms_done", "pages", "jobs", "duplicates", "failures"]):
            column.metric(label, run[field])
        if service.active() and selected == service.active_id:
            if st.button("Cancelar após a operação atual"):
                service.cancel()
                st.info("Cancelamento solicitado; resultados já coletados serão preservados.")
        elif run["status"] != "running" and service.worker and selected == service.active_id:
            st.caption("Busca encerrada. Uma nova busca usa os critérios salvos atualmente.")
        if run["errors"]:
            with st.expander("Falhas registradas", expanded=run["status"] == "failed"):
                for error in run["errors"]:
                    st.error(error["kind"] + ": " + error["message"])
        with st.expander("Perfil e critérios usados nesta execução"):
            st.json({"perfil": run["profile"], "critérios": run["config"]})
        results_view(store, selected)
    monitor()


def main():
    st.set_page_config(page_title="Busca Vagas", page_icon="🔎", layout="wide")
    st.title("Busca Vagas")
    st.caption("Organize seu perfil. Encontre oportunidades. Revise com evidências.")
    st.html("""<style>
        .stMainBlockContainer {max-width: 1120px; padding-top: 2.5rem; padding-bottom: 4rem;}
        h1 {font-size: 2rem !important; letter-spacing: -.025em;}
        h3 {font-size: 1.25rem !important;}
        button[data-variant="segmented_control"] {min-height: 44px;}
        [role="radiogroup"][aria-label="Navegação"] {flex-wrap: wrap;}
        [data-testid="stCaptionContainer"] {color: #516174; max-width: 75ch;}
        input::placeholder, textarea::placeholder {color: #516174; opacity: 1;}
        :root {accent-color: #145fa8;}
        ::selection {background: #cce4fb; color: #17212f;}
        @media (max-width: 640px) {.stMainBlockContainer {padding: 1.5rem 1rem 3rem;} }
    </style>""")
    path = os.environ.get("JOB_HUNTER_DB") or str(Path(__file__).resolve().parents[3] / "data" / "jobs.sqlite")
    store, service = resources(path)
    page = st.segmented_control("Navegação", ["Usuário", "Critérios", "Executar e revisar"], default="Usuário",
                                key="navigation", selection_mode="single", required=True, width="stretch", label_visibility="collapsed")
    st.divider()
    if page == "Usuário":
        profile_form(store)
    elif page == "Critérios":
        search_form(store)
    else:
        execution_view(store, service)
    st.divider()
    st.caption("Cadastro e resultados salvos neste computador · IA opcional apenas para sugerir termos · Candidaturas no site da empresa")
