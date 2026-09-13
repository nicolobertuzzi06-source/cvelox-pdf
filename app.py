"""
Servizio web che genera il PDF dei template a sidebar (Creativo, Tecnico, Riflesso) con
WeasyPrint. Espone un endpoint HTTP /generate-pdf pensato per essere chiamato da app.html
(vedi PDF_ENDPOINT nel file principale).

Contiene la stessa logica già testata in api/generate-pdf.py (build_html, _is_dark_color,
ACCENT_DEFAULTS, SIDEBAR_DEFAULTS) avvolta in un piccolo server Flask, perché Render pubblica
servizi web sempre accesi, non funzioni "una tantum" come Vercel/Netlify.
"""

from flask import Flask, request, send_file, jsonify
from weasyprint import HTML
import io

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    # app.html gira su un dominio diverso da questo servizio (es. cvelox.netlify.app vs
    # questo servizio Render): senza queste intestazioni, il browser blocca la richiesta per
    # sicurezza (CORS) prima ancora che arrivi qui — non è un errore visibile, la richiesta
    # semplicemente fallisce in silenzio lato client.
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route('/generate-pdf', methods=['OPTIONS'])
def generate_pdf_preflight():
    # Il browser manda prima una richiesta "OPTIONS" di verifica (preflight) per le richieste
    # POST con corpo JSON da un altro dominio: deve ricevere una risposta vuota ma con le
    # intestazioni CORS sopra, altrimenti blocca la vera richiesta POST che segue.
    return ('', 204)

ACCENT_DEFAULTS = {
    'creativo': '#0F6E5C', 'tecnico': '#1F7A8C', 'riflesso': '#6D5DBB',
    'modern': '#2451B8', 'fascia': '#8E3B6F', 'timeline': '#3D8361', 'junior': '#FF6B5B',
    'servizio': '#2E9E83', 'sviluppo': '#4A5A70', 'rivista': '#C0327A', 'portfolio': '#7C3AED',
    'elegante': '#8A6D2F', 'ats': '#000000',
}
DEFAULT_INK_ACCENT = '#1B1F3B'  # classic, minimal, compatto, executive, accademico, consulenza
# Sfondo di default della sidebar e lato della pagina, fedeli al file originale (app.html):
# Creativo è scuro con testo bianco, Tecnico e Riflesso sono chiari con testo scuro,
# Riflesso ha la sidebar a DESTRA — non è solo una questione di colore, cambia il layout.
SIDEBAR_DEFAULTS = {
    'creativo': {'color': '#1B1F3B', 'side': 'left',  'dark': True},
    'tecnico':  {'color': '#EAF1F3', 'side': 'left',  'dark': False},
    'riflesso': {'color': '#EFEDF7', 'side': 'right', 'dark': False},
}

