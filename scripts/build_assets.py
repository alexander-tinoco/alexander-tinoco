#!/usr/bin/env python3
"""Generate the bilingual SVG graphics used by the profile READMEs.

Usage:
    python scripts/build_assets.py            # build from data/languages.json
    python scripts/build_assets.py --refresh  # re-read language bytes from GitHub first

English files are assets/<name>.svg, Spanish files are assets/<name>.es.svg.
Brand icons come from simple-icons (CC0), vendored in scripts/icons/.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ICONS = Path(__file__).resolve().parent / "icons"
OWNER = "alexander-tinoco"

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif"
BG, CARD, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, MUTED = "#e6edf3", "#8b949e"
BLUE, VIOLET, GREEN, ORANGE, GOLD = "#58a6ff", "#a371f7", "#3fb950", "#f78166", "#d29922"

BRAND = {
    "javascript": "#F7DF1E", "typescript": "#3178C6", "python": "#3776AB", "cplusplus": "#00599C",
    "openjdk": "#ED8B00", "nodedotjs": "#5FA04E", "express": "#e6edf3", "nestjs": "#E0234E",
    "django": "#44B78B", "spring": "#6DB33F", "fastapi": "#009688", "react": "#61DAFB",
    "angular": "#DD0031", "astro": "#BC52EE", "flutter": "#54C5F8", "postgresql": "#4169E1",
    "mysql": "#4479A1", "mongodb": "#47A248", "redis": "#FF4438", "docker": "#2496ED",
    "git": "#F05032", "githubactions": "#2088FF", "linux": "#FCC624", "apachekafka": "#e6edf3",
    "prometheus": "#E6522C", "grafana": "#F46800", "tailwindcss": "#06B6D4", "cloudflare": "#F38020",
    "sentry": "#8B6FD6", "jenkins": "#D24939", "raspberrypi": "#C51A4A", "espressif": "#E7352C",
    "mqtt": "#B07CF0", "celery": "#5DB36A", "fastify": "#e6edf3", "opentelemetry": "#7B8FE8",
    "nextdotjs": "#e6edf3",
}

# --------------------------------------------------------------------------- strings
STR = {
    "en": {
        "kicker": "HELLO, I AM",
        "subtitle": "Full Stack Developer · Data and Backend Engineering",
        "taglines": [
            "I turn messy data into reliable systems.",
            "Backend APIs with tests, audit trails and observability.",
            "Web, mobile and IoT: from the sensor to the dashboard.",
        ],
        "kpis": [
            ("1,300+", "automated tests across five flagship projects"),
            ("99%", "coverage on The Club engine (220 tests)"),
            ("4", "hackathons: Capital One semifinalist, HACKDGO finalist"),
            ("2", "app stores: React Native app live on Google Play and App Store"),
        ],
        "kpis_title": "Key numbers",
        "kpis_desc": "Tests, coverage, hackathons and shipped apps",
        "tests_title": "Tested like production",
        "tests_sub": "Automated tests per project, with measured coverage where reported",
        "coverage": "coverage",
        "tests_rows": ["Job · résumé screening", "Survey Analytics", "Tramex · case management", "The Club · roulette engine", "Payroll · audit system"],
        "tests_notes": ["FastAPI · React", "Django · Celery", "FastAPI · Angular", "FastAPI · Kafka", "Express · React (backend tests)"],
        "tests_desc": "Bar chart of automated tests per flagship project",
        "stack_title": "Tech stack",
        "stack_sub": "What I use day to day, grouped by role",
        "stack_cats": ["Languages", "Backend", "Frontend and mobile", "Data and messaging", "DevOps and cloud", "Observability", "IoT and edge"],
        "stack_desc": "Languages, frameworks, databases, DevOps, observability and IoT tools",
        "lang_title": "Code on GitHub",
        "lang_sub": "Share of code by bytes across my public repositories",
        "lang_unit": "bytes of code",
        "other": "Other",
        "lang_desc": "Donut chart of language share across public repositories",
        "tl_title": "Journey",
        "tl_sub": "Education and work by year; projects by repository activity",
        "tl_edu": "Education", "tl_exp": "Experience", "tl_proj": "Projects", "tl_hack": "Hackathons", "today": "today",
        "edu_bars": ["Technical degree in IT · UTD", "Software Engineering · UTD", "Oracle Next Education"],
        "tl_desc": "Timeline of education, work, projects and hackathons from 2023",
        "footer": "Thanks for stopping by. Let's build something solid.",
        "footer_desc": "Animated wave footer",
        "hero_desc": "Full Stack Developer, data and backend engineering",
    },
    "es": {
        "kicker": "HOLA, SOY",
        "subtitle": "Desarrollador Full Stack · Datos e ingeniería backend",
        "taglines": [
            "Convierto datos desordenados en sistemas confiables.",
            "APIs con pruebas, bitácora de auditoría y observabilidad.",
            "Web, móvil e IoT: del sensor al dashboard.",
        ],
        "kpis": [
            ("1,300+", "pruebas automatizadas en cinco proyectos principales"),
            ("99%", "cobertura en el motor de The Club (220 pruebas)"),
            ("4", "hackathones: semifinalista Capital One, finalista HACKDGO"),
            ("2", "tiendas de apps: app React Native en Google Play y App Store"),
        ],
        "kpis_title": "Cifras clave",
        "kpis_desc": "Pruebas, cobertura, hackathones y apps publicadas",
        "tests_title": "Probado como producción",
        "tests_sub": "Pruebas automatizadas por proyecto, con cobertura medida donde se reporta",
        "coverage": "cobertura",
        "tests_rows": ["Job · selección de CVs", "Survey Analytics", "Tramex · gestión de casos", "The Club · motor de ruleta", "Payroll · auditoría de nómina"],
        "tests_notes": ["FastAPI · React", "Django · Celery", "FastAPI · Angular", "FastAPI · Kafka", "Express · React (pruebas de backend)"],
        "tests_desc": "Gráfica de barras de pruebas automatizadas por proyecto principal",
        "stack_title": "Stack tecnológico",
        "stack_sub": "Lo que uso día a día, agrupado por rol",
        "stack_cats": ["Lenguajes", "Backend", "Frontend y móvil", "Datos y mensajería", "DevOps y nube", "Observabilidad", "IoT y edge"],
        "stack_desc": "Lenguajes, frameworks, bases de datos, DevOps, observabilidad e IoT",
        "lang_title": "Código en GitHub",
        "lang_sub": "Proporción de código por bytes en mis repositorios públicos",
        "lang_unit": "bytes de código",
        "other": "Otros",
        "lang_desc": "Gráfica de dona con la proporción de lenguajes en repositorios públicos",
        "tl_title": "Trayectoria",
        "tl_sub": "Estudios y trabajo por año; proyectos según la actividad del repositorio",
        "tl_edu": "Educación", "tl_exp": "Experiencia", "tl_proj": "Proyectos", "tl_hack": "Hackathones", "today": "hoy",
        "edu_bars": ["TSU en Tecnologías de la Información · UTD", "Ing. en Desarrollo de Software · UTD", "Oracle Next Education"],
        "tl_desc": "Línea de tiempo de estudios, trabajo, proyectos y hackathones desde 2023",
        "footer": "Gracias por pasar. Construyamos algo sólido.",
        "footer_desc": "Pie con ola animada",
        "hero_desc": "Desarrollador Full Stack, datos e ingeniería backend",
    },
}

LANG = "en"


def S(key: str):
    return STR[LANG][key]


# --------------------------------------------------------------------------- helpers
def write(name: str, svg: str) -> None:
    ASSETS.mkdir(exist_ok=True)
    out = name if LANG == "en" else name.replace(".svg", ".es.svg")
    (ASSETS / out).write_text(svg, encoding="utf-8")
    print(f"wrote assets/{out} ({len(svg) // 1024 or 1} KB)")


def icon_paths(slug: str) -> list[str] | None:
    f = ICONS / f"{slug}.svg"
    if not f.exists():
        return None
    return re.findall(r'<path d="([^"]+)"', f.read_text(encoding="utf-8"))


def icon(slug: str, x: float, y: float, size: float = 20) -> str:
    paths = icon_paths(slug)
    color = BRAND.get(slug, TEXT)
    if not paths:
        return ""
    scale = size / 24
    body = "".join(f'<path d="{d}"/>' for d in paths)
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({scale:.3f})" fill="{color}">{body}</g>'


def frame(w: int, h: int, title: str, desc: str, body: str, defs: str = "") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t d" font-family="{FONT}">'
        f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>'
        f"<defs>{defs}</defs>{body}</svg>"
    )


def card(w: int, h: int, r: int = 16) -> str:
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{r}" fill="{BG}" stroke="{BORDER}"/>'


def fade(delay: float, dur: float = 0.6) -> str:
    return f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="{dur}s" fill="freeze"/>'


# --------------------------------------------------------------------------- header
def build_header() -> None:
    w, h = 1000, 300
    taglines = S("taglines")
    nodes = [(700, 70), (790, 120), (880, 60), (930, 150), (840, 210), (740, 230), (650, 170), (800, 40), (900, 240)]
    edges = [(0, 1), (1, 2), (1, 3), (1, 4), (4, 5), (5, 6), (6, 0), (0, 7), (7, 2), (3, 4), (4, 8), (6, 1)]
    lines = "".join(
        f'<line x1="{nodes[a][0]}" y1="{nodes[a][1]}" x2="{nodes[b][0]}" y2="{nodes[b][1]}" '
        f'stroke="url(#acc)" stroke-width="1.4" stroke-dasharray="4 6" opacity=".55">'
        f'<animate attributeName="stroke-dashoffset" from="0" to="-40" dur="{3 + i % 3}s" repeatCount="indefinite"/></line>'
        for i, (a, b) in enumerate(edges)
    )
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="5" fill="url(#acc)">'
        f'<animate attributeName="r" values="4;7;4" dur="{2.4 + (i % 4) * 0.5}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values=".6;1;.6" dur="{2.4 + (i % 4) * 0.5}s" repeatCount="indefinite"/></circle>'
        for i, (x, y) in enumerate(nodes)
    )
    rotating = "".join(
        f'<text x="60" y="226" font-size="21" fill="{BLUE}" opacity="0">{escape(t)}'
        f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.05;0.30;0.34;1" '
        f'dur="12s" begin="{i * 4}s" repeatCount="indefinite"/></text>'
        for i, t in enumerate(taglines)
    )
    pills = ["Python", "TypeScript", "FastAPI", "Next.js", "Astro", "PostgreSQL", "Docker"]
    px, pill_svg = 60, ""
    for i, p in enumerate(pills):
        pw = 16 + len(p) * 8
        pill_svg += (
            f'<g opacity="0">{fade(0.4 + i * 0.12)}<rect x="{px}" y="246" width="{pw}" height="30" rx="15" '
            f'fill="#ffffff" fill-opacity=".06" stroke="#ffffff" stroke-opacity=".18"/>'
            f'<text x="{px + pw / 2}" y="266" font-size="13" fill="{TEXT}" text-anchor="middle">{p}</text></g>'
        )
        px += pw + 10
    defs = (
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1220"/>'
        '<stop offset=".55" stop-color="#17123a"/><stop offset="1" stop-color="#0a2a3a"/></linearGradient>'
        f'<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BLUE}"/>'
        f'<stop offset="1" stop-color="{VIOLET}"/></linearGradient>'
        '<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">'
        '<path d="M32 0H0V32" fill="none" stroke="#ffffff" stroke-opacity=".05"/></pattern>'
        '<radialGradient id="glow" cx=".8" cy=".35" r=".6"><stop offset="0" stop-color="#7c5cff" stop-opacity=".35"/>'
        '<stop offset="1" stop-color="#7c5cff" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="clip"><rect width="{w}" height="{h}" rx="20"/></clipPath>'
    )
    body = (
        f'<g clip-path="url(#clip)"><rect width="{w}" height="{h}" fill="url(#bg)"/>'
        f'<rect width="{w}" height="{h}" fill="url(#grid)"/><rect width="{w}" height="{h}" fill="url(#glow)"/>'
        f"{lines}{dots}</g>"
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="20" fill="none" stroke="#ffffff" stroke-opacity=".12"/>'
        f'<text x="60" y="92" font-size="18" fill="{MUTED}" letter-spacing="3">{escape(S("kicker"))}</text>'
        f'<text x="58" y="150" font-size="60" font-weight="700" fill="url(#acc)">Alexander Tinoco</text>'
        f'<text x="60" y="186" font-size="17" fill="{TEXT}" opacity=".9">{escape(S("subtitle"))}</text>'
        f"{rotating}{pill_svg}"
    )
    write("header.svg", frame(w, h, "Alexander Tinoco", S("hero_desc"), body, defs))


# --------------------------------------------------------------------------- KPI strip
def build_kpis() -> None:
    w, h = 1000, 140
    cols = [BLUE, VIOLET, GREEN, ORANGE]
    gap, cw = 16, (w - 16 * 3) / 4
    body = ""
    for i, (big, small) in enumerate(S("kpis")):
        col, x = cols[i], i * (cw + gap)
        words, lines, cur = small.split(), [], ""
        for wd in words:
            if len(cur) + len(wd) + 1 > 30:
                lines.append(cur)
                cur = wd
            else:
                cur = f"{cur} {wd}".strip()
        lines.append(cur)
        sub = "".join(
            f'<text x="{x + 20}" y="{92 + j * 18}" font-size="13" fill="{MUTED}">{escape(l)}</text>' for j, l in enumerate(lines)
        )
        body += (
            f'<g opacity="0">{fade(i * 0.15)}'
            f'<rect x="{x:.1f}" y=".5" width="{cw:.1f}" height="{h - 1}" rx="14" fill="{CARD}" stroke="{BORDER}"/>'
            f'<rect x="{x:.1f}" y=".5" width="{cw:.1f}" height="4" rx="2" fill="{col}"/>'
            f'<text x="{x + 20}" y="68" font-size="40" font-weight="700" fill="{col}">{big}</text>{sub}</g>'
        )
    write("kpis.svg", frame(w, h, S("kpis_title"), S("kpis_desc"), body))


# --------------------------------------------------------------------------- tests chart
def build_tests() -> None:
    data = [(415, None), (383, "98.6%"), (245, "90.4%"), (220, "99%"), (97, None)]
    names, notes = S("tests_rows"), S("tests_notes")
    w, h = 1000, 120 + len(data) * 52
    x0, maxw, mx = 270, 470, 415
    body = (
        f"{card(w, h)}"
        f'<text x="32" y="46" font-size="20" font-weight="700" fill="{TEXT}">{escape(S("tests_title"))}</text>'
        f'<text x="32" y="68" font-size="13" fill="{MUTED}">{escape(S("tests_sub"))}</text>'
    )
    for i, (n, cov) in enumerate(data):
        y = 100 + i * 52
        bw = maxw * n / mx
        col = [BLUE, VIOLET, GREEN, ORANGE, GOLD][i]
        body += (
            f'<text x="32" y="{y + 15}" font-size="14" font-weight="600" fill="{TEXT}">{escape(names[i])}</text>'
            f'<text x="32" y="{y + 32}" font-size="11.5" fill="{MUTED}">{escape(notes[i])}</text>'
            f'<rect x="{x0}" y="{y + 4}" width="{maxw}" height="22" rx="11" fill="{CARD}"/>'
            f'<rect x="{x0}" y="{y + 4}" width="0" height="22" rx="11" fill="{col}">'
            f'<animate attributeName="width" from="0" to="{bw:.1f}" begin="{i * 0.18:.2f}s" dur="1s" fill="freeze" '
            f'calcMode="spline" keySplines=".2 .8 .2 1" keyTimes="0;1"/></rect>'
            f'<text x="{x0 + bw + 12:.1f}" y="{y + 20}" font-size="14" font-weight="700" fill="{TEXT}">{n}</text>'
        )
        if cov:
            body += (
                f'<g><rect x="{w - 160}" y="{y + 2}" width="128" height="26" rx="13" fill="{GREEN}" fill-opacity=".14" stroke="{GREEN}" stroke-opacity=".5"/>'
                f'<text x="{w - 96}" y="{y + 20}" font-size="13" font-weight="600" fill="{GREEN}" text-anchor="middle">{cov} {escape(S("coverage"))}</text></g>'
            )
    write("tests.svg", frame(w, h, S("tests_title"), S("tests_desc"), body))


# --------------------------------------------------------------------------- stack
def build_stack() -> None:
    techs = [
        [("javascript", "JavaScript"), ("typescript", "TypeScript"), ("python", "Python"), ("openjdk", "Java"), ("cplusplus", "C++")],
        [("nodedotjs", "Node.js"), ("express", "Express"), ("nestjs", "NestJS"), ("fastify", "Fastify"), ("django", "Django"), ("spring", "Spring Boot"), ("fastapi", "FastAPI")],
        [("react", "React"), ("react", "React Native"), ("nextdotjs", "Next.js"), ("angular", "Angular"), ("astro", "Astro"), ("flutter", "Flutter"), ("tailwindcss", "Tailwind")],
        [("postgresql", "PostgreSQL"), ("mysql", "MySQL"), ("mongodb", "MongoDB"), ("redis", "Redis"), ("apachekafka", "Kafka"), ("celery", "Celery")],
        [("docker", "Docker"), ("git", "Git"), ("githubactions", "GitHub Actions"), ("linux", "Linux"), ("jenkins", "Jenkins"), ("cloudflare", "Cloudflare"), ("aws", "AWS")],
        [("prometheus", "Prometheus"), ("grafana", "Grafana"), ("sentry", "Sentry"), ("opentelemetry", "OpenTelemetry")],
        [("espressif", "ESP32"), ("raspberrypi", "Raspberry Pi"), ("mqtt", "MQTT")],
    ]
    cats = list(zip(S("stack_cats"), techs))
    w, label_w, th, gap = 1000, 190, 40, 8
    avail = w - label_w - 28
    body, y, delay = "", 78, 0.0
    for cname, tl in cats:
        placed, x, row = [], 0.0, 0
        for slug, label in tl:
            tw = 46 + len(label) * 7.4
            if x + tw > avail:
                x, row = 0.0, row + 1
            placed.append((slug, label, x, row, tw))
            x += tw + gap
        block_h = (row + 1) * (th + gap) - gap
        body += (
            f'<text x="32" y="{y + th / 2 + 5}" font-size="14" font-weight="700" fill="{TEXT}">{escape(cname)}</text>'
            f'<rect x="{label_w - 14}" y="{y}" width="2" height="{block_h}" rx="1" fill="{BORDER}"/>'
        )
        for slug, label, tx, r, tw in placed:
            ax, ay = label_w + tx, y + r * (th + gap)
            glyph = icon(slug, ax + 12, ay + 10, 20) or (
                f'<text x="{ax + 22}" y="{ay + 26}" font-size="12" font-weight="800" fill="#FF9900" text-anchor="middle">aws</text>'
            )
            body += (
                f'<g opacity="0">{fade(delay)}'
                f'<rect x="{ax:.1f}" y="{ay}" width="{tw:.1f}" height="{th}" rx="10" fill="{CARD}" stroke="{BORDER}"/>'
                f'{glyph}<text x="{ax + 40:.1f}" y="{ay + 25}" font-size="13" fill="{TEXT}">{escape(label)}</text></g>'
            )
            delay += 0.04
        y += block_h + 22
    h = y + 10
    head = (
        f"{card(w, h)}"
        f'<text x="32" y="40" font-size="20" font-weight="700" fill="{TEXT}">{escape(S("stack_title"))}</text>'
        f'<text x="32" y="60" font-size="13" fill="{MUTED}">{escape(S("stack_sub"))}</text>'
    )
    write("stack.svg", frame(w, h, S("stack_title"), S("stack_desc"), head + body))


# --------------------------------------------------------------------------- languages donut
def load_languages(refresh: bool) -> dict[str, int]:
    f = ROOT / "data" / "languages.json"
    if refresh:
        names = subprocess.run(
            ["gh", "repo", "list", OWNER, "--visibility", "public", "--limit", "200", "--json", "name", "--jq", ".[].name"],
            capture_output=True, text=True, check=True,
        ).stdout.split()
        total: dict[str, int] = {}
        for n in names:
            out = subprocess.run(["gh", "api", f"repos/{OWNER}/{n}/languages"], capture_output=True, text=True, check=True).stdout
            for k, v in json.loads(out).items():
                total[k] = total.get(k, 0) + v
        f.write_text(json.dumps(total, indent=1), encoding="utf-8")
    return json.loads(f.read_text(encoding="utf-8"))


def build_languages(refresh: bool) -> None:
    data = load_languages(refresh)
    ignore = {"Dockerfile", "CMake", "Makefile", "Mako", "Shell", "Batchfile"}
    data = {k: v for k, v in data.items() if k not in ignore}
    total = sum(data.values())
    top = sorted(data.items(), key=lambda kv: -kv[1])[:6]
    other = total - sum(v for _, v in top)
    if other > 0:
        top.append((S("other"), other))
    colors = {"Python": "#3776AB", "Astro": "#BC52EE", "TypeScript": "#3178C6", "JavaScript": "#F7DF1E",
              "Dart": "#00B4AB", "CSS": "#8957E5", "HTML": "#E34C26", "C++": "#00599C"}
    w, h, cx, cy, r, sw = 1000, 330, 200, 180, 88, 30
    circ = 2 * math.pi * r
    arcs, legend, offset = "", "", 0.0
    for i, (name, val) in enumerate(top):
        frac = val / total
        seg = frac * circ
        col = colors.get(name, "#6e7681")
        arcs += (
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}" '
            f'stroke-dasharray="0 {circ:.2f}" stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})">'
            f'<animate attributeName="stroke-dasharray" from="0 {circ:.2f}" to="{max(seg - 2, 0.5):.2f} {circ - max(seg - 2, 0.5):.2f}" '
            f'begin="{i * 0.2:.1f}s" dur="0.9s" fill="freeze"/></circle>'
        )
        offset += seg
        ly = 98 + i * 33
        legend += (
            f'<g opacity="0">{fade(0.3 + i * 0.12)}<circle cx="430" cy="{ly - 5}" r="7" fill="{col}"/>'
            f'<text x="450" y="{ly}" font-size="15" fill="{TEXT}">{escape(name)}</text>'
            f'<rect x="590" y="{ly - 12}" width="260" height="10" rx="5" fill="{CARD}"/>'
            f'<rect x="590" y="{ly - 12}" width="{260 * frac:.1f}" height="10" rx="5" fill="{col}"/>'
            f'<text x="{w - 40}" y="{ly}" font-size="14" font-weight="600" fill="{TEXT}" text-anchor="end">{frac * 100:.1f}%</text></g>'
        )
    body = (
        f"{card(w, h)}"
        f'<text x="32" y="44" font-size="20" font-weight="700" fill="{TEXT}">{escape(S("lang_title"))}</text>'
        f'<text x="32" y="66" font-size="13" fill="{MUTED}">{escape(S("lang_sub"))}</text>'
        f"{arcs}"
        f'<text x="{cx}" y="{cy - 2}" font-size="30" font-weight="700" fill="{TEXT}" text-anchor="middle">{total / 1e6:.1f}M</text>'
        f'<text x="{cx}" y="{cy + 20}" font-size="12" fill="{MUTED}" text-anchor="middle">{escape(S("lang_unit"))}</text>'
        f"{legend}"
    )
    write("languages.svg", frame(w, h, S("lang_title"), S("lang_desc"), body))


# --------------------------------------------------------------------------- timeline
def build_timeline() -> None:
    w = 1000
    x0, x1, t0, t1 = 250, 960, 2023.0, 2028.0
    X = lambda t: x0 + (t - t0) / (t1 - t0) * (x1 - x0)  # noqa: E731
    eb = S("edu_bars")
    edu = [(eb[0], 2023.67, 2025.67, BLUE), (eb[1], 2025.67, 2027.67, BLUE), (eb[2], 2024.0, 2026.0, VIOLET)]
    work = [("Blue Bird LLC", 2024.917, 2025.083, ORANGE), ("Jardinería Ornamental", 2025.083, 2025.583, GREEN),
            ("GMC Store", 2025.5, 2026.083, GOLD)]
    proj = [("Legatum", 2026.42, 2026.75, "#2ea8a0"), ("Puertia", 2026.6, 2026.77, "#d2699b"), ("Plasticity", 2026.8, 2026.86, "#7c5cff")]
    hacks = [("HACKDGO", 2024.25), ("HackMTY", 2024.8), ("TalentLand", 2025.2), ("HackMTY", 2025.8)]
    top = 118
    h = top + (len(edu) + len(work) + len(proj)) * 34 + 170
    grid = ""
    for yr in range(2023, 2029):
        gx = X(yr)
        grid += (
            f'<line x1="{gx:.1f}" y1="{top - 14}" x2="{gx:.1f}" y2="{h - 36}" stroke="{BORDER}" stroke-dasharray="3 5"/>'
            f'<text x="{gx:.1f}" y="{top - 22}" font-size="12" fill="{MUTED}" text-anchor="middle">{yr}</text>'
        )
    body = (
        f"{card(w, h)}"
        f'<text x="32" y="44" font-size="20" font-weight="700" fill="{TEXT}">{escape(S("tl_title"))}</text>'
        f'<text x="32" y="66" font-size="13" fill="{MUTED}">{escape(S("tl_sub"))}</text>{grid}'
    )
    y, delay = top, 0.0

    def bar(label: str, a: float, b: float, col: str, yy: float) -> str:
        bx, bw = X(a), max(X(b) - X(a), 10)
        inside = bw > len(label) * 7 + 16
        txt = (
            f'<text x="{bx + 12:.1f}" y="{yy + 19}" font-size="12.5" font-weight="600" fill="#0d1117">{escape(label)}</text>'
            if inside else
            f'<text x="{bx + bw + 8:.1f}" y="{yy + 19}" font-size="12.5" font-weight="600" fill="{TEXT}">{escape(label)}</text>'
        )
        return f'<g opacity="0">{fade(delay)}<rect x="{bx:.1f}" y="{yy}" width="{bw:.1f}" height="26" rx="13" fill="{col}"/>{txt}</g>'

    for head, items in ((S("tl_edu"), edu), (S("tl_exp"), work), (S("tl_proj"), proj)):
        body += f'<text x="32" y="{y + 18}" font-size="13" font-weight="700" fill="{TEXT}">{escape(head)}</text>'
        for label, a, b, col in items:
            body += bar(label, a, b, col, y)
            y += 34
            delay += 0.15
        y += 4
    y += 14
    body += f'<text x="32" y="{y + 20}" font-size="13" font-weight="700" fill="{TEXT}">{escape(S("tl_hack"))}</text>'
    for i, (label, t) in enumerate(hacks):
        hx = X(t)
        body += (
            f'<g opacity="0">{fade(delay)}<path d="M{hx:.1f} {y + 4} l9 9 l-9 9 l-9 -9 Z" fill="{VIOLET}"/>'
            f'<text x="{hx:.1f}" y="{y + 42 + (i % 2) * 16}" font-size="12" fill="{TEXT}" text-anchor="middle">{label}</text></g>'
        )
        delay += 0.15
    now = X(2026.85)
    body += (
        f'<line x1="{now:.1f}" y1="{top - 14}" x2="{now:.1f}" y2="{h - 36}" stroke="{ORANGE}" stroke-width="2"/>'
        f'<rect x="{now - 26:.1f}" y="{h - 34}" width="52" height="22" rx="11" fill="{ORANGE}"/>'
        f'<text x="{now:.1f}" y="{h - 19}" font-size="12" font-weight="700" fill="#0d1117" text-anchor="middle">{escape(S("today"))}</text>'
    )
    write("timeline.svg", frame(w, h, S("tl_title"), S("tl_desc"), body))


# --------------------------------------------------------------------------- footer
def build_footer() -> None:
    w, h = 1000, 110
    defs = (
        f'<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BLUE}"/>'
        f'<stop offset="1" stop-color="{VIOLET}"/></linearGradient>'
        f'<clipPath id="clip"><rect width="{w}" height="{h}" rx="20"/></clipPath>'
    )
    wave = lambda amp, dur, op, off: (  # noqa: E731
        f'<path fill="url(#acc)" opacity="{op}" d="M0 {h - 30} Q 125 {h - 30 - amp} 250 {h - 30} T 500 {h - 30} T 750 {h - 30} T 1000 {h - 30} T 1250 {h - 30} V {h} H 0 Z">'
        f'<animateTransform attributeName="transform" type="translate" from="{off}" to="{off - 500}" dur="{dur}s" repeatCount="indefinite"/></path>'
    )
    body = (
        f'<g clip-path="url(#clip)"><rect width="{w}" height="{h}" fill="{BG}"/>{wave(34, 14, .35, 0)}{wave(24, 9, .55, -120)}'
        f'<text x="{w / 2}" y="46" font-size="15" fill="{TEXT}" text-anchor="middle">{escape(S("footer"))}</text></g>'
    )
    write("footer.svg", frame(w, h, "Footer", S("footer_desc"), body, defs))


if __name__ == "__main__":
    refresh = "--refresh" in sys.argv
    for LANG in ("en", "es"):
        build_header()
        build_kpis()
        build_stack()
        build_tests()
        build_languages(refresh and LANG == "en")
        build_timeline()
        build_footer()
