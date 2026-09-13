"""
Servizio web che genera il PDF del CV usando IL VERO CSS di app.html, non una ricostruzione
a mano — vedi il LEGGIMI per il perché di questo cambio di architettura (i tentativi
precedenti, con CSS riscritto in Python, non erano mai perfettamente fedeli all'originale:
maiuscole sbagliate, campi mancanti, larghezze indovinate). Ora il client manda l'HTML già
renderizzato del CV (con tutti gli stili reali già applicati dal browser dell'utente) e
questo servizio lo incornicia con lo stesso identico CSS di app.html più le regole di
impaginazione da stampa necessarie solo per Creativo/Tecnico/Riflesso (sidebar ricorrente).
"""

from flask import Flask, request, send_file, jsonify
from weasyprint import HTML
import io

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route('/generate-pdf', methods=['OPTIONS'])
def generate_pdf_preflight():
    return ('', 204)


GOOGLE_FONTS_IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=Fraunces:wght@500;600&display=swap');"

# CSS VERO, copiato identico da app.html (non riscritto a mano) — così qualunque colore,
# font, spaziatura o dettaglio del template è sempre lo stesso dell'anteprima a schermo.
REAL_CV_CSS = \
"""  :root{
    --ink:#1B1F3B;
    --paper:#FAF9F6;
    --paper-dim:#F1EFE8;
    --highlight:#FFC93C;
    --muted:#63677A;
    --line:#DAD7CE;
    --white:#FFFFFF;
    --danger:#B3432B;
    --success:#1E7F52;
    --accent-modern:#2451B8;
    --accent-creative:#0F6E5C;
    --accent-tecnico:#1F7A8C;
    --accent-fascia:#8E3B6F;
    --accent-riflesso:#6D5DBB;
    --accent-timeline:#3D8361;
    --accent-junior:#FF6B5B;
    --accent-servizio:#2E9E83;
    --accent-sviluppo:#4A5A70;
    --accent-rivista:#C0327A;
    --accent-portfolio:#7C3AED;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  body{
    background:var(--paper-dim);color:var(--ink);
    font-family:'Inter',sans-serif;-webkit-font-smoothing:antialiased;
  }
  h1,h2,h3,.brand{font-family:'Space Grotesk',sans-serif;}

  /* ---------- TOPBAR ---------- */
  .topbar{
    display:flex;align-items:center;justify-content:space-between;
    padding:14px 24px;background:var(--paper);border-bottom:1px solid var(--line);
    position:sticky;top:0;z-index:30;
  }
  .brand{font-size:19px;font-weight:700;display:flex;align-items:center;gap:6px;}
  .brand a{color:var(--ink);text-decoration:none;display:flex;align-items:center;gap:2px;}
  .brand .dot{color:var(--highlight);}
  .brand .cv-part{color:var(--highlight);}
  .brand .badge-mini{font-size:10.5px;font-weight:600;color:var(--muted);border:1px solid var(--line);border-radius:20px;padding:2px 8px;margin-left:6px;}
  .top-actions{display:flex;gap:12px;align-items:center;}
  .account-area{display:flex;gap:12px;align-items:center;font-size:13px;}
  .account-area .account-email{color:var(--muted);max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .progress-pill{
    font-size:12.5px;color:var(--muted);background:var(--paper-dim);
    padding:6px 12px;border-radius:20px;display:flex;align-items:center;gap:8px;
  }
  .progress-track{width:64px;height:5px;border-radius:3px;background:var(--line);overflow:hidden;}
  .progress-fill{height:100%;background:var(--ink);border-radius:3px;transition:width .3s ease;}
  .btn{
    display:inline-flex;align-items:center;gap:8px;background:var(--ink);color:var(--paper);
    padding:10px 18px;border-radius:8px;border:1px solid var(--ink);
    font-size:14.5px;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif;
  }
  .btn:hover{opacity:.92;}
  .btn.secondary{background:transparent;color:var(--ink);}
  .btn:disabled{opacity:.55;cursor:default;}
  .link-btn{background:none;border:none;color:var(--muted);font-size:13px;cursor:pointer;text-decoration:underline;padding:0;font-family:'Inter',sans-serif;}
  .link-btn.remove{color:var(--danger);}

  /* ---------- GALLERY SCREEN ---------- */
  #gallery-screen{max-width:1120px;margin:0 auto;padding:56px 32px 90px;}
  .entry-choice{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:40px;}
  .entry-card{border:1.5px solid var(--line);border-radius:12px;padding:20px 22px;background:var(--white);cursor:pointer;text-align:left;font-family:'Inter',sans-serif;}
  .entry-card:hover{border-color:var(--ink);}
  .entry-card h3{font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:600;margin-bottom:4px;}
  .entry-card p{font-size:13px;color:var(--muted);}
  .entry-upload-panel{border:1px dashed var(--line);border-radius:10px;padding:16px 18px;margin:-16px 0 40px;background:var(--paper-dim);}
  .entry-upload-panel p{font-size:13.5px;color:var(--muted);margin-bottom:10px;}
  .entry-upload-panel input[type="file"]{display:block;}
  #field-import-notes{border:1px solid #E8C27A;background:#FFF8EC;border-radius:10px;padding:20px 22px;}
  .gallery-head{max-width:620px;margin-bottom:28px;}
  .gallery-head h1{font-size:32px;font-weight:600;letter-spacing:-0.01em;}
  .gallery-head p{color:var(--muted);margin-top:12px;font-size:15.5px;line-height:1.6;}
  .filter-bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:30px;}
  .filter-chip{padding:7px 15px;border-radius:20px;border:1px solid var(--line);background:var(--white);font-size:13px;color:var(--muted);cursor:pointer;font-family:'Inter',sans-serif;}
  .filter-chip.active{background:var(--ink);color:var(--paper);border-color:var(--ink);}
  .gallery-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;}
  .gallery-card{
    background:var(--white);border:1px solid var(--line);border-radius:12px;
    overflow:hidden;cursor:pointer;transition:transform .15s ease, box-shadow .15s ease;
  }
  .gallery-card:hover{transform:translateY(-4px);box-shadow:0 20px 38px -22px rgba(27,31,59,.4);}
  .gallery-thumb{height:236px;overflow:hidden;position:relative;background:var(--paper-dim);}
  .mini-cv{transform:scale(.365);transform-origin:top left;pointer-events:none;}
  .cv-page.mini-cv{width:274%;max-width:none;min-height:640px;}
  .badge-chip{font-size:10.5px;font-weight:600;padding:3px 9px;border-radius:20px;background:var(--ink);color:#fff;white-space:nowrap;flex-shrink:0;}
  .badge-chip.badge-recommended{background:var(--accent-modern);}
  .badge-chip.badge-ats{background:#000;}
  .badge-chip.badge-junior{background:var(--accent-junior);}
  .gallery-card:hover .gallery-thumb::after{
    content:"Usa questo modello";position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
    background:rgba(27,31,59,.55);color:#fff;font-weight:600;font-size:14px;font-family:'Space Grotesk',sans-serif;
  }
  .gallery-label{padding:14px 16px;}
  .gallery-label .name-row{display:flex;justify-content:space-between;align-items:center;}
  .gallery-label span.name{font-weight:600;font-size:14.5px;}
  .gallery-label span.tag{font-size:12.5px;color:var(--muted);display:block;margin-top:3px;}
  .gallery-skip{margin-top:36px;text-align:center;}

  .trust-strip{display:flex;gap:30px;margin-top:44px;padding-top:30px;border-top:1px solid var(--line);flex-wrap:wrap;}
  .trust-item{display:flex;align-items:center;gap:8px;font-size:13.5px;color:var(--muted);}
  .trust-item::before{content:"✓";color:var(--success);font-weight:700;}

  .reviews-strip{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:26px;}
  .review-card{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:18px 20px;}
  .review-stars{color:var(--highlight);letter-spacing:2px;margin-bottom:10px;font-size:13px;}
  .review-quote{font-size:13.5px;color:var(--ink);line-height:1.5;}
  .review-name{margin-top:12px;font-weight:600;font-size:12.5px;color:var(--muted);display:flex;align-items:center;gap:8px;}
  .review-avatar{width:26px;height:26px;border-radius:50%;flex-shrink:0;}

  /* ---------- BUILDER ---------- */
  #builder-screen{display:none;}
  .layout{display:grid;grid-template-columns:1fr 1fr;gap:0;min-height:calc(100vh - 61px);}
  .form-pane{padding:32px;max-width:640px;margin:0 auto;width:100%;min-width:0;}
  .preview-pane{
    background:var(--paper-dim);padding:32px;display:flex;flex-direction:column;
    align-items:center;position:sticky;top:61px;
    height:calc(100vh - 61px);overflow:auto;
  }
  .accent-picker{display:flex;gap:9px;align-items:center;margin-bottom:14px;width:100%;max-width:600px;}
  .accent-picker .accent-label{font-size:12px;color:var(--muted);margin-right:2px;}
  .accent-dot{width:22px;height:22px;border-radius:50%;border:2px solid var(--white);box-shadow:0 0 0 1px var(--line);cursor:pointer;padding:0;}
  .accent-dot.active{box-shadow:0 0 0 2px var(--ink);}
  .style-controls{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:14px;width:100%;max-width:600px;}
  .style-control-label{display:flex;flex-direction:column;gap:4px;font-size:12px;color:var(--muted);flex:1 1 140px;}
  .style-control-label select{padding:7px 8px;border:1px solid var(--line);border-radius:7px;font-family:'Inter',sans-serif;font-size:13px;background:var(--white);color:var(--ink);}

  .template-switch{
    display:flex;flex-wrap:wrap;gap:6px;margin-bottom:18px;
    background:var(--white);border:1px solid var(--line);border-radius:9px;padding:5px;width:100%;max-width:600px;
  }
  .template-switch button{
    flex:1 1 22%;padding:8px 6px;border:none;background:transparent;border-radius:6px;
    font-size:12.5px;font-family:'Inter',sans-serif;cursor:pointer;color:var(--muted);
  }
  .template-switch button.active{background:var(--ink);color:var(--paper);}
  .back-link{font-size:13px;color:var(--muted);text-decoration:underline;cursor:pointer;margin-bottom:16px;display:inline-block;}

  .scrivania-bridge{border:1px dashed var(--line);border-radius:8px;padding:12px 14px;margin-bottom:14px;width:100%;max-width:600px;background:var(--paper-dim);}
  .scrivania-bridge p{margin:0 0 8px;}
  #interview-prep-result ul{margin-top:0;}
  #onepage-warning{width:100%;max-width:600px;margin-bottom:14px;color:var(--danger);}

  .stepper{display:flex;gap:8px;overflow-x:auto;margin-bottom:28px;padding-bottom:6px;scrollbar-width:thin;}
  .step-pill{flex-shrink:0;padding:7px 14px;border-radius:20px;border:1px solid var(--line);background:var(--white);font-size:12.5px;color:var(--muted);cursor:pointer;font-family:'Inter',sans-serif;white-space:nowrap;}
  .step-pill.active{background:var(--ink);color:var(--paper);border-color:var(--ink);}

  .field-group{margin-bottom:34px;scroll-margin-top:172px;}
  .field-group h2{font-size:18px;font-weight:600;margin-bottom:4px;display:flex;align-items:center;}
  .field-group .hint{font-size:13px;color:var(--muted);margin-bottom:14px;}
  label{display:flex;align-items:center;font-size:13px;color:var(--muted);margin-bottom:6px;margin-top:14px;}
  input,textarea{
    width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:7px;
    font-family:'Inter',sans-serif;font-size:14.5px;background:var(--white);color:var(--ink);
  }
  input[type="checkbox"]{width:auto;margin-right:8px;}
  textarea{resize:vertical;min-height:70px;}
  input:focus,textarea:focus{outline:2px solid var(--ink);outline-offset:1px;}
  .row2{display:grid;grid-template-columns:1fr 1fr;gap:14px;}

  /* tooltip / hint icon */
  .tip{position:relative;display:inline-flex;margin-left:6px;}
  .tip button{width:16px;height:16px;border-radius:50%;border:1px solid var(--line);background:var(--white);color:var(--muted);font-size:10px;line-height:1;cursor:pointer;font-family:'Inter',sans-serif;padding:0;}
  .tip .tip-bubble{
    position:absolute;left:0;top:22px;background:var(--ink);color:#fff;font-size:12.5px;
    padding:10px 12px;border-radius:8px;width:230px;z-index:40;display:none;line-height:1.5;font-weight:400;
  }
  .tip:hover .tip-bubble,.tip.open .tip-bubble{display:block;}

  .suggestion-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}
  .suggestion-row.small{margin-top:6px;}
  .suggestion-chip{border:1px dashed var(--line);background:var(--white);border-radius:16px;padding:5px 11px;font-size:12px;color:var(--muted);cursor:pointer;font-family:'Inter',sans-serif;}
  .suggestion-chip:hover{border-color:var(--ink);color:var(--ink);}

  .entry{border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:14px;background:var(--white);}
  .entry-head{display:flex;justify-content:space-between;align-items:center;}
  .entry-head span{font-size:13px;color:var(--muted);}

  .ai-row{display:flex;justify-content:flex-end;gap:14px;align-items:center;margin-top:8px;}
  .guided-panel{border:1px dashed var(--line);border-radius:8px;padding:14px 16px;margin:12px 0;background:var(--paper-dim);}
  .guided-panel label{margin-top:10px;display:block;}
  .guided-panel label:first-of-type{margin-top:0;}
  .ai-btn{
    background:var(--highlight);color:var(--ink);border:none;border-radius:7px;
    padding:8px 14px;font-size:13.5px;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif;
  }
  .ai-btn:disabled{opacity:.6;cursor:default;}
  .ai-note{font-size:12.5px;color:var(--muted);margin-top:6px;}
  .spellcheck-btn{background:none;border:1px dashed var(--line);color:var(--muted);border-radius:7px;padding:7px 12px;font-size:12.5px;cursor:pointer;font-family:'Inter',sans-serif;}
  .spellcheck-btn:hover{border-color:var(--ink);color:var(--ink);}
  .spellcheck-result{display:none;font-size:12.5px;color:var(--ink);background:var(--paper-dim);border-radius:7px;padding:10px 12px;margin-top:8px;white-space:pre-line;}

  .add-btn{
    width:100%;padding:10px;border:1px dashed var(--line);border-radius:8px;
    background:transparent;color:var(--muted);cursor:pointer;font-size:14px;font-family:'Inter',sans-serif;
  }
  .add-btn:hover{border-color:var(--ink);color:var(--ink);}

  .photo-row{display:flex;align-items:center;gap:14px;margin-top:14px;}
  .photo-preview{width:56px;height:56px;border-radius:50%;background:var(--paper-dim);border:1px solid var(--line);object-fit:cover;flex-shrink:0;}
  .photo-actions{display:flex;gap:10px;font-size:13px;}
  .photo-actions label.upload{cursor:pointer;text-decoration:underline;color:var(--ink);}
  input[type="file"]{display:none;}

  .photo-editor-stage{
    width:220px;height:220px;margin:0 auto 16px;border-radius:50%;overflow:hidden;
    position:relative;background:#DDD;cursor:grab;touch-action:none;
  }
  .photo-editor-stage:active{cursor:grabbing;}
  .photo-editor-stage img{position:absolute;user-select:none;-webkit-user-drag:none;}
  .zoom-row{display:flex;align-items:center;gap:10px;}
  .zoom-row input[type="range"]{flex:1;}

  .photo-controls{margin-top:14px;padding:14px;border:1px solid var(--line);border-radius:8px;background:var(--paper-dim);}
  .shape-row{display:flex;gap:8px;margin-bottom:12px;}
  .shape-btn{padding:6px 13px;border-radius:20px;border:1px solid var(--line);background:var(--white);font-size:12.5px;color:var(--muted);cursor:pointer;font-family:'Inter',sans-serif;}
  .shape-btn.active{background:var(--ink);color:var(--paper);border-color:var(--ink);}
  .photo-controls .hint{margin-top:10px;margin-bottom:0;}
  #p-photo{cursor:move;touch-action:none;}

  .chip-list{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}
  .chip{background:var(--paper-dim);padding:6px 12px;border-radius:20px;font-size:13px;display:flex;align-items:center;gap:8px;}
  .chip button{background:none;border:none;color:var(--muted);cursor:pointer;font-size:14px;line-height:1;}

  .signature-pad{width:100%;max-width:380px;height:130px;border:1px solid var(--line);border-radius:8px;background:var(--white);touch-action:none;cursor:crosshair;display:block;}
  .signature-actions{display:flex;gap:12px;align-items:center;margin-top:10px;}

  .cv-page .sec-signature{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;}
  .cv-page .signature-consent{font-size:11px;color:var(--muted);max-width:340px;line-height:1.4;}
  .cv-page .signature-block{text-align:center;flex-shrink:0;}
  .cv-page .signature-block img{height:52px;display:block;margin:0 auto 4px;}
  .cv-page .signature-block .signature-date{font-size:11.5px;color:var(--muted);border-top:1px solid var(--line);padding-top:4px;}

  /* ---------- CV RENDER (shared by builder + gallery thumbnails) ---------- */
  .cv-page{
    background:var(--white);width:100%;max-width:600px;min-height:420px;
    padding:52px 48px;box-shadow:0 20px 50px -28px rgba(27,31,59,.35);
    position:relative;font-size:14px;line-height:1.5;color:#22263F;
    display:flex;flex-direction:column;
  }
  .cv-page .cv-photo{width:76px;height:76px;border-radius:50%;object-fit:cover;order:0;}
  .cv-page .cv-identity{order:1;}
  .cv-page .cv-name{font-size:28px;font-weight:700;font-family:'Space Grotesk',sans-serif;}
  .cv-page .cv-role{color:var(--muted);font-size:14.5px;margin-top:2px;}
  .cv-page .cv-contact{color:var(--muted);font-size:13px;margin-top:6px;order:2;}
  .cv-page .cv-section{margin-top:24px;}
  .cv-page .cv-section h3{
    font-size:12.5px;letter-spacing:.04em;color:var(--ink);
    border-bottom:1.5px solid var(--ink);padding-bottom:4px;margin-bottom:10px;font-weight:600;
  }
  .cv-page .sec-summary{order:3;} .cv-page .sec-exp{order:var(--order-exp, 4);} .cv-page .sec-edu{order:var(--order-edu, 5);}
  .cv-page .sec-skills{order:6;} .cv-page .sec-lang{order:7;} .cv-page .sec-cert{order:8;} .cv-page .sec-hobbies{order:9;} .cv-page .sec-signature{order:10;}
  .cv-page .cv-entry{margin-bottom:14px;}
  .cv-page .cv-entry .top{display:flex;justify-content:space-between;font-weight:600;font-size:14px;}
  .cv-page .cv-entry .sub{color:var(--muted);font-size:12.5px;margin-bottom:4px;}
  .cv-page .cv-entry ul{margin-left:16px;margin-top:4px;}
  .cv-page .chips-preview{display:flex;flex-wrap:wrap;gap:6px;}
  .cv-page .skill-chip{background:var(--paper-dim);padding:4px 10px;border-radius:20px;font-size:12.5px;}
  .cv-page.no-photo .cv-photo{display:none;}

  /* Classico — supporto colore accento opzionale */
  .cv-page.classic .cv-section h3{border-bottom-color:var(--accent-user, var(--ink));}

  /* Moderno */
  .cv-page.modern .cv-name{color:var(--accent-user, var(--accent-modern));}
  .cv-page.modern .cv-section h3{background:var(--accent-user, var(--accent-modern));color:#fff;padding:4px 12px;border-radius:5px;border-bottom:none;display:inline-block;}
  .cv-page.modern .skill-chip{background:#EAF0FC;color:var(--accent-user, var(--accent-modern));}

  /* Minimal — l'accento, se scelto, appare solo come sottile sottolineatura del nome */
  .cv-page.minimal .cv-name{font-weight:600;letter-spacing:-0.01em;border-bottom:2px solid var(--accent-user, transparent);padding-bottom:4px;display:inline-block;}
  .cv-page.minimal .cv-section h3{border:none;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:600;}
  .cv-page.minimal .skill-chip{background:transparent;border:1px solid var(--line);}

  /* Elegante */
  .cv-page.elegante{font-family:'Fraunces',serif;background:#FFFDF8;}
  .cv-page.elegante .cv-identity{text-align:center;}
  .cv-page.elegante .cv-name{font-size:32px;}
  .cv-page.elegante .cv-contact{text-align:center;}
  .cv-page.elegante .cv-section h3{border-bottom:1px solid var(--accent-user, #C9A24B);color:var(--accent-user, #8A6D2F);font-family:'Space Grotesk',sans-serif;text-align:center;}

  /* Compatto */
  .cv-page.compatto{font-size:12.5px;line-height:1.35;padding:38px 42px;border-left:6px solid var(--accent-user, var(--ink));}
  .cv-page.compatto .cv-name{font-size:22px;}
  .cv-page.compatto .cv-section{margin-top:14px;}
  .cv-page.compatto .cv-section h3{font-size:10.5px;margin-bottom:6px;padding:3px 8px;border-bottom:none;background:var(--paper-dim);display:inline-block;border-radius:3px;}
  .cv-page.compatto .cv-entry{margin-bottom:8px;}

  /* Creativo — sidebar layout, overrides the flex/order system with a grid */
  .cv-page.creativo{display:grid;grid-template-columns:190px 1fr;padding:0;grid-template-areas:"side main";}
  .cv-page.creativo .cv-sidebar{grid-area:side;background:var(--ink);color:#fff;padding:32px 20px;display:flex;flex-direction:column;gap:20px;}
  .cv-page.creativo .cv-main{grid-area:main;padding:32px 30px;display:flex;flex-direction:column;gap:20px;}
  .cv-page.creativo .cv-photo{order:0;border:3px solid var(--accent-user, var(--accent-creative));}
  .cv-page.creativo .cv-contact{order:0;color:#C9CCDA;font-size:12px;line-height:1.7;}
  .cv-page.creativo .sec-skills,.cv-page.creativo .sec-lang,.cv-page.creativo .sec-cert{order:0;margin-top:0;}
  .cv-page.creativo .cv-sidebar .cv-section h3{color:var(--accent-user, var(--accent-creative));border-bottom:1px solid rgba(255,255,255,.2);}
  .cv-page.creativo .cv-sidebar .skill-chip{background:rgba(255,255,255,.08);color:#fff;}
  .cv-page.creativo .cv-identity{order:0;}
  .cv-page.creativo .sec-summary{order:0;margin-top:0;}
  .cv-page.creativo .sec-exp{order:var(--order-exp, 4);margin-top:0;}
  .cv-page.creativo .sec-edu{order:var(--order-edu, 5);margin-top:0;}
  .cv-page.creativo .cv-main .cv-section h3{color:var(--ink);border-bottom-color:var(--accent-user, var(--accent-creative));}

  /* Tecnico — sidebar chiara + timeline a pallini + barre lingua */
  .cv-page.tecnico{display:grid;grid-template-columns:190px 1fr;padding:0;}
  .cv-page.tecnico .cv-sidebar{background:#EAF1F3;padding:30px 22px;display:flex;flex-direction:column;gap:20px;}
  .cv-page.tecnico .cv-main{padding:34px 34px 34px 30px;border-left:2px solid #DCE7E9;display:flex;flex-direction:column;gap:4px;}
  .cv-page.tecnico .cv-photo{order:0;width:96px;height:96px;margin:0 auto;border:3px solid #fff;box-shadow:0 0 0 2px #DCE7E9;}
  .cv-page.tecnico .cv-contact{order:0;font-size:12px;color:#3E5B60;line-height:2;}
  .cv-page.tecnico .cv-contact .contact-line{display:flex;gap:6px;align-items:center;}
  .cv-page.tecnico .cv-contact .contact-line::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--accent-user, var(--accent-tecnico));flex-shrink:0;}
  .cv-page.tecnico .sec-summary,.cv-page.tecnico .sec-skills,.cv-page.tecnico .sec-lang,.cv-page.tecnico .sec-cert{order:0;margin-top:0;}
  .cv-page.tecnico .cv-sidebar h3{color:var(--accent-user, var(--accent-tecnico));border-bottom:1px solid #D2E0E3;font-size:11.5px;}
  .cv-page.tecnico .cv-sidebar .skill-chip{background:#DCEAEC;color:#265E68;}
  .cv-page.tecnico .cv-identity{order:0;}
  .cv-page.tecnico .sec-exp{order:var(--order-exp, 4);margin-top:20px;position:relative;padding-left:20px;}
  .cv-page.tecnico .sec-edu{order:var(--order-edu, 5);margin-top:20px;position:relative;padding-left:20px;}
  .cv-page.tecnico .sec-exp::before,.cv-page.tecnico .sec-edu::before{
    content:"";position:absolute;left:-8px;top:2px;width:11px;height:11px;border-radius:50%;
    background:var(--accent-user, var(--accent-tecnico));border:2px solid #fff;box-shadow:0 0 0 2px #DCE7E9;
  }
  .cv-page.tecnico .cv-main h3{border:none;color:#204349;}
  .cv-page.tecnico .sec-lang .chips-preview{display:block;}
  .cv-page.tecnico .lang-row{margin-bottom:10px;}
  .cv-page.tecnico .lang-row .lang-label{display:flex;justify-content:space-between;gap:8px;font-size:12.5px;margin-bottom:3px;}

  /* Fascia foto — banner colorato full-width con foto tonda a cavallo del bordo */
  .cv-page.fascia{padding-top:170px;position:relative;}
  .cv-page.fascia::before{content:"";position:absolute;top:0;left:0;right:0;height:130px;background:var(--accent-user, var(--accent-fascia));}
  .cv-page.fascia .cv-photo{position:relative;z-index:1;margin:-96px auto 0;display:block;border:4px solid #fff;box-shadow:0 4px 14px rgba(0,0,0,.18);}
  .cv-page.fascia .cv-identity,.cv-page.fascia .cv-contact{position:relative;z-index:1;text-align:center;}
  .cv-page.fascia .cv-section h3{border-bottom-color:var(--accent-user, var(--accent-fascia));color:var(--accent-user, var(--accent-fascia));}
  .cv-page.fascia .skill-chip{background:color-mix(in srgb, var(--accent-user, var(--accent-fascia)) 12%, var(--paper-dim));}
  .cv-page.fascia.no-photo{padding-top:66px;}
  .cv-page.fascia.no-photo::before{height:66px;}

  /* Riflesso — stessa struttura del Tecnico (sidebar chiara + timeline) ma specchiata a destra */
  .cv-page.riflesso{display:grid;grid-template-columns:1fr 190px;grid-template-areas:"main side";padding:0;}
  .cv-page.riflesso .cv-sidebar{grid-area:side;background:#EFEDF7;padding:30px 22px;display:flex;flex-direction:column;gap:20px;}
  .cv-page.riflesso .cv-main{grid-area:main;padding:34px 30px 34px 34px;border-right:2px solid #DFDAF0;display:flex;flex-direction:column;gap:4px;}
  .cv-page.riflesso .cv-photo{order:0;width:96px;height:96px;margin:0 auto;border:3px solid #fff;box-shadow:0 0 0 2px #DFDAF0;}
  .cv-page.riflesso .cv-contact{order:0;font-size:12px;color:#4B4570;line-height:2;}
  .cv-page.riflesso .cv-contact .contact-line{display:flex;gap:6px;align-items:center;}
  .cv-page.riflesso .cv-contact .contact-line::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--accent-user, var(--accent-riflesso));flex-shrink:0;}
  .cv-page.riflesso .sec-summary,.cv-page.riflesso .sec-skills,.cv-page.riflesso .sec-lang,.cv-page.riflesso .sec-cert{order:0;margin-top:0;}
  .cv-page.riflesso .cv-sidebar h3{color:var(--accent-user, var(--accent-riflesso));border-bottom:1px solid #DFDAF0;font-size:11.5px;}
  .cv-page.riflesso .cv-sidebar .skill-chip{background:#E2DEF2;color:#463F73;}
  .cv-page.riflesso .cv-identity{order:0;}
  .cv-page.riflesso .sec-exp{order:var(--order-exp, 4);margin-top:20px;position:relative;padding-left:20px;}
  .cv-page.riflesso .sec-edu{order:var(--order-edu, 5);margin-top:20px;position:relative;padding-left:20px;}
  .cv-page.riflesso .sec-exp::before,.cv-page.riflesso .sec-edu::before{
    content:"";position:absolute;left:-8px;top:2px;width:11px;height:11px;border-radius:50%;
    background:var(--accent-user, var(--accent-riflesso));border:2px solid #fff;box-shadow:0 0 0 2px #DFDAF0;
  }
  .cv-page.riflesso .cv-main h3{border:none;color:#2E2A4D;}
  .cv-page.riflesso .sec-lang .chips-preview{display:block;}
  .cv-page.riflesso .lang-row{margin-bottom:10px;}
  .cv-page.riflesso .lang-row .lang-label{display:flex;justify-content:space-between;gap:8px;font-size:12.5px;margin-bottom:3px;}

  /* Timeline centrale — colonna singola, esperienze/istruzione con pallino e linea continua */
  .cv-page.timeline .cv-name{color:var(--accent-user, var(--accent-timeline));}
  .cv-page.timeline .sec-exp,.cv-page.timeline .sec-edu{position:relative;}
  .cv-page.timeline .sec-exp::before,.cv-page.timeline .sec-edu::before{
    content:"";position:absolute;left:5px;top:32px;bottom:2px;width:3px;background:var(--accent-user, var(--accent-timeline));opacity:.25;
  }
  .cv-page.timeline .sec-exp .cv-entry,.cv-page.timeline .sec-edu .cv-entry{position:relative;padding-left:26px;}
  .cv-page.timeline .sec-exp .cv-entry::before,.cv-page.timeline .sec-edu .cv-entry::before{
    content:"";position:absolute;left:-1px;top:3px;width:13px;height:13px;border-radius:50%;
    background:var(--accent-user, var(--accent-timeline));border:2.5px solid #fff;box-shadow:0 0 0 1.5px var(--accent-user, var(--accent-timeline));
  }
  .cv-page.timeline .cv-section h3{border-bottom-color:var(--accent-user, var(--accent-timeline));}

  /* ATS puro / essenziale — nessun colore, nessuna icona, massima leggibilità automatica */
  .cv-page.ats{color:#000;}
  .cv-page.ats .cv-role,.cv-page.ats .cv-contact,.cv-page.ats .cv-entry .sub{color:#444;}
  .cv-page.ats .cv-name{color:#000;}
  .cv-page.ats .cv-section h3{border-bottom-color:var(--accent-user, #000);color:#000;font-size:12px;letter-spacing:.03em;text-transform:uppercase;}
  .cv-page.ats .chips-preview{gap:4px;}
  .cv-page.ats .skill-chip{background:none;border:none;padding:0;border-radius:0;color:#000;}
  .cv-page.ats .skill-chip:not(:last-child)::after{content:" ·";color:#000;}

  /* Executive — serif istituzionale, doppia riga sotto il nome, doppio filetto nelle intestazioni */
  .cv-page.executive{font-family:'Fraunces',serif;background:#FDFCF9;}
  .cv-page.executive .cv-identity{border-bottom:5px double var(--accent-user, var(--ink));padding-bottom:12px;margin-bottom:4px;}
  .cv-page.executive .cv-name{font-size:25px;letter-spacing:.05em;text-transform:uppercase;}
  .cv-page.executive .cv-role{font-family:'Space Grotesk',sans-serif;text-transform:uppercase;letter-spacing:.14em;font-size:10.5px;margin-top:8px;}
  .cv-page.executive .cv-section h3{
    border-top:1px solid var(--accent-user, var(--ink));border-bottom:1px solid var(--accent-user, var(--ink));
    padding:5px 0;font-family:'Space Grotesk',sans-serif;letter-spacing:.06em;
  }

  /* Giovane/Junior — colonna singola, chip colorati, pallino accanto alle intestazioni */
  .cv-page.junior .cv-section h3{border:none;display:flex;align-items:center;gap:8px;color:var(--ink);font-size:13px;}
  .cv-page.junior .cv-section h3::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--accent-user, var(--accent-junior));flex-shrink:0;}
  .cv-page.junior .skill-chip{background:var(--accent-user, var(--accent-junior));color:#fff;border-radius:20px;}

  /* Accademico — colonna singola, serif, periodo sopra il titolo in maiuscoletto (convenzione da CV di ricerca) */
  .cv-page.accademico{font-family:'Fraunces',serif;}
  .cv-page.accademico .cv-name{font-size:26px;}
  .cv-page.accademico .cv-role{font-style:italic;}
  .cv-page.accademico .cv-entry .top{flex-direction:column;align-items:flex-start;gap:2px;}
  .cv-page.accademico .cv-entry .top span:last-child{order:-1;font-size:11px;letter-spacing:.05em;color:var(--muted);font-family:'Space Grotesk',sans-serif;text-transform:uppercase;}
  .cv-page.accademico .cv-entry .top span:first-child{font-size:15.5px;}
  .cv-page.accademico .cv-section h3{font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:11px;letter-spacing:.1em;text-transform:uppercase;border-bottom:1px solid var(--accent-user, var(--ink));}

  /* Consulenza — intestazione a blocco pieno (nome/ruolo in negativo), sezioni numerate, niente foto */
  .cv-page.consulenza{padding:0;}
  .cv-page.consulenza .cv-photo{display:none !important;}
  .cv-page.consulenza .cv-identity{background:var(--accent-user, var(--ink));color:#fff;padding:36px 48px;}
  .cv-page.consulenza .cv-name{color:#fff;}
  .cv-page.consulenza .cv-role{color:rgba(255,255,255,.75);}
  .cv-page.consulenza .cv-contact{padding:16px 48px 0;}
  .cv-page.consulenza .cv-section{padding:0 48px;counter-increment:consulenza-count;}
  .cv-page.consulenza{counter-reset:consulenza-count;}
  .cv-page.consulenza .cv-section:last-child{padding-bottom:40px;}
  .cv-page.consulenza .cv-section h3{border:none;font-family:'Space Grotesk',sans-serif;font-weight:700;}
  .cv-page.consulenza .cv-section h3::before{content:counter(consulenza-count, decimal-leading-zero) " — ";color:var(--accent-user, var(--ink));}

  /* Portfolio — nome molto grande, accento geometrico decorativo, pensato per chi ha un portfolio da mostrare */
  .cv-page.portfolio{position:relative;}
  .cv-page.portfolio::after{content:"";position:absolute;top:-16px;right:-16px;width:120px;height:120px;border-radius:50%;background:var(--accent-user, var(--accent-portfolio));opacity:.13;z-index:0;}
  .cv-page.portfolio .cv-identity,.cv-page.portfolio .cv-section{position:relative;z-index:1;}
  .cv-page.portfolio .cv-name{font-size:40px;letter-spacing:-0.02em;line-height:1.05;}
  .cv-page.portfolio .cv-role{font-size:15.5px;color:var(--accent-user, var(--accent-portfolio));font-weight:600;}
  .cv-page.portfolio .cv-section h3{font-size:19px;border:none;font-weight:700;letter-spacing:-0.01em;}
  .cv-page.portfolio .skill-chip{background:var(--accent-user, var(--accent-portfolio));color:#fff;font-weight:600;}

  /* Servizio — schede arrotondate per ogni esperienza, pallino colorato, per ruoli a contatto col pubblico */
  .cv-page.servizio .cv-entry{background:var(--paper-dim);border-radius:10px;padding:14px 16px;margin-bottom:12px;}
  .cv-page.servizio .cv-section h3{display:flex;align-items:center;gap:8px;border:none;}
  .cv-page.servizio .cv-section h3::before{content:"";width:10px;height:10px;border-radius:50%;background:var(--accent-user, var(--accent-servizio));flex-shrink:0;}
  .cv-page.servizio .skill-chip{background:var(--accent-user, var(--accent-servizio));color:#fff;border-radius:20px;}

  /* Sviluppo — intestazioni in monospaziato stile commento di codice, bordo laterale per voce, per sviluppatori */
  .cv-page.sviluppo .cv-section h3{font-family:'Courier New',Courier,monospace;font-size:13px;border:none;color:var(--accent-user, var(--accent-sviluppo));}
  .cv-page.sviluppo .cv-section h3::before{content:"// ";color:var(--muted);}
  .cv-page.sviluppo .cv-entry{border-left:3px solid var(--accent-user, var(--accent-sviluppo));padding-left:14px;margin-bottom:14px;}
  .cv-page.sviluppo .skill-chip{background:#1B1F3B;color:#7EE7C7;font-family:'Courier New',monospace;border-radius:4px;}

  /* Rivista — impaginazione editoriale, nome masthead, profilo in evidenza come citazione */
  .cv-page.rivista .cv-name{font-size:36px;text-transform:uppercase;letter-spacing:.01em;line-height:1.05;}
  .cv-page.rivista .cv-role{font-size:14px;text-transform:uppercase;letter-spacing:.14em;color:var(--muted);margin-top:8px;}
  .cv-page.rivista .cv-section.sec-summary{background:var(--paper-dim);border-left:4px solid var(--accent-user, var(--accent-rivista));padding:18px 22px;font-size:15px;font-style:italic;}
  .cv-page.rivista .cv-section h3{font-size:21px;font-weight:800;border:none;border-bottom:4px solid var(--accent-user, var(--accent-rivista));display:inline-block;padding-bottom:2px;}

  /* Formato Anglosassone one-page — layer aggiuntivo indipendente dal template, riusa la densità del Compatto */
  .cv-page.format-anglo .cv-photo{display:none !important;}
  .cv-page.format-anglo .cv-section{margin-top:14px;}
  .cv-page.format-anglo .cv-entry{margin-bottom:8px;}
  .cv-page.format-anglo{font-size:12.5px;line-height:1.35;}

  .watermark{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none;overflow:hidden;z-index:5;}
  .watermark span{font-family:'Space Grotesk',sans-serif;font-size:56px;font-weight:700;color:rgba(27,31,59,.09);transform:rotate(-28deg);white-space:nowrap;}

  /* ---------- MODALS / PRICING ---------- */
  .modal{position:fixed;inset:0;background:rgba(27,31,59,.55);display:none;align-items:center;justify-content:center;z-index:50;padding:20px;overflow-y:auto;}
  .modal.open{display:flex;}
  .modal-card{background:var(--white);border-radius:14px;padding:32px;max-width:460px;width:100%;max-height:92vh;overflow-y:auto;}
  .modal-card.pricing-card{max-width:660px;}
  .modal-card h3{font-size:20px;margin-bottom:8px;}
  .modal-card p{color:var(--muted);font-size:14px;margin-bottom:16px;}
  .modal-card .actions{display:flex;gap:10px;margin-top:18px;}

  .plan-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:18px 0 22px;}
  .plan-option{position:relative;border:1.5px solid var(--line);border-radius:12px;padding:22px 20px;cursor:pointer;background:var(--white);}
  .plan-option.selected{border-color:var(--ink);box-shadow:0 0 0 1px var(--ink) inset;}
  .plan-option.recommended{border-color:var(--accent-modern);}
  .plan-option.recommended.selected{box-shadow:0 0 0 1px var(--accent-modern) inset;}
  .plan-option .ribbon{position:absolute;top:-11px;left:18px;background:var(--accent-modern);color:#fff;font-size:11px;font-weight:600;padding:3px 11px;border-radius:20px;}
  .plan-name{font-weight:600;font-size:15px;}
  .price-big{font-family:'Space Grotesk',sans-serif;font-size:23px;font-weight:700;margin:10px 0 14px;}
  .price-big span{font-size:13px;font-weight:400;color:var(--muted);}
  .plan-features{list-style:none;font-size:13px;color:var(--muted);display:flex;flex-direction:column;gap:8px;}
  .plan-features li{padding-left:20px;position:relative;}
  .plan-features li::before{content:"✓";position:absolute;left:0;color:var(--success);font-weight:700;}

  .toast{
    position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(12px);
    background:var(--ink);color:var(--paper);padding:12px 20px;border-radius:8px;
    font-size:13.5px;box-shadow:0 12px 30px -10px rgba(0,0,0,.4);z-index:100;
    opacity:0;pointer-events:none;transition:opacity .2s ease, transform .2s ease;max-width:90vw;text-align:center;
  }
  .toast.visible{opacity:1;transform:translateX(-50%) translateY(0);}

  .cross-sell{background:var(--ink);color:var(--paper);border-radius:12px;padding:24px;margin-top:18px;}
  .cross-sell h4{font-family:'Space Grotesk',sans-serif;font-size:16px;margin-bottom:10px;}
  .cross-sell .plan-features{color:#C9CCDA;margin-bottom:16px;}
  .cross-sell .plan-features li::before{color:var(--highlight);}

  .code-toggle{margin:2px 0 16px;}
  .code-field{margin-bottom:6px;}

"""

