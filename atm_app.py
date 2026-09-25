#!/usr/bin/env python3
"""
ATM Kiosk Web App - Cosmos Bank (v3 - blue theme, card insert animation, HK flags)
Run one instance per city, each on its own port:
    python3 atm_app.py PUNE 8001
    python3 atm_app.py MUMBAI 8002
    python3 atm_app.py HONGKONG 8003

All text is plain ASCII on purpose (safe to copy-paste over a terminal).
"""

import socket
import json
import sys

from flask import Flask, request, jsonify, render_template_string

if len(sys.argv) != 3:
    print("Usage: python3 atm_app.py <ATM_NAME> <PORT>")
    sys.exit(1)

ATM_NAME = sys.argv[1]
PORT = int(sys.argv[2])
SHOW_FLAGS = (ATM_NAME.upper() == "HONGKONG")

ATM_SWITCH_IP = "10.24.0.5"
ATM_SWITCH_PORT = 5000

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Cosmos Bank ATM</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; user-select:none; }
  body {
    background: radial-gradient(circle at 50% 0%, #14335c, #030812 70%);
    color: white; font-family: 'Segoe UI', Arial, sans-serif;
    height: 100vh; display:flex; align-items:center; justify-content:center;
    overflow: hidden;
  }
  .atm-frame {
    background: #081426; border-radius: 22px; padding: 0;
    width: 560px; height: 660px; box-shadow: 0 25px 70px rgba(0,0,0,0.6);
    border: 2px solid #1d3d6d; display:flex; flex-direction:column; overflow:hidden;
  }
  .atm-topbar {
    background:#0a1a33; padding: 14px 24px; display:flex; align-items:center;
    justify-content:space-between; border-bottom:1px solid #1d3d6d;
  }
  .brand-group { display:flex; align-items:center; gap:10px; }
  .brand-mark { width:32px; height:32px; flex-shrink:0; }
  .atm-topbar .bank-name { font-size: 16px; font-weight:700; color:#c9974a; letter-spacing:0.5px; }
  .atm-topbar .city-name { font-size: 10.5px; color:#7fa0c8; text-transform:uppercase; letter-spacing:1px; }
  .atm-topbar .clock { font-size: 12px; color:#5a7aa8; }
  .flag-row { display:flex; gap:6px; padding: 8px 24px; background:#0a1a33; border-bottom:1px solid #1d3d6d; }
  .flag { width:26px; height:17px; border-radius:2px; position:relative; overflow:hidden; box-shadow:0 0 0 1px rgba(255,255,255,0.18); }
  .flag-india { background: linear-gradient(#ff9933 0 33%, #ffffff 33% 66%, #128807 66% 100%); }
  .flag-hk { background:#de2910; }
  .flag-hk .dot { position:absolute; left:50%; top:50%; width:8px; height:8px; background:#fff; border-radius:50%; transform:translate(-50%,-50%); }
  .flag-usa { background:#b22234; }
  .flag-usa .stripe { position:absolute; left:0; right:0; height:2px; background:#fff; }
  .flag-usa .canton { position:absolute; left:0; top:0; width:12px; height:9px; background:#3c3b6e; }
  .flag-uk { background:#00247d; position:relative; }
  .flag-uk .cross-v { position:absolute; left:45%; top:0; bottom:0; width:12%; background:#fff; }
  .flag-uk .cross-h { position:absolute; top:42%; left:0; right:0; height:16%; background:#fff; }
  .flag-uk .cross-vr { position:absolute; left:48%; top:0; bottom:0; width:4%; background:#c8102e; }
  .flag-uk .cross-hr { position:absolute; top:46%; left:0; right:0; height:8%; background:#c8102e; }
  .flag-sg { background:#fff; position:relative; }
  .flag-sg .top { position:absolute; top:0; left:0; right:0; height:50%; background:#ed2939; }

  .atm-body { flex:1; padding: 24px 26px; position:relative; }
  .screen { display:none; height:100%; flex-direction:column; opacity:0; }
  .screen.active { display:flex; animation: fadein 0.35s ease forwards; }
  @keyframes fadein { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }

  #screen-insert { flex-direction:row; gap:20px; height:100%; }
  .pin-panel, .card-panel { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:12px; }
  .panel-divider { width:1px; background:#1d3d6d; }
  .panel-title { font-size:12.5px; color:#7fa0c8; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px; }

  .masked-card { font-size:12.5px; color:#8fb0d0; letter-spacing:1.5px; text-align:center; min-height:16px; }
  .pin-dots { display:flex; gap:12px; margin: 6px 0 2px; }
  .pin-dots .dot { width:14px; height:14px; border-radius:50%; border:1.5px solid #3a6aa8; background:transparent; }
  .pin-dots .dot.filled { background:#c9974a; border-color:#c9974a; }
  .keypad { display:grid; grid-template-columns: repeat(3, 1fr); gap:9px; width:100%; margin-top:8px; transition: opacity 0.3s; }
  .keypad.disabled { opacity:0.35; pointer-events:none; }
  .keypad button {
    padding:13px 0; border-radius:9px; border:1px solid #1d3d6d; background:#0e2140;
    color:#fff; font-size:16px; font-weight:600; cursor:pointer;
  }
  .keypad button:hover { background:#1d3d6d; }
  .keypad button.wide { font-size:11.5px; color:#ff9a9a; }
  .pin-error { color:#ff8080; font-size:11.5px; min-height:14px; text-align:center; }
  .enter-btn { width:100%; margin-top:10px; padding:11px; border:none; border-radius:8px; background:#1a5fa8; color:#fff; font-size:13px; font-weight:600; cursor:pointer; transition:opacity 0.3s; }
  .enter-btn:disabled { opacity:0.35; cursor:not-allowed; }
  .enter-btn:not(:disabled):hover { background:#123f73; }

  .atm-slot-outer { width:190px; height:16px; background:#020509; border-radius:4px; box-shadow: inset 0 3px 6px rgba(0,0,0,0.7); position:relative; margin-bottom:56px; }
  .card-stage { position:relative; width:190px; height:110px; }
  .card-graphic {
    position:absolute; left:8px; top:20px; width:174px; height:104px; border-radius:9px;
    background: linear-gradient(135deg, #1a5fa8, #0a2a52); box-shadow:0 12px 24px rgba(0,0,0,0.45);
    padding:12px; display:flex; flex-direction:column; justify-content:space-between;
    transition: transform 0.9s cubic-bezier(.4,0,.2,1), opacity 0.4s ease 0.55s;
  }
  .card-graphic.inserted { transform: translateY(-150px); opacity:0; }
  .card-graphic .chip { width:26px; height:19px; background:#d9b568; border-radius:3px; }
  .card-graphic .num { font-size:12px; letter-spacing:2px; color:#dce8f7; }
  .card-graphic .cbrand { font-size:9.5px; color:#9fc0e8; text-transform:uppercase; letter-spacing:1px; }
  .card-input-row { display:flex; flex-direction:column; gap:10px; width:100%; align-items:center; }
  .card-input-row input { width:190px; padding:10px 12px; border-radius:8px; border:1px solid #1d3d6d; background:#0e2140; color:#fff; font-size:13px; text-align:center; letter-spacing:1.5px; }
  .card-input-row button { width:190px; padding:11px; border:none; border-radius:8px; background:#1a5fa8; color:#fff; font-size:13.5px; font-weight:600; cursor:pointer; }
  .card-input-row button:hover { background:#123f73; }
  .card-hint { font-size:11px; color:#5a7aa8; text-align:center; max-width:190px; }

  #screen-menu { justify-content:flex-start; gap:12px; }
  #screen-menu .menu-title { font-size:14px; color:#8fb0d0; margin-bottom:4px; }
  .menu-grid { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
  .menu-tile {
    background:#0e2140; border:1px solid #1d3d6d; border-radius:12px; padding:18px 12px;
    text-align:center; cursor:pointer; display:flex; flex-direction:column; align-items:center; gap:6px;
  }
  .menu-tile:hover { background:#1d3d6d; border-color:#c9974a; }
  .menu-tile .icon { font-size:13px; font-weight:700; color:#c9974a; letter-spacing:0.5px; }
  .menu-tile .label { font-size:12.5px; color:#eaf1fa; }
  .exit-tile { grid-column: span 2; background:transparent; border-style:dashed; }
  .exit-tile .label { color:#ff9a9a; }

  .screen-header { font-size:15px; color:#eaf1fa; margin-bottom:16px; }
  .quick-amounts { display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:14px; }
  .quick-amounts button { padding:13px; border-radius:8px; border:1px solid #1d3d6d; background:#0e2140; color:#fff; font-size:13.5px; cursor:pointer; }
  .quick-amounts button:hover { background:#1d3d6d; }
  .amount-input { padding:11px 13px; border-radius:8px; border:1px solid #1d3d6d; background:#0e2140; color:#fff; font-size:14px; margin-bottom:14px; }
  .btn-row { display:flex; gap:10px; margin-top:auto; }
  .btn-row button { flex:1; padding:12px; border-radius:8px; border:none; font-size:13.5px; font-weight:600; cursor:pointer; }
  .btn-confirm { background:#1a5fa8; color:#fff; }
  .btn-confirm:hover { background:#123f73; }
  .btn-back { background:#12233e; color:#b9cbe3; }

  #screen-processing { align-items:center; justify-content:center; gap:16px; }
  .spinner { width:42px; height:42px; border:4px solid #1d3d6d; border-top-color:#c9974a; border-radius:50%; animation:spin 0.9s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  #screen-result { align-items:center; justify-content:center; text-align:center; gap:12px; }
  .result-icon { width:52px; height:52px; }
  .result-message { font-size:14.5px; }
  .result-message.approved { color:#5fe0a8; }
  .result-message.declined { color:#ff8080; }
  .result-balance { font-size:12.5px; color:#8fb0d0; }

  .balance-amount { font-size:30px; font-weight:700; color:#c9974a; margin: 18px 0; text-align:center; }
  .stmt-list { display:flex; flex-direction:column; gap:10px; }
  .stmt-entry { background:#0e2140; border:1px solid #1d3d6d; border-radius:10px; padding:12px 14px; font-size:11.5px; }
  .stmt-entry .stmt-row { display:flex; justify-content:space-between; padding:3px 0; border-bottom:1px solid #16294a; }
  .stmt-entry .stmt-row:last-child { border-bottom:none; }
  .stmt-entry .stmt-label { color:#7fa0c8; }
  .stmt-entry .stmt-value { color:#eaf1fa; font-weight:600; text-align:right; }
  .stmt-value.credit { color:#5fe0a8; }
  .stmt-value.debit { color:#ff9a9a; }
  .badge-approved { color:#5fe0a8; } .badge-declined { color:#ff8080; }
</style>
</head>
<body oncontextmenu="return false">
  <div class="atm-frame">
    <div class="atm-topbar">
      <div class="brand-group">
        <svg class="brand-mark" viewBox="0 0 46 46">
          <circle cx="23" cy="23" r="21" fill="none" stroke="#1a5fa8" stroke-width="2.5"/>
          <path d="M23 6 A17 17 0 0 1 40 23" fill="none" stroke="#c9974a" stroke-width="3.5" stroke-linecap="round"/>
          <circle cx="23" cy="23" r="8" fill="#1a5fa8"/>
          <path d="M19 23 L22 26 L28 19" stroke="#eaf1fa" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div>
          <div class="bank-name">COSMOS BANK</div>
          <div class="city-name">{{ atm_name }} ATM {{ '- INTERNATIONAL' if show_flags else '' }}</div>
        </div>
      </div>
      <div class="clock" id="clock"></div>
    </div>

    {% if show_flags %}
    <div class="flag-row">
      <div class="flag flag-india"></div>
      <div class="flag flag-hk"><div class="dot"></div></div>
      <div class="flag flag-usa">
        <div class="canton"></div>
        <div class="stripe" style="top:14%"></div><div class="stripe" style="top:28%"></div>
        <div class="stripe" style="top:42%"></div><div class="stripe" style="top:56%"></div>
        <div class="stripe" style="top:70%"></div><div class="stripe" style="top:84%"></div>
      </div>
      <div class="flag flag-uk">
        <div class="cross-h"></div><div class="cross-v"></div>
        <div class="cross-hr"></div><div class="cross-vr"></div>
      </div>
      <div class="flag flag-sg"><div class="top"></div></div>
    </div>
    {% endif %}

    <div class="atm-body">

      <div class="screen active" id="screen-insert">
        <div class="pin-panel">
          <div class="panel-title">Enter PIN</div>
          <div class="masked-card" id="pin-card-label">Insert your card to begin</div>
          <div class="pin-dots" id="pin-dots">
            <div class="dot"></div><div class="dot"></div><div class="dot"></div><div class="dot"></div>
          </div>
          <div class="pin-error" id="pin-error"></div>
          <div class="keypad disabled" id="keypad">
            <button onclick="keyPress('1')">1</button><button onclick="keyPress('2')">2</button><button onclick="keyPress('3')">3</button>
            <button onclick="keyPress('4')">4</button><button onclick="keyPress('5')">5</button><button onclick="keyPress('6')">6</button>
            <button onclick="keyPress('7')">7</button><button onclick="keyPress('8')">8</button><button onclick="keyPress('9')">9</button>
            <button class="wide" onclick="cancelToIdle()">CANCEL</button><button onclick="keyPress('0')">0</button><button class="wide" onclick="keyClear()">CLEAR</button>
          </div>
          <button class="enter-btn" id="enter-btn" onclick="verifyPin()" disabled>ENTER</button>
        </div>

        <div class="panel-divider"></div>

        <div class="card-panel">
          <div class="panel-title">Card Slot</div>
          <div class="atm-slot-outer"></div>
          <div class="card-stage">
            <div class="card-graphic" id="card-graphic">
              <div class="chip"></div>
              <div class="num" id="card-graphic-num">**** **** **** ****</div>
              <div class="cbrand">COSMOS BANK</div>
            </div>
          </div>
          <div class="card-input-row" id="card-input-row">
            <input id="idle-card" maxlength="16" placeholder="Card Number">
            <button onclick="insertCard()">Insert Card</button>
            <div class="card-hint">Type your card number, then press Insert Card to feed it into the slot.</div>
          </div>
        </div>
      </div>

      <div class="screen" id="screen-menu">
        <div class="menu-title">Please select a transaction</div>
        <div class="menu-grid">
          <div class="menu-tile" onclick="showScreen('screen-withdraw')"><div class="icon">CASH</div><div class="label">Withdraw Cash</div></div>
          <div class="menu-tile" onclick="showScreen('screen-deposit')"><div class="icon">DEPOSIT</div><div class="label">Deposit Cash</div></div>
          <div class="menu-tile" onclick="doBalance()"><div class="icon">BAL</div><div class="label">Balance Inquiry</div></div>
          <div class="menu-tile" onclick="doMiniStatement()"><div class="icon">STMT</div><div class="label">Mini Statement</div></div>
          <div class="menu-tile exit-tile" onclick="takeCard()"><div class="label">Exit / Take Card</div></div>
        </div>
      </div>

      <div class="screen" id="screen-withdraw">
        <div class="screen-header">Withdraw Cash</div>
        <div class="quick-amounts">
          <button onclick="withdrawAmount(500)">Rs. 500</button>
          <button onclick="withdrawAmount(1000)">Rs. 1,000</button>
          <button onclick="withdrawAmount(2000)">Rs. 2,000</button>
          <button onclick="withdrawAmount(5000)">Rs. 5,000</button>
        </div>
        <input class="amount-input" id="withdraw-other" placeholder="Other amount">
        <div class="btn-row">
          <button class="btn-back" onclick="showScreen('screen-menu')">Back</button>
          <button class="btn-confirm" onclick="withdrawAmount(null)">Confirm</button>
        </div>
      </div>

      <div class="screen" id="screen-deposit">
        <div class="screen-header">Deposit Cash</div>
        <input class="amount-input" id="deposit-amount" placeholder="Enter amount to deposit">
        <div class="btn-row">
          <button class="btn-back" onclick="showScreen('screen-menu')">Back</button>
          <button class="btn-confirm" onclick="depositAmount()">Confirm</button>
        </div>
      </div>

      <div class="screen" id="screen-processing">
        <div class="spinner"></div>
        <div>Processing your request...</div>
      </div>

      <div class="screen" id="screen-result">
        <svg class="result-icon" id="result-icon-ok" viewBox="0 0 52 52" style="display:none;">
          <circle cx="26" cy="26" r="24" fill="none" stroke="#5fe0a8" stroke-width="3"/>
          <path d="M15 27 L22 34 L37 18" fill="none" stroke="#5fe0a8" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <svg class="result-icon" id="result-icon-x" viewBox="0 0 52 52" style="display:none;">
          <circle cx="26" cy="26" r="24" fill="none" stroke="#ff8080" stroke-width="3"/>
          <path d="M18 18 L34 34 M34 18 L18 34" stroke="#ff8080" stroke-width="3.5" stroke-linecap="round"/>
        </svg>
        <div class="result-message" id="result-message"></div>
        <div class="result-balance" id="result-balance"></div>
        <div class="btn-row" style="width:100%; margin-top:16px;">
          <button class="btn-back" onclick="showScreen('screen-menu')">Another Transaction</button>
          <button class="btn-confirm" onclick="takeCard()">Take Card</button>
        </div>
      </div>

      <div class="screen" id="screen-balance">
        <div class="screen-header">Balance Inquiry</div>
        <div class="balance-amount" id="balance-value"></div>
        <div class="btn-row" style="margin-top:auto;">
          <button class="btn-back" onclick="showScreen('screen-menu')">Back to Menu</button>
          <button class="btn-confirm" onclick="takeCard()">Take Card</button>
        </div>
      </div>

      <div class="screen" id="screen-ministatement">
        <div class="screen-header">Mini Statement (last 5)</div>
        <div style="flex:1; overflow-y:auto;">
          <div class="stmt-list" id="mini-stmt-list"></div>
        </div>
        <div class="btn-row">
          <button class="btn-back" onclick="showScreen('screen-menu')">Back to Menu</button>
          <button class="btn-confirm" onclick="takeCard()">Take Card</button>
        </div>
      </div>

      <div class="screen" id="screen-takecard">
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:12px;">
          <svg width="52" height="52" viewBox="0 0 52 52">
            <circle cx="26" cy="26" r="24" fill="none" stroke="#5fe0a8" stroke-width="3"/>
            <path d="M15 27 L22 34 L37 18" fill="none" stroke="#5fe0a8" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <div>Thank you. Please take your card.</div>
        </div>
      </div>

    </div>
  </div>

<script>
let session = { card: "", pin: "" };
let pinAttempts = 0;

document.addEventListener('keydown', e => {
  if (e.key === 'F11' || e.key === 'F12' || e.altKey || (e.ctrlKey && e.shiftKey)) e.preventDefault();
});

function tick() { document.getElementById('clock').innerText = new Date().toLocaleTimeString(); }
setInterval(tick, 1000); tick();

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function insertCard() {
  const card = document.getElementById('idle-card').value.trim();
  if (!card) return;
  session.card = card;
  session.pin = "";
  pinAttempts = 0;

  document.getElementById('card-graphic-num').innerText = '**** **** **** ' + card.slice(-4);
  document.getElementById('card-graphic').classList.add('inserted');
  document.getElementById('card-input-row').style.visibility = 'hidden';

  document.getElementById('pin-card-label').innerText = 'Card: **** **** **** ' + card.slice(-4);
  document.getElementById('pin-error').innerText = '';
  updatePinDots();

  setTimeout(() => {
    document.getElementById('keypad').classList.remove('disabled');
    document.getElementById('enter-btn').disabled = false;
  }, 900);
}

function updatePinDots() {
  const dots = document.querySelectorAll('#pin-dots .dot');
  dots.forEach((d, i) => d.classList.toggle('filled', i < session.pin.length));
}

function keyPress(digit) {
  if (!session.card || session.pin.length >= 4) return;
  session.pin += digit;
  updatePinDots();
  if (session.pin.length === 4) verifyPin();
}

function keyClear() {
  session.pin = "";
  document.getElementById('pin-error').innerText = '';
  updatePinDots();
}

function cancelToIdle() {
  session = { card: "", pin: "" };
  document.getElementById('idle-card').value = '';
  document.getElementById('card-graphic').classList.remove('inserted');
  document.getElementById('card-input-row').style.visibility = 'visible';
  document.getElementById('pin-card-label').innerText = 'Insert your card to begin';
  document.getElementById('keypad').classList.add('disabled');
  document.getElementById('enter-btn').disabled = true;
  document.getElementById('pin-error').innerText = '';
  updatePinDots();
  showScreen('screen-insert');
}

function callSwitch(action, amount) {
  return fetch('/api/action', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ action, card: session.card, pin: session.pin, amount: amount || 0 })
  }).then(r => r.json());
}

function verifyPin() {
  if (session.pin.length !== 4) {
    document.getElementById('pin-error').innerText = 'Please enter a 4-digit PIN.';
    return;
  }
  callSwitch('verify_pin').then(data => {
    if (data.status === 'APPROVED') {
      showScreen('screen-menu');
    } else {
      pinAttempts++;
      document.getElementById('pin-error').innerText = data.reason + (pinAttempts < 3 ? ' - try again' : '');
      session.pin = "";
      updatePinDots();
      if (pinAttempts >= 3) {
        document.getElementById('pin-error').innerText = 'Too many attempts. Card retained.';
        setTimeout(cancelToIdle, 2000);
      }
    }
  }).catch(() => {
    document.getElementById('pin-error').innerText = 'Switch unavailable.';
    session.pin = ""; updatePinDots();
  });
}

function withdrawAmount(preset) {
  const amount = preset !== null ? preset : parseFloat(document.getElementById('withdraw-other').value);
  if (!amount || amount <= 0) return;
  showScreen('screen-processing');
  callSwitch('withdraw', amount).then(data => renderResult(data)).catch(() => renderResult({status:'ERROR', reason:'Could not reach switch'}));
}

function depositAmount() {
  const amount = parseFloat(document.getElementById('deposit-amount').value);
  if (!amount || amount <= 0) return;
  showScreen('screen-processing');
  callSwitch('deposit', amount).then(data => renderResult(data)).catch(() => renderResult({status:'ERROR', reason:'Could not reach switch'}));
}

function renderResult(data) {
  const approved = data.status === 'APPROVED';
  document.getElementById('result-icon-ok').style.display = approved ? 'block' : 'none';
  document.getElementById('result-icon-x').style.display = approved ? 'none' : 'block';
  const msg = document.getElementById('result-message');
  msg.className = 'result-message ' + (approved ? 'approved' : 'declined');
  msg.innerText = (approved ? 'Approved - ' : 'Declined - ') + data.reason;
  document.getElementById('result-balance').innerText = (data.balance !== undefined) ? ('New balance: Rs. ' + data.balance.toFixed(2)) : '';
  showScreen('screen-result');
}

function doBalance() {
  showScreen('screen-processing');
  callSwitch('balance').then(data => {
    if (data.status === 'APPROVED') {
      document.getElementById('balance-value').innerText = 'Rs. ' + data.balance.toFixed(2);
      showScreen('screen-balance');
    } else {
      renderResult(data);
    }
  });
}

function doMiniStatement() {
  showScreen('screen-processing');
  callSwitch('ministatement').then(data => {
    if (data.status === 'APPROVED') {
      const maskedCard = '**** **** **** ' + session.card.slice(-4);
      let html = '';
      if (!data.transactions || data.transactions.length === 0) {
        html = '<div class="stmt-entry">No transactions found for this card.</div>';
      }
      data.transactions.forEach(t => {
        const indClass = t.indicator === 'Credit' ? 'credit' : 'debit';
        const indSign = t.indicator === 'Credit' ? '+' : '-';
        const balText = (t.balance_after !== null && t.balance_after !== undefined)
          ? 'Rs. ' + t.balance_after.toFixed(2) : 'N/A';
        html += '<div class="stmt-entry">'
          + '<div class="stmt-row"><span class="stmt-label">ATM Info</span><span class="stmt-value">' + t.atm_id + '</span></div>'
          + '<div class="stmt-row"><span class="stmt-label">Date &amp; Time</span><span class="stmt-value">' + t.created_at + '</span></div>'
          + '<div class="stmt-row"><span class="stmt-label">Card Number</span><span class="stmt-value">' + maskedCard + '</span></div>'
          + '<div class="stmt-row"><span class="stmt-label">Transaction Type</span><span class="stmt-value">' + t.txn_type + '</span></div>'
          + '<div class="stmt-row"><span class="stmt-label">Transaction Date</span><span class="stmt-value">' + t.created_at.split(' ')[0] + '</span></div>'
          + '<div class="stmt-row"><span class="stmt-label">Transaction Amount</span><span class="stmt-value">Rs. ' + t.amount.toFixed(2) + '</span></div>'
          + '<div class="stmt-row"><span class="stmt-label">Credit/Debit</span><span class="stmt-value ' + indClass + '">' + indSign + ' ' + t.indicator + '</span></div>'
          + '<div class="stmt-row"><span class="stmt-label">Status</span><span class="stmt-value badge-' + t.status + '">' + t.status + '</span></div>'
          + '<div class="stmt-row"><span class="stmt-label">Available Balance</span><span class="stmt-value">' + balText + '</span></div>'
          + '</div>';
      });
      document.getElementById('mini-stmt-list').innerHTML = html;
      showScreen('screen-ministatement');
    } else {
      renderResult(data);
    }
  });
}

function takeCard() {
  showScreen('screen-takecard');
  setTimeout(() => {
    session = { card: "", pin: "" };
    document.getElementById('idle-card').value = '';
    document.getElementById('card-graphic').classList.remove('inserted');
    document.getElementById('card-input-row').style.visibility = 'visible';
    document.getElementById('pin-card-label').innerText = 'Insert your card to begin';
    document.getElementById('keypad').classList.add('disabled');
    document.getElementById('enter-btn').disabled = true;
    updatePinDots();
    showScreen('screen-insert');
  }, 2500);
}
</script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML_PAGE, atm_name=ATM_NAME, show_flags=SHOW_FLAGS)


@app.route("/api/action", methods=["POST"])
def api_action():
    data = request.json
    payload = {
        "atm_id": ATM_NAME,
        "action": data.get("action", "withdraw"),
        "card": data["card"],
        "pin": data["pin"],
        "amount": data.get("amount", 0)
    }
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ATM_SWITCH_IP, ATM_SWITCH_PORT))
        s.send(json.dumps(payload).encode())
        response = json.loads(s.recv(4096).decode())
        s.close()
        return jsonify(response)
    except Exception as e:
        return jsonify({"status": "ERROR", "reason": str(e)})


if __name__ == "__main__":
    print(f"[{ATM_NAME} ATM] Serving on port {PORT}, forwarding to switch at {ATM_SWITCH_IP}:{ATM_SWITCH_PORT}")
    app.run(host="0.0.0.0", port=PORT)
