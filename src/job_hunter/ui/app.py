from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import streamlit as st
from job_hunter.application.search import SearchService
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


def profile_form(store):
    profile = store.load_profile()
    st.subheader("Seu perfil")
    st.caption("Informe apenas o que você possui. Áreas de interesse ficam nos critérios de busca. Dados salvos neste computador.")
    with st.form("profile"):
        name = st.text_input("Nome (opcional)", profile.name)
        education = st.text_area("Formação", profile.education)
        experience = st.text_area("Experiências e atividades realizadas", profile.experience)
        skills = st.text_area("Competências declaradas — uma por linha: competência: domínio", "\n".join(f"{k}: {v}" for k, v in profile.skills.items()),
                              placeholder="SQL: intermediário\nPower BI: avançado", help="Domínio: básico, intermediário ou avançado. Exemplos são fictícios e não preenchidos automaticamente.")
        languages = st.text_area("Idiomas e níveis declarados", profile.languages)
        years_known = st.checkbox("Quero declarar meus anos de experiência", profile.years is not None)
        years = st.number_input("Anos de experiência", min_value=0.0, max_value=80.0, value=float(profile.years or 0), step=0.5)
        seniorities = st.multiselect("Senioridades em que possuo experiência (declaradas)", SENIORITIES[:-1], default=profile.seniorities)
        extra = st.text_area("Informações complementares", profile.extra)
        save = st.form_submit_button("Salvar perfil", type="primary")
    if save:
        try:
            parsed = {}
            for line in lines(skills):
                skill, level = line.rsplit(":", 1)
                parsed[skill.strip()] = level.strip().lower()
            saved = Profile(name, education, experience, parsed, languages, years if years_known else None, seniorities, extra)
            store.save_profile(saved)
            st.success(f"Perfil salvo — versão {saved.version}.")
        except ValueError as exc:
            st.error(f"Não foi possível salvar. Confira competência: domínio. {exc}")


def search_form(store):
    st.subheader("Critérios de busca")
    names = store.search_names()
    selected = st.selectbox("Busca salva", ["Nova busca"] + names)
    c = store.load_search(selected) if selected != "Nova busca" else SearchConfig()
    with st.form("config:" + selected):
        name = st.text_input("Nome desta busca", c.name)
        terms = st.text_area("Cargos e termos — um por linha", "\n".join(c.terms), placeholder="Analista de Dados\nAnalista de BI\nPower BI")
        synonyms = st.text_area("Sinônimos opcionais — termo: alternativa, alternativa", "\n".join(f"{k}: {', '.join(v)}" for k, v in c.synonyms.items()),
                               help="Adicione alternativas também nos termos se quiser que sejam pesquisadas no portal.")
        seniorities = st.multiselect("Senioridades desejadas", SENIORITIES, c.seniorities)
        modes = st.multiselect("Modalidades", MODES, c.modes)
        cities = st.text_area("Cidades/UF — uma por linha", "\n".join(c.cities), help="Obrigatório para híbrido/presencial. Remoto é tratado separadamente.")
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
                                  seniorities=seniorities, modes=modes, cities=lines(cities), location_required=loc_required,
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


def execution_view(store, service):
    st.subheader("Executar e revisar")
    names = store.search_names()
    if names:
        preferred = st.session_state.get("chosen_search")
        selected = st.selectbox("Critérios para executar", names, index=names.index(preferred) if preferred in names else 0)
        if st.button("Iniciar busca", type="primary", disabled=service.active()):
            try:
                run_id = service.start(store.load_profile(), store.load_search(selected))
                st.session_state["current_run"] = run_id
                st.session_state["monitoring_run"] = run_id
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    else:
        st.info("Salve os critérios para iniciar uma busca real.")

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
    st.caption("Seu perfil, sua busca, evidências para revisar. Aplicação local · IA desativada")
    path = os.environ.get("JOB_HUNTER_DB") or str(Path(__file__).resolve().parents[3] / "data" / "jobs.sqlite")
    store, service = resources(path)
    page = st.sidebar.radio("Navegação", ["Perfil", "Critérios", "Executar e revisar"])
    st.sidebar.caption("Os dados ficam neste computador. Candidaturas são feitas por você no site da empresa.")
    if page == "Perfil":
        profile_form(store)
    elif page == "Critérios":
        search_form(store)
    else:
        execution_view(store, service)