SIDEBAR_SIDE = {'creativo': 'left', 'tecnico': 'left', 'riflesso': 'right'}
SIDEBAR_WIDTH_PX = 190  # stesso valore esatto usato in app.html per tutti e tre


def build_print_overrides(template, sidebar_width_px=None):
    """Regole di stampa aggiuntive: nessuna per i 16 template a colonna singola (il flusso
    normale si spezza già bene da solo), la sidebar ricorrente solo per i tre che ne hanno
    davvero bisogno. sidebar_width_px arriva dal client (l'utente può personalizzarla): se
    manca, usa lo stesso 190px di default del CSS originale."""
    base = """
        @page { size: A4; margin: 0; }
        body { margin: 0; }
        .cv-page {
            width: 100% !important; max-width: none !important; min-height: 0 !important;
            box-shadow: none !important;
        }
        .watermark { display: none !important; }
    """
    if template not in SIDEBAR_SIDE:
        return base

    width = sidebar_width_px if sidebar_width_px else SIDEBAR_WIDTH_PX
    width = max(120, min(320, width))  # stessi limiti ragionevoli dello slider in app.html
    side = SIDEBAR_SIDE[template]
    margin_side = 'left' if side == 'left' else 'right'
    page_margin = f"0 0 0 {width}px" if side == 'left' else f"0 {width}px 0 0"
    return base + f"""
        @page {{
            margin: {page_margin};
            @{margin_side}-top {{ content: element(sidebar); margin: 0; padding: 0; }}
        }}
        .cv-page.{template} {{ display: block !important; }}
        .cv-page.{template} .cv-sidebar {{
            position: running(sidebar) !important;
        }}
    """


def build_pdf_html(cv_page_html, template, sidebar_width_px=None):
    print_css = build_print_overrides(template, sidebar_width_px)
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
{GOOGLE_FONTS_IMPORT}
{REAL_CV_CSS}
{print_css}
</style></head>
<body>{cv_page_html}</body></html>"""


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json(force=True)
        cv_page_html = data.get('cvPageHTML', '')
        template = data.get('template', 'classic')
        sidebar_width_px = data.get('sidebarWidth')
        if not cv_page_html:
            return jsonify({'error': 'cvPageHTML mancante'}), 400
        html_string = build_pdf_html(cv_page_html, template, sidebar_width_px)
        pdf_bytes = HTML(string=html_string).write_pdf()
        filename = (data.get('name', 'CV').strip().replace(' ', '_') or 'CV') + '.pdf'
        return send_file(
            io.BytesIO(pdf_bytes), mimetype='application/pdf',
            as_attachment=True, download_name=filename,
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'cvelox-pdf-generator'})


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
