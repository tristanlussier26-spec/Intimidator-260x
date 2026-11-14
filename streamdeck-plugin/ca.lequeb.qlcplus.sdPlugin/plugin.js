// Plugin Stream Deck « QLC+ Show » — contrôle les boutons du Virtual Console de QLC+
// par son interface web (qlcplus -w), sans raccourcis clavier : QLC+ n'a pas besoin d'être en avant-plan.
//
// Protocole QLC+ (ws://HOTE:9999/qlcplusWS) :
//   "<id>|255"  -> appui du bouton     "<id>|0" -> relâchement (utile pour les boutons Flash)
//   "QLC+API|getWidgetsList"            -> "QLC+API|getWidgetsList|id|nom|id|nom..."
//   "QLC+API|getWidgetStatus|<id>"      -> "QLC+API|getWidgetStatus|<id>|255/127/0"
//   QLC+ pousse "<id>|BUTTON|255/127/0" à chaque changement d'état d'un bouton.
'use strict';
const WebSocket = require('./node_modules/ws');
const http = require('http');

const args = {};
for (let i = 2; i < process.argv.length - 1; i++) {
  if (process.argv[i].startsWith('-')) args[process.argv[i].replace(/^-+/, '')] = process.argv[i + 1];
}

const PLUGIN = args.pluginUUID;
const contexts = new Map();       // context Stream Deck -> { widgetId, state }
const LEVEL = 'ca.lequeb.qlcplus.level';   // action « Niveau » : fader / bouton rotatif de QLC+
const status = new Map();         // id widget -> 255 / 127 / 0
let widgets = [];                 // [{id, name}]
let host = '127.0.0.1:9999';
let qlc = null;
let qlcOk = false;
let retry = null;
let pageLoaded = false;           // la page web de QLC+ (qui branche le retour d'état) déjà chargée ?

// ------------------------------------------------------------------ Stream Deck
const sd = new WebSocket(`ws://127.0.0.1:${args.port}`);
const sdSend = (o) => { if (sd.readyState === WebSocket.OPEN) sd.send(JSON.stringify(o)); };
const log = (msg) => sdSend({ event: 'logMessage', payload: { message: `[QLC+] ${msg}` } });

sd.on('open', () => {
  sdSend({ event: args.registerEvent, uuid: PLUGIN });
  sdSend({ event: 'getGlobalSettings', context: PLUGIN });
  connectQlc();
});
sd.on('close', () => process.exit(0));

sd.on('message', (raw) => {
  let m;
  try { m = JSON.parse(raw); } catch { return; }
  const ctx = m.context;
  const settings = (m.payload && m.payload.settings) || {};
  switch (m.event) {
    case 'willAppear':
    case 'didReceiveSettings':
      contexts.set(ctx, { widgetId: String(settings.widgetId || ''), hold: settings.mode === 'hold',
                          state: -1, held: false, level: m.action === LEVEL,
                          step: parseInt(settings.step, 10) || 0, label: settings.label || '' });
      refresh(ctx);
      break;
    case 'willDisappear':
      stopRepeat(ctx);
      contexts.delete(ctx);
      break;
    case 'keyDown':
      keyDown(ctx);
      break;
    case 'keyUp':
      keyUp(ctx);
      break;
    case 'didReceiveGlobalSettings':
      if (settings.host && settings.host !== host) { host = settings.host; reconnect(); }
      break;
    case 'propertyInspectorDidAppear':
    case 'sendToPlugin':
      sendList(ctx, m.action);
      if (m.payload && m.payload.cmd === 'reload') qlcSend('QLC+API|getWidgetsList');
      break;
  }
});

// Mode « appui » : comme un clic sur le bouton du board (toggle = on/off, flash = tant que tenu).
// Mode « maintenu » : allumé tant que la touche est tenue, même sur un bouton toggle :
//   appui -> on ; relâchement -> on rappuie pour éteindre (si c'est nous qui l'avons allumé).
function keyDown(ctx) {
  const c = contexts.get(ctx);
  if (c && c.level) return levelDown(ctx);
  if (c && c.hold) c.held = (status.get(c.widgetId) || 0) === 0;
  press(ctx, 255);
}

function keyUp(ctx) {
  const c = contexts.get(ctx);
  if (c && c.level) return stopRepeat(ctx);
  press(ctx, 0);
  if (c && c.hold && c.held) { c.held = false; press(ctx, 255); }
  setTimeout(() => refresh(ctx), 150);   // resynchronise le cadre avec l'état réel de QLC+
}

function press(ctx, value) {
  const c = contexts.get(ctx);
  if (!c || !c.widgetId) { if (value) sdSend({ event: 'showAlert', context: ctx }); return; }
  if (!qlcOk) { if (value) sdSend({ event: 'showAlert', context: ctx }); return; }
  qlcSend(`${c.widgetId}|${value}`);
}

