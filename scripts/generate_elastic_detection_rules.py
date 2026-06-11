#!/usr/bin/env python3
"""
Populate the `elastic_detection_rules` query field for every detection-style
step that already has an `elastic` (Elastic EQL/KQL) query.

For each such step, generates an Elastic Security detection-rule definition
in the TOML format used by the elastic/detection-rules repo, reusing the
existing query, the playbook's severity, and any MITRE ATT&CK technique IDs
referenced by the playbook.

Usage: python3 scripts/generate_elastic_detection_rules.py
"""
import json
import glob
import re

PLAYBOOKS_DIR = "app/playbooks"
STEP_KEYS = ["detSteps", "contSteps", "eradSteps", "recSteps", "steps"]

SEVERITY_MAP = {
    "low": ("low", 21),
    "medium": ("medium", 47),
    "high": ("high", 73),
    "critical": ("critical", 99),
}

TECHNIQUE_RE = re.compile(r"T\d{4}(?:\.\d{3})?")


def clean_query(raw):
    lines = [l for l in raw.splitlines() if not l.strip().startswith("#")]
    cleaned = "\n".join(lines).strip()
    return cleaned or raw.strip()


def rule_name(step_title):
    title = step_title.strip().rstrip(".")
    return title[0].upper() + title[1:] if title else "Detection Rule"


def build_rule_toml(step_title, query, sev_key, mitre_field):
    severity, risk_score = SEVERITY_MAP.get(sev_key, ("medium", 47))
    techniques = TECHNIQUE_RE.findall(mitre_field or "")[:5]

    lines = []
    lines.append("[rule]")
    lines.append(f'name = "{rule_name(step_title)}"')
    lines.append('type = "query"')
    lines.append('language = "kuery"')
    lines.append('index = ["logs-*", "winlogbeat-*", "filebeat-*"]')
    lines.append(f'risk_score = {risk_score}')
    lines.append(f'severity = "{severity}"')
    lines.append("")
    lines.append("query = '''")
    lines.append(query)
    lines.append("'''")

    if techniques:
        lines.append("")
        lines.append("[[rule.threat]]")
        lines.append('framework = "MITRE ATT&CK"')
        for tid in techniques:
            lines.append("[[rule.threat.technique]]")
            lines.append(f'id = "{tid}"')

    return "\n".join(lines)


def main():
    files = sorted(glob.glob(f"{PLAYBOOKS_DIR}/**/*.json", recursive=True))
    files = [f for f in files if "manifest.json" not in f and "mitre-techniques.json" not in f]

    updated_files = 0
    updated_steps = 0

    for f in files:
        with open(f) as fh:
            data = json.load(fh)

        mitre_field = data.get("mitre", "")
        sev_key = (data.get("sev") or "medium").lower()
        file_changed = False

        for step_key in STEP_KEYS:
            for step in data.get(step_key) or []:
                queries = step.get("queries")
                if not queries:
                    continue
                elastic_q = queries.get("elastic")
                if not elastic_q:
                    if "elastic" in queries and "elastic_detection_rules" not in queries:
                        queries["elastic_detection_rules"] = None
                        file_changed = True
                    continue

                cleaned = clean_query(elastic_q)
                queries["elastic_detection_rules"] = build_rule_toml(
                    step.get("title", data.get("name", "Detection")),
                    cleaned,
                    sev_key,
                    mitre_field,
                )
                file_changed = True
                updated_steps += 1

        if file_changed:
            with open(f, "w") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            updated_files += 1

    print(f"Updated {updated_steps} steps across {updated_files} files")


if __name__ == "__main__":
    main()