# Configurazione per i 16 template a colonna singola: nessuno di questi ha bisogno della
# sidebar ricorrente (niente CSS Grid/float coinvolto, il flusso normale si spezza bene tra
# le pagine da solo) — solo differenze di font, colori e piccoli dettagli decorativi, fedeli
# al CSS originale di app.html per ciascuno.
SINGLE_COLUMN_STYLES = {
    'classic':   {'body': '', 'css': ''},
    'modern':    {'body': '', 'css': '''
        h1{ color: var(--accent); }
        h2{ background: var(--accent); color: #fff; padding: 3pt 10pt; border-radius: 4pt; display: inline-block; border: none; }
        .chip{ background: #EAF0FC; color: var(--accent); }
    '''},
    'minimal':   {'body': '', 'css': '''
        h1{ font-weight: 600; border-bottom: 2pt solid var(--accent); padding-bottom: 3pt; display: inline-block; }
        h2{ border: none; font-size: 9pt; letter-spacing: .1em; text-transform: uppercase; color: #63677A; }
        .chip{ background: transparent; border: 1pt solid #DAD7CE; }
    '''},
    'elegante':  {'body': "font-family:'Fraunces',serif; background:#FFFDF8;", 'css': '''
        .identity-block{ text-align: center; }
        h1{ font-size: 24pt; }
        h2{ border-bottom: 1pt solid var(--accent); color: var(--accent); font-family:'Helvetica','Arial',sans-serif; text-align: center; }
    '''},
    'compatto':  {'body': 'font-size:9.5pt; line-height:1.35;', 'css': '''
        body{ border-left: 5pt solid var(--accent); }
        .main{ padding-left: 16pt; }
        h1{ font-size: 16pt; }
        h2{ font-size: 8.5pt; padding: 2pt 6pt; border: none; background: #F1EFE8; display: inline-block; border-radius: 2pt; }
        .entry{ margin-bottom: 6pt; }
    '''},
    'fascia':    {'body': '', 'css': '''
        .banner{ height: 60pt; background: var(--accent); margin: -14mm -10mm 0; }
        .photo{ margin: -34pt auto 8pt; border: 3pt solid #fff; position: relative; }
        .identity-block{ text-align: center; }
        h2{ border-bottom-color: var(--accent); color: var(--accent); }
        .chip{ background: var(--fascia-chip-bg); }
    '''},
    'timeline':  {'body': '', 'css': '''
        h1{ color: var(--accent); }
        h2{ border-bottom-color: var(--accent); }
        .sec-exp, .sec-edu{ position: relative; }
        .entry{ position: relative; padding-left: 16pt; }
        .entry::before{
            content: ""; position: absolute; left: 0; top: 3pt; width: 7pt; height: 7pt;
            border-radius: 50%; background: var(--accent); border: 1.5pt solid #fff; box-shadow: 0 0 0 1pt var(--accent);
        }
    '''},
    'ats':       {'body': 'color:#000;', 'css': '''
        h1, h2{ color: #000; }
        .role, .muted{ color: #444; }
        h2{ border-bottom-color: #000; font-size: 10pt; letter-spacing: .03em; text-transform: uppercase; }
        .chip{ background: none; border: none; padding: 0; border-radius: 0; color: #000; }
        .chip:not(:last-child)::after{ content: " ·"; }
    '''},
    'executive': {'body': "font-family:'Fraunces',serif; background:#FDFCF9;", 'css': '''
        .identity-block{ border-bottom: 4pt double var(--accent); padding-bottom: 10pt; margin-bottom: 4pt; }
        h1{ font-size: 19pt; letter-spacing: .04em; text-transform: uppercase; }
        .role{ font-family:'Helvetica','Arial',sans-serif; text-transform: uppercase; letter-spacing: .12em; font-size: 8pt; }
        h2{ border-top: 1pt solid var(--accent); border-bottom: 1pt solid var(--accent); padding: 4pt 0; font-family:'Helvetica','Arial',sans-serif; }
    '''},
    'junior':    {'body': '', 'css': '''
        h2{ border: none; }
        h2::before{ content: ""; display: inline-block; width: 6pt; height: 6pt; border-radius: 50%; background: var(--accent); margin-right: 6pt; }
        .chip{ background: var(--accent); color: #fff; border-radius: 10pt; }
    '''},
    'accademico':{'body': "font-family:'Fraunces',serif;", 'css': '''
        h1{ font-size: 20pt; }
        .role{ font-style: italic; }
        h2{ font-family:'Helvetica','Arial',sans-serif; font-weight: 600; font-size: 9pt; letter-spacing: .08em; text-transform: uppercase; border-bottom: 1pt solid var(--accent); }
    '''},
    'consulenza':{'body': 'padding:0;', 'css': '''
        .photo{ display: none; }
        .identity-block{ background: var(--accent); color: #fff; padding: 20pt 26pt; }
        .role{ color: rgba(255,255,255,.75); }
        .main{ padding: 0 26pt 20pt; counter-reset: section-count; }
        h2{ border: none; font-weight: 700; counter-increment: section-count; }
        h2::before{ content: counter(section-count, decimal-leading-zero) " — "; color: var(--accent); }
    '''},
    'portfolio': {'body': '', 'css': '''
        h1{ font-size: 28pt; letter-spacing: -.02em; }
        .role{ color: var(--accent); font-weight: 600; }
        h2{ font-size: 14pt; border: none; font-weight: 700; }
        .chip{ background: var(--accent); color: #fff; font-weight: 600; }
    '''},
    'servizio':  {'body': '', 'css': '''
        .entry{ background: #F1EFE8; border-radius: 6pt; padding: 8pt 10pt; }
        h2{ border: none; }
        h2::before{ content: ""; display: inline-block; width: 7pt; height: 7pt; border-radius: 50%; background: var(--accent); margin-right: 6pt; }
        .chip{ background: var(--accent); color: #fff; border-radius: 10pt; }
    '''},
    'sviluppo':  {'body': '', 'css': '''
        h2{ font-family:'Courier New',Courier,monospace; border: none; color: var(--accent); }
        h2::before{ content: "// "; color: #63677A; }
        .entry{ border-left: 2pt solid var(--accent); padding-left: 10pt; }
        .chip{ background: #1B1F3B; color: #7EE7C7; font-family:'Courier New',monospace; border-radius: 2pt; }
    '''},
    'rivista':   {'body': '', 'css': '''
        h1{ font-size: 22pt; text-transform: uppercase; }
        .role{ font-size: 10pt; text-transform: uppercase; letter-spacing: .1em; color: #63677A; }
        .sec-summary{ background: #F1EFE8; border-left: 3pt solid var(--accent); padding: 10pt 14pt; font-style: italic; }
        h2{ font-size: 14pt; font-weight: 800; border: none; border-bottom: 3pt solid var(--accent); display: inline-block; }
    '''},
}