// ------------------------------------------------------------------ Niveau (faders)
// step > 0 : monte de step %, step < 0 : descend, step = 0 : affiche seulement (appui = 0 %).
// Tenir la touche répète. QLC+ applique lui-même la limite haute du fader (ex. 70 % des lekos).
const repeats = new Map();
function levelDown(ctx) {
  const c = contexts.get(ctx);
  if (!c.widgetId || !qlcOk) { sdSend({ event: 'showAlert', context: ctx }); return; }
  const stepOnce = () => {
    const cur = status.get(c.widgetId) || 0;
    const next = c.step === 0 ? 0 : Math.max(0, Math.min(255, Math.round(cur + c.step * 2.55)));
    status.set(c.widgetId, next);           // estimation immédiate, corrigée par le retour de QLC+
    qlcSend(`${c.widgetId}|${next}`);
  };
  stepOnce();
  if (c.step !== 0) {
    const t = setTimeout(() => repeats.set(ctx, setInterval(stepOnce, 120)), 400);
    repeats.set(ctx, t);
  }
}
function stopRepeat(ctx) {
  const t = repeats.get(ctx);
  if (t) { clearTimeout(t); clearInterval(t); repeats.delete(ctx); }
  const c = contexts.get(ctx);
  if (c && c.widgetId) setTimeout(() => qlcSend(`QLC+API|getWidgetStatus|${c.widgetId}`), 150);
}
function showLevel(ctx) {
  const c = contexts.get(ctx);
  const pct = Math.round((status.get(c.widgetId) || 0) / 2.55);
  const sign = c.step > 0 ? '+' : c.step < 0 ? '−' : '';
  const title = `${c.label}${sign ? ' ' + sign : ''}\n${pct} %`;
  if (title !== c.title) { c.title = title; sdSend({ event: 'setTitle', context: ctx, payload: { title } }); }
}

function setKeyState(ctx, force) {
  const c = contexts.get(ctx);
  if (!c) return;
  if (c.level) return showLevel(ctx);
  const v = status.get(c.widgetId) || 0;
  const st = v === 255 ? 1 : 0;          // cadre seulement si le bouton est vraiment actif (pas « surveillé »)
  if (st !== c.state || force) {
    c.state = st;
    sdSend({ event: 'setState', context: ctx, payload: { state: st } });
  }
}

function refresh(ctx) {
  const c = contexts.get(ctx);
  if (!c || !c.widgetId) return;
  setKeyState(ctx, true);
  qlcSend(`QLC+API|getWidgetStatus|${c.widgetId}`);
}

function sendList(ctx, action) {
  sdSend({ event: 'sendToPropertyInspector', context: ctx, action,
           payload: { widgets, connected: qlcOk, host } });
}

// ------------------------------------------------------------------ QLC+
function qlcSend(s) { if (qlcOk) qlc.send(s); }

function connectQlc() {
  clearTimeout(retry);
  // QLC+ envoie parfois des trames mal encodées quand plusieurs choses changent en même temps :
  // on ne valide pas l'UTF-8 (sinon la connexion coupe à chaque fois).
  const ws = new WebSocket(`ws://${host}/qlcplusWS`, { handshakeTimeout: 3000, skipUTF8Validation: true });
  let opened = false;
  qlc = ws;
  ws.on('open', () => {
    if (ws !== qlc) return;
    opened = true;
    qlcOk = true;
    log(`connecté à ${host}`);
    qlcSend('QLC+API|getWidgetsList');
    // QLC+ ne branche le retour d'état des boutons qu'une fois sa page web générée : on la charge,
    // UNE seule fois par démarrage de QLC+ (chaque chargement double les messages de retour).
    if (!pageLoaded) {
      pageLoaded = true;
      http.get(`http://${host}/`, (res) => { res.resume(); res.on('end', () => {
        for (const ctx of contexts.keys()) refresh(ctx);
      }); }).on('error', () => { pageLoaded = false; });
    }
    for (const ctx of contexts.keys()) refresh(ctx);
  });
  ws.on('message', (data) => {
    if (ws !== qlc) return;
    onQlc(Buffer.from(data).toString('latin1'));
  });
  const down = () => {
    if (ws !== qlc) return;
    if (qlcOk) log('déconnecté — nouvel essai…');
    qlcOk = false;
    // jamais connecté = QLC+ fermé ou relancé : il faudra recharger sa page au retour
    if (!opened) pageLoaded = false;
    // coupure sur une trame abîmée (QLC+ toujours là) : on revient tout de suite, sans éteindre les touches
    retry = setTimeout(connectQlc, opened ? 300 : 2000);
    if (!opened) { status.clear(); for (const ctx of contexts.keys()) setKeyState(ctx); }
  };
  ws.on('close', down);
  ws.on('error', () => { try { ws.terminate(); } catch {} });
}

function reconnect() {
  const old = qlc;
  qlc = null;
  qlcOk = false;
  if (old) try { old.terminate(); } catch {}
  connectQlc();
}

function onQlc(msg) {
  const p = msg.split('|');
  if (p[0] === 'QLC+API') {
    if (p[1] === 'getWidgetsList') {
      widgets = [];
      for (let i = 2; i + 1 < p.length; i += 2) widgets.push({ id: p[i], name: p[i + 1] });
    } else if (p[1] === 'getWidgetStatus' && p.length >= 4) {
      updateStatus(p[2], parseInt(p[3], 10) || 0);
    }
    return;
  }
  if ((p[1] === 'BUTTON' || p[1] === 'SLIDER') && p.length >= 3) updateStatus(p[0], parseInt(p[2], 10) || 0);
}

function updateStatus(id, v) {
  status.set(id, v);
  for (const [ctx, c] of contexts) if (c.widgetId === id) setKeyState(ctx);
}

// Les connexions QLC+ inactives restent ouvertes, mais on vérifie quand même régulièrement.
setInterval(() => { if (qlcOk && qlc) try { qlc.ping(); } catch {} }, 10000);
