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
    'creativo': '#0F6E5C',
    'tecnico': '#1F7A8C',
    'riflesso': '#6D5DBB',
}
SIDEBAR_DEFAULTS = {
    'creativo': {'color': '#1B1F3B', 'side': 'left',  'dark': True},
    'tecnico':  {'color': '#EAF1F3', 'side': 'left',  'dark': False},
    'riflesso': {'color': '#EFEDF7', 'side': 'right', 'dark': False},
}


def _is_dark_color(hex_color):
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
    template = data.get('template', 'creativo')
    accent = data.get('accentColor') or ACCENT_DEFAULTS.get(template, '#0F6E5C')

    sidebar_width = data.get('sidebarWidth', 32)
    try:
        sidebar_width = float(sidebar_width)
    except (TypeError, ValueError):
        sidebar_width = 32
    sidebar_width = max(30, min(55, sidebar_width))

    defaults = SIDEBAR_DEFAULTS.get(template, SIDEBAR_DEFAULTS['tecnico'])
    sidebar_color = data.get('sidebarColor') or defaults['color']
    sidebar_side = defaults['side']
    sidebar_dark = defaults['dark'] if not data.get('sidebarColor') else _is_dark_color(data['sidebarColor'])
    text_color = '#FFFFFF' if sidebar_dark else '#1B1F3B'
    muted_color = 'rgba(255,255,255,.75)' if sidebar_dark else '#63677A'
    chip_bg = 'rgba(255,255,255,.12)' if sidebar_dark else '#FFFFFF'

    name = escape(data.get('name', ''))
    role = escape(data.get('role', ''))

    contact_parts = [p for p in [data.get('email'), data.get('phone'), data.get('city')] if p]
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
  .sidebar{{
    position: running(sidebar);
    width: {sidebar_width}mm; background: {sidebar_color}; color: {text_color};
    padding: 14mm 6mm; box-sizing: border-box; height: 297mm;
    overflow-wrap: break-word; word-break: break-word;
  }}
  .main{{ padding: 14mm 10mm; box-sizing: border-box; }}
  .entry, .chip {{ page-break-inside: avoid; }}
  .photo{{ width: 20mm; height: 20mm; border-radius: 50%; object-fit: cover; display: block; margin-bottom: 8mm; }}
  h1{{ font-size: 18pt; margin: 0 0 2mm; overflow-wrap: break-word; color: #1B1F3B; }}
  .role{{ color: #63677A; margin-bottom: 4mm; }}
  .sidebar h2{{
    font-size: 10pt; text-transform: uppercase; letter-spacing: .04em; color: {accent};
    border-bottom: 1pt solid {sidebar_border_color}; padding-bottom: 1mm; margin: 6mm 0 3mm;
    white-space: nowrap;
  }}
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
  .lang-row{{ display: flex; flex-wrap: wrap; justify-content: space-between; font-size: 9.5pt; margin-bottom: 2mm; gap: 1mm 4pt; }}
</style></head>
<body>
  <div class="sidebar">
    {photo_html}
    <h2>Contatti</h2>
    <p style="font-size:9pt;">{contact}</p>
    <h2>Competenze</h2>
    {skills_html}
    <h2>Lingue</h2>
    {langs_html}
  </div>
  <div class="main">
    <h1>{name}</h1>
    <p class="role">{role}</p>
    <h2>Profilo</h2>
    <p>{escape(data.get("summary", ""))}</p>
    <h2>Esperienze</h2>
    {exp_html}
    <h2>Istruzione</h2>
    {edu_html}
  </div>
</body></html>'''


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json(force=True)
        html_string = build_html(data)
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