def _mix_color(hex_color, base_hex, weight_pct):
    """Mescola un colore con uno sfondo di base in Python (non con color-mix() in CSS, una
    funzione recente che non sono certo sia supportata da WeasyPrint e non ho potuto
    verificare) — così il risultato è sempre un colore esadecimale semplice, comprensibile da
    qualunque motore CSS senza scommesse."""
    def to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    r1, g1, b1 = to_rgb(hex_color)
    r2, g2, b2 = to_rgb(base_hex)
    w = weight_pct / 100
    r = round(r1 * w + r2 * (1 - w))
    g = round(g1 * w + g2 * (1 - w))
    b = round(b1 * w + b2 * (1 - w))
    return f'#{r:02X}{g:02X}{b:02X}'


def _is_dark_color(hex_color):
    """Vero se un colore è abbastanza scuro da richiedere testo bianco sopra, secondo la
    luminanza percepita — così un colore di sfondo scelto liberamente dall'utente non finisce
    mai con testo scuro sopra sfondo scuro (o viceversa), illeggibile."""
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) != 6:
        return False
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return False
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance < 0.55


def escape(s):
    if not s:
        return ''
    return (str(s)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;'))


def build_html(data):
    """Costruisce l'HTML+CSS del CV a partire dai dati inviati dal client.
    Riusabile indipendentemente dalla piattaforma serverless scelta."""
    template = data.get('template', 'creativo')
    accent = data.get('accentColor') or ACCENT_DEFAULTS.get(template, '#0F6E5C')

    # Larghezza sidebar personalizzabile. Minimo alzato a 30mm dopo un test reale: con 26mm
    # persino le intestazioni fisse ("Competenze") si spezzavano a metà parola, e "Lingue"
    # arrivava a sovrapporsi al livello indicato — non un compromesso accettabile.
    # 55mm come massimo per non lasciare la colonna principale troppo stretta a sua volta.
    sidebar_width = data.get('sidebarWidth', 32)
    try:
        sidebar_width = float(sidebar_width)
    except (TypeError, ValueError):
        sidebar_width = 32
    sidebar_width = max(30, min(55, sidebar_width))
    defaults = SIDEBAR_DEFAULTS.get(template, SIDEBAR_DEFAULTS['tecnico'])
    sidebar_color = data.get('sidebarColor') or defaults['color']
    sidebar_side = defaults['side']  # 'left' o 'right': non personalizzabile via dati, è identità del template
    sidebar_dark = defaults['dark'] if not data.get('sidebarColor') else _is_dark_color(data['sidebarColor'])
    text_color = '#FFFFFF' if sidebar_dark else '#1B1F3B'
    muted_color = 'rgba(255,255,255,.75)' if sidebar_dark else '#63677A'
    chip_bg = 'rgba(255,255,255,.12)' if sidebar_dark else '#FFFFFF'

    name = escape(data.get('name', ''))
    role = escape(data.get('role', ''))

    contact_parts = [p for p in [data.get('email'), data.get('phone'), data.get('city')] if p]
    if data.get('license'):
        contact_parts.append('Patente ' + data['license'])
    contact = ' &middot; '.join(escape(p) for p in contact_parts)

    skills_html = ''.join(
        f'<span class="chip">{escape(s)}</span>' for s in data.get('skills', [])
    )
    langs_html = ''.join(
        f'<div class="lang-row"><span>{escape(l.get("name",""))}</span>'
        f'<span>{escape(l.get("level",""))}</span></div>'
        for l in data.get('languages', [])
    )

    exp_html = ''
    for e in data.get('experiences', []):
        header = escape(e.get('role', '')) + (' — ' + escape(e.get('org', '')) if e.get('org') else '')
        period = escape(e.get('period', ''))
        text = escape(e.get('improved') or e.get('raw') or '')
        exp_html += f'''
        <div class="entry">
          <div class="entry-top"><strong>{header}</strong><span class="period">{period}</span></div>
          <p>{text}</p>
        </div>'''

    edu_html = ''
    for e in data.get('educations', []):
        edu_html += f'''
        <div class="entry">
          <div class="entry-top"><strong>{escape(e.get("title",""))}</strong><span class="period">{escape(e.get("period",""))}</span></div>
          <p class="muted">{escape(e.get("school",""))}</p>
        </div>'''

    photo_html = f'<img class="photo" src="{data["photoDataUrl"]}">' if data.get('photoDataUrl') else ''

    margin_side = 'left' if sidebar_side == 'left' else 'right'
    page_margin = f"0 0 0 {sidebar_width}mm" if sidebar_side == 'left' else f"0 {sidebar_width}mm 0 0"
    margin_box = f"@{margin_side}-top"
    sidebar_border_color = 'rgba(255,255,255,.25)' if sidebar_dark else 'rgba(27,31,59,.15)'

    return f'''<!doctype html>
<html><head><meta charset="utf-8">
<style>
  @page {{
    size: A4; margin: {page_margin};
    {margin_box} {{ content: element(sidebar); margin: 0; padding: 0; }}
  }}
  body {{ font-family: 'Helvetica', 'Arial', sans-serif; font-size: 10.5pt; color: #1B1F3B; margin: 0; }}

  /* Sidebar RICORRENTE: vedi commento in cima al file. position:running() la toglie dal
     flusso normale e la registra come contenuto della casella di margine (a sinistra o a
     destra secondo il template — Riflesso è a destra, fedele all'originale) che il motore
     ripete identica su ogni pagina generata. Larghezza e colore sono personalizzabili
     (sidebarWidth in mm, sidebarColor); se l'utente sceglie un colore, il testo passa
     automaticamente bianco o scuro secondo la luminanza, per restare leggibile. */
  .sidebar{{
    position: running(sidebar);
    width: {sidebar_width}mm; background: {sidebar_color}; color: {text_color};
    padding: 14mm 6mm; box-sizing: border-box; height: 297mm;
    overflow-wrap: break-word; word-break: break-word; /* niente testo che esce dal riquadro, qualunque sia la larghezza */
  }}
  .main{{ padding: 14mm 10mm; box-sizing: border-box; }}

  .entry, .chip {{ page-break-inside: avoid; }}

  .photo{{ width: 20mm; height: 20mm; border-radius: 50%; object-fit: cover; display: block; margin-bottom: 8mm; }}
  h1{{ font-size: 18pt; margin: 0 0 2mm; overflow-wrap: break-word; color: #1B1F3B; }}
  .role{{ color: #63677A; margin-bottom: 4mm; }}
  /* Intestazioni nella sidebar: colore accento, bordo tenue adattato a sfondo chiaro/scuro
     (fedele all'originale: nel Creativo il bordo è bianco semitrasparente, non l'accento). */
  .sidebar h2{{
    font-size: 10pt; text-transform: uppercase; letter-spacing: .04em; color: {accent};
    border-bottom: 1pt solid {sidebar_border_color}; padding-bottom: 1mm; margin: 6mm 0 3mm;
    white-space: nowrap;
  }}
  /* Intestazioni nel corpo principale: testo scuro, bordo dell'accento — fedeli all'originale. */
  .main h2{{
    font-size: 10pt; text-transform: uppercase; letter-spacing: .04em; color: #1B1F3B;
    border-bottom: 1pt solid {accent}; padding-bottom: 1mm; margin: 6mm 0 3mm;
  }}
  .chip{{
    display: inline-block; background: {chip_bg}; color: {text_color}; border-radius: 3mm;
    padding: 1mm 3mm; margin: 0 1mm 1mm 0; font-size: 9pt; overflow-wrap: break-word; max-width: 100%;
  }}
  .entry{{ margin-bottom: 4mm; }}
  .entry-top{{ display: flex; justify-content: space-between; font-size: 10pt; }}
  .period{{ color: #63677A; font-size: 9pt; }}
  .muted{{ color: #63677A; }}
  .sidebar p, .sidebar .lang-row {{ color: {text_color}; }}
  .sidebar .lang-row span:last-child {{ color: {muted_color}; }}
  .lang-row{{
    display: flex; flex-wrap: wrap; justify-content: space-between; font-size: 9.5pt;
    margin-bottom: 2mm; gap: 1mm 4pt;
    /* flex-wrap:wrap invece che nowrap: se nome lingua + livello non ci stanno affiancati,
       il livello va a capo sotto invece di sovrapporsi al nome (bug reale visto in test) */
  }}

</style></head>
<body>
  <div class="sidebar">
    {photo_html}
    <h2>Contatti</h2>
    <p style="font-size:9pt;">{contact}</p>
    {'<h2>Competenze</h2>' + skills_html if skills_html else ''}
    {'<h2>Lingue</h2>' + langs_html if langs_html else ''}
  </div>
  <div class="main">
    <h1>{name}</h1>
    <p class="role">{role}</p>
    {'<h2>Profilo</h2><p>' + escape(data.get("summary", "")) + '</p>' if data.get("summary") else ''}
    {'<h2>Esperienze</h2>' + exp_html if exp_html else ''}
    {'<h2>Istruzione</h2>' + edu_html if edu_html else ''}
  </div>
</body></html>'''


def build_single_column_html(data):
    """CV a colonna singola: nessun trucco di impaginazione necessario (niente CSS Grid o
    elementi ricorrenti), il flusso normale del documento si spezza bene tra le pagine da
    solo — motivo per cui questi 16 template non avevano il bug delle sidebar a due colonne."""
    template = data.get('template', 'classic')
    style = SINGLE_COLUMN_STYLES.get(template, SINGLE_COLUMN_STYLES['classic'])
    accent = data.get('accentColor') or ACCENT_DEFAULTS.get(template, DEFAULT_INK_ACCENT)

    name = escape(data.get('name', ''))
    role = escape(data.get('role', ''))
    contact_parts = [p for p in [data.get('email'), data.get('phone'), data.get('city')] if p]
    if data.get('license'):
        contact_parts.append('Patente ' + data['license'])
    contact = ' &middot; '.join(escape(p) for p in contact_parts)

    skills_html = ''.join(f'<span class="chip">{escape(s)}</span>' for s in data.get('skills', []))
    langs_html = ''.join(
        f'<div class="lang-row"><span>{escape(l.get("name",""))}</span>'
        f'<span>{escape(l.get("level",""))}</span></div>'
        for l in data.get('languages', [])
    )
    exp_html = ''
    for e in data.get('experiences', []):
        header = escape(e.get('role', '')) + (' — ' + escape(e.get('org', '')) if e.get('org') else '')
        period = escape(e.get('period', ''))
        text = escape(e.get('improved') or e.get('raw') or '')
        exp_html += f'''
        <div class="entry">
          <div class="entry-top"><strong>{header}</strong><span class="period">{period}</span></div>
          <p>{text}</p>
        </div>'''
    edu_html = ''
    for e in data.get('educations', []):
        edu_html += f'''
        <div class="entry">
          <div class="entry-top"><strong>{escape(e.get("title",""))}</strong><span class="period">{escape(e.get("period",""))}</span></div>
          <p class="muted">{escape(e.get("school",""))}</p>
        </div>'''

    # Consulenza nasconde la foto (fedele all'originale); Fascia la vuole sopra un banner colorato.
    show_photo = data.get('photoDataUrl') and template != 'consulenza'
    photo_html = f'<img class="photo" src="{data["photoDataUrl"]}">' if show_photo else ''
    banner_html = '<div class="banner"></div>' if template == 'fascia' else ''

    extra_css = style['css'].replace('var(--accent)', accent).replace(
        'var(--fascia-chip-bg)', _mix_color(accent, '#F1EFE8', 12)
    )
    body_extra = style['body'].replace('var(--accent)', accent)

    summary_text = escape(data.get('summary', ''))
    sections_html = ''
    if summary_text:
        sections_html += f'<div class="cv-section sec-summary"><h2>Profilo</h2><p>{summary_text}</p></div>'
    if exp_html:
        sections_html += f'<div class="cv-section sec-exp"><h2>Esperienze</h2>{exp_html}</div>'
    if edu_html:
        sections_html += f'<div class="cv-section sec-edu"><h2>Istruzione</h2>{edu_html}</div>'
    if skills_html:
        sections_html += f'<div class="cv-section"><h2>Competenze</h2>{skills_html}</div>'
    if langs_html:
        sections_html += f'<div class="cv-section"><h2>Lingue</h2>{langs_html}</div>'

    return f'''<!doctype html>
<html><head><meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 14mm 10mm; }}
  body {{ font-family: 'Helvetica', 'Arial', sans-serif; font-size: 10.5pt; color: #1B1F3B; margin: 0; {body_extra} }}
  .entry, .chip {{ page-break-inside: avoid; }}
  .photo{{ width: 20mm; height: 20mm; border-radius: 50%; object-fit: cover; display: block; margin-bottom: 8pt; }}
  h1{{ font-size: 16pt; margin: 0 0 3pt; overflow-wrap: break-word; }}
  .role{{ color: #63677A; margin-bottom: 3pt; }}
  .cv-contact{{ color: #63677A; font-size: 9.5pt; margin-bottom: 10pt; overflow-wrap: break-word; }}
  h2{{
    font-size: 10pt; color: {accent};
    border-bottom: 1pt solid {accent}; padding-bottom: 2pt; margin: 12pt 0 6pt;
  }}
  .chip{{ display: inline-block; background: #F1EFE8; border-radius: 8pt; padding: 2pt 8pt; margin: 0 3pt 3pt 0; font-size: 9pt; overflow-wrap: break-word; }}
  .entry{{ margin-bottom: 8pt; }}
  .entry-top{{ display: flex; justify-content: space-between; font-size: 10pt; }}
  .period{{ color: #63677A; font-size: 9pt; }}
  .muted{{ color: #63677A; }}
  .lang-row{{ display: flex; flex-wrap: wrap; justify-content: space-between; font-size: 9.5pt; margin-bottom: 3pt; gap: 2pt 8pt; }}
  {extra_css}
</style></head>
<body>
  {banner_html}
  <div class="identity-block">
    {photo_html}
    <h1>{name}</h1>
    <p class="role">{role}</p>
    <p class="cv-contact">{contact}</p>
  </div>
  <div class="main">
    {sections_html}
  </div>
</body></html>'''


def generate_cv_html(data):
    """Smista tra le due tecniche secondo il template scelto: i tre a sidebar (Creativo,
    Tecnico, Riflesso) usano l'elemento ricorrente; tutti gli altri 16 usano il flusso a
    colonna singola, molto più semplice perché non hanno il bug da aggirare."""
    template = data.get('template', 'classic')
    if template in SIDEBAR_DEFAULTS:
        return build_html(data)
    return build_single_column_html(data)


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json(force=True)
        html_string = generate_cv_html(data)
        pdf_bytes = HTML(string=html_string).write_pdf()
        filename = (data.get('name', 'CV').strip().replace(' ', '_') or 'CV') + '.pdf'
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/', methods=['GET'])
def health():
    # Render usa questa rotta per sapere se il servizio è vivo — utile anche per verificare
    # a occhio, aprendo l'indirizzo nel browser, che il deploy sia andato a buon fine.
    return jsonify({'status': 'ok', 'service': 'cvelox-pdf-generator'})


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
