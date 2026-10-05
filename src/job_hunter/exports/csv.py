import csv
import io


def safe_cell(value):
    value = str(value if value is not None else "")
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")) or value.startswith(("\t", "\r", "\n")) else value


def export_csv(rows):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=";", quoting=csv.QUOTE_ALL)
    writer.writerow(["Título", "Empresa", "Modalidade", "Local", "URL", "Publicação", "Primeira coleta", "Última coleta", "Salário BRL/mês", "Aderência experimental", "Cobertura", "Elegibilidade", "Estado", "Notas", "Termos", "Pendências", "Evidências"])
    for row in rows:
        job, ev = row["job"], row["evaluation"]
        values = [job.get(k) for k in ["title", "company", "mode", "location", "url", "published_at"]]
        values += [row["first_seen"], row["last_seen"], job.get("salary"), ev.get("score"), ev.get("coverage"), ev.get("eligibility"),
                   row["state"], row["notes"], " | ".join(row["terms"]), " | ".join(ev.get("pending", [])),
                   " | ".join(f"{e['component']}: anúncio={e['job']}; perfil={e['profile']}" for e in ev.get("evidence", []))]
        writer.writerow([safe_cell(v) for v in values])
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")
