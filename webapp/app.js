"use strict";
/* PWA AI Financial Assistant — memanggil backend; tidak menghitung ulang finansial. */

// ---- util ---------------------------------------------------------- //
const $ = (id) => document.getElementById(id);
const rp = (n) => "Rp" + Math.abs(n || 0).toLocaleString("id-ID");
const esc = (s) => (s == null ? "" : String(s).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])));
const TYPE_LABEL = { income: "Pemasukan", expense: "Pengeluaran", transfer: "Transfer", refund: "Refund" };

function getToken() { try { return localStorage.getItem("ck_token") || ""; } catch (_) { return ""; } }
function setToken(t) { try { localStorage.setItem("ck_token", t); } catch (_) {} }
function clearToken() { try { localStorage.removeItem("ck_token"); } catch (_) {} }
async function api(method, path, body) {
  const opt = { method, headers: {} };
  const tok = getToken(); if (tok) opt.headers["X-Token"] = tok;
  if (body !== undefined) { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
  const res = await fetch(path, opt);
  const data = await res.json().catch(() => ({}));
  if (res.status === 401) { clearToken(); showAuth("login"); throw new Error("Sesi berakhir, silakan masuk"); }
  if (!res.ok) throw new Error(data.error || "Terjadi kesalahan");
  return data;
}

const MIC_SVG = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2"><path d="M12 2a3 3 0 013 3v6a3 3 0 01-6 0V5a3 3 0 013-3z"/><path d="M19 10a7 7 0 01-14 0"/><path d="M12 19v3"/></svg>';
function showAuth(mode) {
  VIEW = "__auth";
  $("topbar").innerHTML = ""; $("nav").innerHTML = ""; $("fab").hidden = true;
  const login = mode !== "register";
  $("view").innerHTML = `<div class="auth">
    <div class="logo">${MIC_SVG}</div>
    <h1>${login ? "Selamat Datang" : "Buat Akun"}</h1>
    <p class="muted">${login ? "Kelola keuangan Anda dengan asisten cerdas." : "Daftar untuk mulai mencatat keuangan."}</p>
    ${login ? "" : `<label class="fl">Nama</label><input class="field" id="au-name" placeholder="Nama Anda" />`}
    <label class="fl">Email</label><input class="field" id="au-email" type="email" placeholder="Alamat email Anda" />
    <label class="fl">Kata Sandi</label><input class="field" id="au-pass" type="password" placeholder="${login ? "Masukkan kata sandi" : "Minimal 6 karakter"}" />
    <button class="btn primary" id="au-go" style="margin-top:16px">${login ? "MASUK" : "DAFTAR"}</button>
    ${login ? `<div style="text-align:center;margin-top:12px"><a id="au-forgot" style="cursor:pointer">Lupa Kata Sandi?</a></div>
    <div class="or">Atau masuk dengan</div>
    <div class="socials"><div class="soc" data-soon>Google</div><div class="soc" data-soon>Apple</div><div class="soc" data-soon>Facebook</div></div>
    <div class="voice-card" data-soon><span class="vic">${MIC_SVG.replace('#fff','#06B6D4').replace('30" height="30','20" height="20')}</span><div><b>Suara Quick-Login</b><div class="s">Masuk dengan Suara (Lebih Cepat)</div></div></div>` : ""}
    <div style="text-align:center;margin-top:20px" class="muted">${login ? 'Belum punya akun? <a id="au-switch" style="cursor:pointer">Daftar Sekarang</a>' : 'Sudah punya akun? <a id="au-switch" style="cursor:pointer">Masuk</a>'}</div>
  </div>`;
  const submit = async () => {
    const email = ($("au-email").value || "").trim();
    const pass = $("au-pass").value || "";
    if (!email || !pass) return toast("Isi email & kata sandi", true);
    try {
      const body = login ? { email, password: pass }
        : { email, password: pass, display_name: ($("au-name").value || "").trim() };
      const out = await api("POST", login ? "/api/auth/login" : "/api/auth/register", body);
      setToken(out.token); $("fab").hidden = false; go("home");
    } catch (e) { toast(e.message, true); }
  };
  $("au-go").addEventListener("click", submit);
  $("au-pass").addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });
  $("au-switch").addEventListener("click", () => showAuth(login ? "register" : "login"));
  const fg = $("au-forgot"); if (fg) fg.addEventListener("click", () => toast("Fitur reset kata sandi segera hadir"));
  $("view").querySelectorAll("[data-soon]").forEach((el) => el.addEventListener("click", () => toast("Fitur ini segera hadir")));
}

let ACCOUNTS = [];
let VIEW = "home";
let draft = null;

// ---- toast + sheet ------------------------------------------------- //
function toast(msg, err) {
  const t = $("toast"); t.textContent = msg; t.className = "toast show" + (err ? " err" : "");
  setTimeout(() => (t.className = "toast"), 1800);
}
function openSheet() { $("scrim").classList.add("show"); $("sheet").classList.add("show"); }
function closeSheet() { $("scrim").classList.remove("show"); $("sheet").classList.remove("show"); stopVoice(); }
$("scrim").addEventListener("click", closeSheet);

// ---- navigation ---------------------------------------------------- //
function navHTML() {
  const item = (id, label, path) =>
    `<a data-view="${id}" class="${VIEW === id ? "on" : ""}">${path}${label}</a>`;
  const home = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 10l9-7 9 7v9a2 2 0 01-2 2h-3v-7H8v7H5a2 2 0 01-2-2z"/></svg>';
  const hist = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h10"/></svg>';
  const bud = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18M3 8h4M3 16h4M17 8h4M17 16h4M9 5h6M9 19h6"/></svg>';
  const acc = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0116 0"/></svg>';
  $("nav").innerHTML = item("home", "Beranda", home) + item("history", "Riwayat", hist) +
    '<a class="nav-spacer" style="visibility:hidden">·</a>' + item("anggaran", "Anggaran", bud) + item("accounts", "Akun", acc);
  $("nav").querySelectorAll("a[data-view]").forEach((a) =>
    a.addEventListener("click", () => go(a.dataset.view)));
}
function go(view) { VIEW = view; render(); }

async function render() {
  navHTML();
  const v = $("view");
  v.innerHTML = '<div class="loading"><div class="spin"></div>Memuat…</div>';
  try {
    if (VIEW === "home") await renderHome();
    else if (VIEW === "history") await renderHistory();
    else if (VIEW === "anggaran") await renderAnggaran();
    else if (VIEW === "accounts") await renderAccounts();
  } catch (e) {
    if (VIEW === "__auth") return; // layar login sedang tampil
    v.innerHTML = `<div class="empty"><div class="big">⚠️</div><p>${esc(e.message)}</p></div>`;
  }
}

// ---- HOME ---------------------------------------------------------- //
async function renderHome() {
  const [sum, accts, bud] = await Promise.all([
    api("GET", "/api/summary"), api("GET", "/api/accounts"), api("GET", "/api/budget").catch(() => ({ alerts: [] })),
  ]);
  ACCOUNTS = accts;
  $("topbar").innerHTML = `<h1>Beranda</h1><span class="period">Bulan Ini</span>`;
  const hasData = sum.income || sum.expense || (sum.recent && sum.recent.length) || accts.some((a) => a.balance);
  if (!hasData && accts.length === 0) return renderOnboarding();

  const cats = sum.expense_by_category || [];
  const max = cats.reduce((m, c) => Math.max(m, c.amount), 0) || 1;
  const ncf = sum.net_cash_flow || 0;
  const alert = (bud.alerts || [])[0];
  const banner = alert ? `<div class="alert-banner ${alert.level === "over" ? "over" : ""}">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z"/></svg>
    <div><b>${esc(alert.title)}</b><div>${esc(alert.message)}</div></div></div>` : "";
  const topCat = cats[0] ? cats[0].category : null;
  const chips = accts.filter((a) => a.type !== "credit_card").slice(0, 3)
    .map((a) => `<div class="bchip"><div class="n">${esc(a.name)}</div><div class="v">${rp(a.balance)}</div></div>`).join("");
  $("view").innerHTML = banner + `
    <div class="card hero balance">
      <div class="label">Total Saldo</div><div class="value">${rp(sum.total_balance)}</div>
      ${chips ? `<div class="bchips">${chips}</div>` : ""}
    </div>
    <div class="cards">
      <div class="card"><div class="label">Masuk (bln ini)</div><div class="value in">+${rp(sum.income)}</div></div>
      <div class="card"><div class="label">Keluar (bln ini)</div><div class="value out">−${rp(sum.expense)}</div>
        ${topCat ? `<div class="muted" style="font-size:11px;margin-top:3px">Terbesar: ${esc(topCat)}</div>` : ""}</div>
      <div class="card wide"><div class="label">Arus Kas Bersih (bln ini)</div><div class="value ${ncf < 0 ? "out" : "in"}">${ncf < 0 ? "−" : "+"}${rp(ncf)}</div></div>
    </div>
    ${cats.length ? `<div class="sec">Pengeluaran per kategori</div>${cats.map((c) => `
      <div class="bar-row"><div class="bar-top"><span>${esc(c.category)}</span><span>${rp(c.amount)}</span></div>
      <div class="bar"><i style="width:${Math.round(c.amount / max * 100)}%"></i></div></div>`).join("")}` : ""}
    <div class="sec">Transaksi terbaru</div>
    <div id="recent">${(sum.recent || []).map(txRow).join("") || '<p class="muted">Belum ada transaksi.</p>'}</div>`;
}

function renderOnboarding() {
  $("view").innerHTML = `
    <div class="empty">
      <div class="big">🎙️</div>
      <h2 style="margin:8px 0 2px">Mulai catat keuanganmu</h2>
      <p>Cukup ucapkan atau ketik satu kalimat — AI yang mencatatnya.</p>
      <div class="ex"><b>"Beli kopi 35 ribu pakai BCA"</b></div>
      <div class="ex">"Gaji 8 juta masuk BCA"</div>
      <div style="margin-top:18px"><button class="btn primary" id="ob-acc" style="max-width:300px;margin:0 auto">Tambah akun dulu</button></div>
    </div>`;
  $("ob-acc").addEventListener("click", () => go("accounts"));
}

function iconFor(type) {
  if (type === "transfer") return "⇄";
  if (type === "income" || type === "refund") return "＋";
  return "－";
}
function txRow(t) {
  const cls = t.type === "income" || t.type === "refund" ? "in" : (t.type === "transfer" ? "neu" : "out");
  const sign = t.type === "income" || t.type === "refund" ? "+" : (t.type === "transfer" ? "" : "−");
  const label = esc(t.category || t.note || TYPE_LABEL[t.type] || t.type);
  const sub = esc([TYPE_LABEL[t.type] || t.type, t.account, t.date].filter(Boolean).join(" · "));
  return `<div class="row"><div class="ic">${iconFor(t.type)}</div>
    <div class="grow"><div class="nm">${label}</div><div class="sub">${sub}</div></div>
    <span class="amt ${cls}">${sign}${rp(t.amount)}</span></div>`;
}

// ---- HISTORY ------------------------------------------------------- //
let histType = "", histQ = "", HIST_ROWS = [];
async function renderHistory() {
  $("topbar").innerHTML = `<h1>Riwayat</h1>`;
  const rows = await api("GET", "/api/transactions" + qs({ type: histType, q: histQ }));
  HIST_ROWS = rows;
  const chip = (v, l) => `<span class="chip ${histType === v ? "on" : ""}" data-t="${v}">${l}</span>`;
  $("view").innerHTML = `
    <div class="search">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9aa1ac" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
      <input id="hq" placeholder="Cari catatan / kategori…" value="${esc(histQ)}" />
    </div>
    <div class="chips">${chip("", "Semua")}${chip("expense", "Pengeluaran")}${chip("income", "Pemasukan")}${chip("transfer", "Transfer")}</div>
    <div id="hlist">${rows.map(histRow).join("") || '<p class="muted">Tidak ada transaksi.</p>'}</div>`;
  const q = $("hq");
  q.addEventListener("input", () => { histQ = q.value; clearTimeout(q._t); q._t = setTimeout(renderHistory, 250); });
  $("view").querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => { histType = c.dataset.t; renderHistory(); }));
  $("view").querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", () => delTx(b.dataset.del)));
  $("view").querySelectorAll("[data-edit]").forEach((b) => b.addEventListener("click", () => {
    const t = HIST_ROWS.find((r) => r.id === b.dataset.edit); if (t) editSheet(t);
  }));
}
function histRow(t) {
  const cls = t.type === "income" || t.type === "refund" ? "in" : (t.type === "transfer" ? "neu" : "out");
  const sign = t.type === "income" || t.type === "refund" ? "+" : (t.type === "transfer" ? "" : "−");
  const label = esc(t.category || t.note || TYPE_LABEL[t.type] || t.type);
  const sub = esc([TYPE_LABEL[t.type] || t.type, t.account, t.date].filter(Boolean).join(" · "));
  return `<div class="row"><div class="ic">${iconFor(t.type)}</div>
    <div class="grow"><div class="nm">${label}</div><div class="sub">${sub}</div></div>
    <span class="amt ${cls}">${sign}${rp(t.amount)}</span>
    <button class="act" data-edit="${t.id}" title="Ubah"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z"/></svg></button>
    <button class="act" data-del="${t.id}" title="Hapus"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg></button></div>`;
}
function editSheet(t) {
  $("sheetBody").innerHTML = `<h3>Ubah transaksi</h3>
    <label class="fl">Nominal (Rp)</label><input class="field" id="e-amt" inputmode="numeric" value="${t.amount}" />
    <label class="fl">Kategori</label><input class="field" id="e-cat" value="${esc(t.category || "")}" />
    <label class="fl">Catatan</label><input class="field" id="e-note" value="${esc(t.note || "")}" />
    <div class="btns"><button class="btn ghost" id="e-cancel">Batal</button><button class="btn primary" id="e-save">Simpan</button></div>`;
  openSheet();
  $("e-cancel").addEventListener("click", closeSheet);
  $("e-save").addEventListener("click", async () => {
    const amt = parseInt(($("e-amt").value || "").replace(/\D/g, ""), 10) || 0;
    if (amt <= 0) return toast("Nominal harus > 0", true);
    try {
      await api("PATCH", "/api/transactions/" + encodeURIComponent(t.id),
        { amount: amt, category: $("e-cat").value || null, note: $("e-note").value || null });
      closeSheet(); toast("Diperbarui"); renderHistory();
    } catch (e) { toast(e.message, true); }
  });
}
async function delTx(id) {
  if (!confirm("Hapus transaksi ini?")) return;
  try { await api("DELETE", "/api/transactions/" + encodeURIComponent(id)); toast("Dihapus"); renderHistory(); }
  catch (e) { toast(e.message, true); }
}

// ---- ACCOUNTS ------------------------------------------------------ //
async function renderAccounts() {
  $("topbar").innerHTML = `<h1>Akun</h1>`;
  const [accts, me] = await Promise.all([
    api("GET", "/api/accounts"), api("GET", "/api/auth/me").catch(() => null),
  ]);
  ACCOUNTS = accts;
  const total = accts.filter((a) => a.type !== "credit_card").reduce((s, a) => s + a.balance, 0);
  $("view").innerHTML = `
    ${me ? `<div class="user-row"><div class="uav">${esc((me.display_name || me.email || "?")[0].toUpperCase())}</div>
      <div class="grow"><div class="nm">${esc(me.display_name || "")}</div><div class="sub">${esc(me.email || "")}</div></div>
      <button class="act-btn" id="logout">Keluar</button></div>` : ""}
    <div class="card hero balance"><div class="label">Total Saldo</div><div class="value">${rp(total)}</div></div>
    <div class="sec">Daftar Akun</div>
    <div>${accts.map(acctRow).join("") || '<p class="muted">Belum ada akun.</p>'}</div>
    <button class="btn primary" id="add-acc" style="margin-top:14px">+ Tambah Akun</button>`;
  $("add-acc").addEventListener("click", showAddAccount);
  const lo = $("logout");
  if (lo) lo.addEventListener("click", async () => {
    try { await api("POST", "/api/auth/logout"); } catch (_) {}
    clearToken(); showAuth("login"); toast("Anda keluar");
  });
}
function acctRow(a) {
  const T = { bank: "Bank", cash: "Tunai", ewallet: "E-wallet", credit_card: "Kartu kredit" };
  const cls = a.type === "credit_card" ? "out" : "";
  return `<div class="row"><div class="ic">${esc(a.name[0] || "?")}</div>
    <div class="grow"><div class="nm">${esc(a.name)}</div><div class="sub">${T[a.type] || a.type}</div></div>
    <span class="amt ${cls}">${rp(a.balance)}</span></div>`;
}
function showAddAccount() {
  $("sheetBody").innerHTML = `<h3>Tambah Akun</h3>
    <label class="fl">Nama akun</label>
    <input class="field" id="a-name" placeholder="mis. BCA, Cash, GoPay" />
    <label class="fl">Tipe</label>
    <select class="field" id="a-type">
      <option value="bank">Bank</option><option value="cash">Tunai</option>
      <option value="ewallet">E-wallet</option><option value="credit_card">Kartu kredit</option>
    </select>
    <label class="fl">Saldo awal (Rp)</label>
    <input class="field" id="a-bal" inputmode="numeric" value="0" />
    <div class="btns"><button class="btn ghost" id="a-cancel">Batal</button><button class="btn primary" id="a-save">Simpan</button></div>`;
  openSheet();
  $("a-cancel").addEventListener("click", closeSheet);
  $("a-save").addEventListener("click", async () => {
    const name = $("a-name").value.trim();
    const type = $("a-type").value;
    const bal = parseInt(($("a-bal").value || "0").replace(/\D/g, ""), 10) || 0;
    if (!name) return toast("Nama akun wajib diisi", true);
    try { await api("POST", "/api/accounts", { name, type, starting_balance: bal }); closeSheet(); toast("Akun ditambahkan"); go("accounts"); }
    catch (e) { toast(e.message, true); }
  });
}

// ---- ANGGARAN (budget/target/alert) -------------------------------- //
const PERIODS = { daily: "Harian", weekly: "Mingguan", monthly: "Bulanan" };
function periodSelect(id, val) {
  return `<select class="field" id="${id}">
    <option value="daily" ${val === "daily" ? "selected" : ""}>Harian</option>
    <option value="weekly" ${val === "weekly" ? "selected" : ""}>Mingguan</option>
    <option value="monthly" ${val === "monthly" || !val ? "selected" : ""}>Bulanan</option></select>`;
}
async function renderAnggaran() {
  $("topbar").innerHTML = `<h1>Anggaran</h1>`;
  const [st, cfg] = await Promise.all([api("GET", "/api/budget"), api("GET", "/api/settings")]);
  const th = cfg.alert_threshold || 90;
  const barColor = (pct, over) => over ? "var(--out)" : (pct >= th ? "#f59e0b" : "var(--accent)");
  let html = "";
  if (st.spending_limit) {
    const s = st.spending_limit;
    html += `<div class="card wide"><div class="label">Batas pengeluaran (${PERIODS[s.period] || s.period})</div>
      <div class="value ${s.over ? "out" : ""}">${rp(s.used)} / ${rp(s.amount)}</div>
      <div class="bar" style="margin-top:8px"><i style="width:${Math.min(100, s.pct)}%;background:${barColor(s.pct, s.over)}"></i></div>
      <div class="muted" style="font-size:12px;margin-top:6px">${s.over ? "Melebihi batas" : "Sisa " + rp(s.remaining)} · ${s.pct}%</div></div>`;
  }
  if (st.income_target) {
    const t = st.income_target;
    html += `<div class="card wide" style="margin-top:10px"><div class="label">Target pemasukan (${PERIODS[t.period] || t.period})</div>
      <div class="value in">${rp(t.achieved)} / ${rp(t.amount)}</div>
      <div class="bar" style="margin-top:8px"><i style="width:${Math.min(100, t.pct)}%;background:var(--in)"></i></div>
      <div class="muted" style="font-size:12px;margin-top:6px">${t.pct}% tercapai</div></div>`;
  }
  (st.alerts || []).forEach((a) => { html += `<div class="banner" style="margin-top:10px">${esc(a.message)}</div>`; });
  html += `<div class="sec">Anggaran per kategori <a data-add-cat style="cursor:pointer;color:var(--accent);text-decoration:none">+ Tambah</a></div>`;
  if ((st.categories || []).length) {
    st.categories.forEach((c) => {
      html += `<div class="card" style="margin-bottom:8px"><div class="bar-top"><span>${esc(c.category)}</span><span>${rp(c.used)} / ${rp(c.amount)}</span></div>
        <div class="bar"><i style="width:${Math.min(100, c.pct)}%;background:${barColor(c.pct, c.status === "over")}"></i></div></div>`;
    });
  } else { html += `<p class="muted">Belum ada anggaran kategori.</p>`; }
  html += `<button class="btn ghost" id="open-settings" style="margin-top:14px">Atur Target &amp; Batas</button>`;
  $("view").innerHTML = html;
  $("open-settings").addEventListener("click", () => showSettings(cfg));
  const addc = $("view").querySelector("[data-add-cat]");
  if (addc) addc.addEventListener("click", () => showAddCategory(cfg));
}
function showSettings(cfg) {
  const sl = cfg.spending_limit || {}, it = cfg.income_target || {};
  $("sheetBody").innerHTML = `<h3>Target &amp; Batas</h3>
    <label class="fl">Batas pengeluaran — periode</label>${periodSelect("s-sl-p", sl.period)}
    <label class="fl">Batas pengeluaran (Rp)</label><input class="field" id="s-sl-a" inputmode="numeric" value="${sl.amount || ""}" />
    <label class="fl">Target pemasukan — periode</label>${periodSelect("s-it-p", it.period)}
    <label class="fl">Target pemasukan (Rp)</label><input class="field" id="s-it-a" inputmode="numeric" value="${it.amount || ""}" />
    <label class="fl">Ambang alert (%)</label><input class="field" id="s-th" inputmode="numeric" value="${cfg.alert_threshold || 90}" />
    <label class="fl">Email untuk alert</label><input class="field" id="s-email" value="${esc(cfg.alert_email || "")}" placeholder="nama@email.com" />
    <div class="btns"><button class="btn ghost" id="s-cancel">Batal</button><button class="btn primary" id="s-save">Simpan</button></div>`;
  openSheet();
  $("s-cancel").addEventListener("click", closeSheet);
  $("s-save").addEventListener("click", async () => {
    const num = (id) => parseInt(($(id).value || "").replace(/\D/g, ""), 10) || 0;
    const patch = {
      alert_threshold: num("s-th") || 90, alert_email: $("s-email").value.trim(),
      spending_limit: num("s-sl-a") ? { period: $("s-sl-p").value, amount: num("s-sl-a") } : null,
      income_target: num("s-it-a") ? { period: $("s-it-p").value, amount: num("s-it-a") } : null,
    };
    try { await api("POST", "/api/settings", patch); closeSheet(); toast("Tersimpan"); go("anggaran"); }
    catch (e) { toast(e.message, true); }
  });
}
function showAddCategory(cfg) {
  $("sheetBody").innerHTML = `<h3>Anggaran kategori</h3>
    <label class="fl">Kategori</label><input class="field" id="c-name" placeholder="mis. Transport" />
    <label class="fl">Batas per bulan (Rp)</label><input class="field" id="c-amt" inputmode="numeric" />
    <div class="btns"><button class="btn ghost" id="c-cancel">Batal</button><button class="btn primary" id="c-save">Simpan</button></div>`;
  openSheet();
  $("c-cancel").addEventListener("click", closeSheet);
  $("c-save").addEventListener("click", async () => {
    const name = $("c-name").value.trim();
    const amt = parseInt(($("c-amt").value || "").replace(/\D/g, ""), 10) || 0;
    if (!name || !amt) return toast("Isi kategori & nominal", true);
    const cats = (cfg.category_budgets || []).filter((c) => c.category !== name).concat([{ category: name, amount: amt }]);
    try { await api("POST", "/api/settings", { category_budgets: cats }); closeSheet(); toast("Anggaran ditambahkan"); go("anggaran"); }
    catch (e) { toast(e.message, true); }
  });
}

// ---- CAPTURE (suara/teks) ------------------------------------------ //
let recognition = null;
function openCapture() {
  $("sheetBody").innerHTML = `
    <h3>Catat transaksi</h3>
    <div class="cap-mic">
      <div class="waveform" id="wave">${Array.from({length:19}).map(()=>"<i></i>").join("")}</div>
      <div class="transcript" id="cap-transcript"></div>
      <button class="mic-btn" id="mic"><svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M12 2a3 3 0 013 3v6a3 3 0 01-6 0V5a3 3 0 013-3z"/><path d="M19 10a7 7 0 01-14 0"/><path d="M12 19v3"/></svg></button>
      <div class="cap-hint" id="cap-hint">Tekan mic lalu ucapkan, atau ketik di bawah</div>
    </div>
    <input class="field" id="cap-text" placeholder='mis. "Beli kopi 35 ribu pakai BCA"' />
    <div class="btns"><button class="btn ghost" id="cap-cancel">Batal</button><button class="btn primary" id="cap-go">Proses</button></div>`;
  openSheet();
  $("cap-cancel").addEventListener("click", closeSheet);
  $("cap-go").addEventListener("click", () => submitCapture($("cap-text").value));
  $("cap-text").addEventListener("keydown", (e) => { if (e.key === "Enter") submitCapture($("cap-text").value); });
  $("mic").addEventListener("click", toggleVoice);
}
function toggleVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { toast("Voice tidak didukung — ketik saja", true); $("cap-text").focus(); return; }
  if (recognition) return stopVoice();
  recognition = new SR(); recognition.lang = "id-ID"; recognition.interimResults = true; recognition.maxAlternatives = 1;
  $("mic").classList.add("rec"); $("cap-hint").textContent = "Mendengarkan…";
  const w = $("wave"); if (w) w.classList.add("on");
  recognition.onresult = (e) => {
    const t = Array.from(e.results).map((r) => r[0].transcript).join("");
    $("cap-transcript").textContent = t; $("cap-text").value = t;
    if (e.results[e.results.length - 1].isFinal) { stopVoice(); submitCapture(t); }
  };
  recognition.onerror = () => { stopVoice(); toast("Tidak bisa mendengar — ketik manual", true); $("cap-text").focus(); };
  recognition.onend = () => stopVoice();
  try { recognition.start(); } catch (_) { stopVoice(); }
}
function stopVoice() {
  if (recognition) { try { recognition.stop(); } catch (_) {} recognition = null; }
  const m = $("mic"); if (m) m.classList.remove("rec");
  const w = $("wave"); if (w) w.classList.remove("on");
  const h = $("cap-hint"); if (h) h.textContent = "Tekan mic lalu ucapkan, atau ketik di bawah";
}
async function submitCapture(text) {
  if (!text || !text.trim()) return;
  stopVoice();
  $("sheetBody").innerHTML = '<div class="loading"><div class="spin"></div>Memahami…</div>';
  try {
    const out = await api("POST", "/api/parse", { text });
    const drafts = out.drafts || [];
    if (!drafts.length || drafts[0].status === "not_transaction")
      return showMessage("Sepertinya ini bukan transaksi. Coba sebutkan nominalnya.");
    showConfirm(drafts[0]); // MVP: tangani draft pertama
  } catch (e) { showMessage(e.message); }
}
function showMessage(msg) {
  $("sheetBody").innerHTML = `<h3>Hmm…</h3><div class="banner">${esc(msg)}</div>
    <div class="btns"><button class="btn ghost" id="m-close">Tutup</button></div>`;
  $("m-close").addEventListener("click", closeSheet);
}

// ---- CONFIRM (draft editable) -------------------------------------- //
function accountOptions(sel) {
  return ACCOUNTS.map((a) => `<option value="${a.id}" ${a.id === sel ? "selected" : ""}>${esc(a.name)}</option>`).join("");
}
function showConfirm(d) {
  draft = d;
  const types = ["expense", "income", "transfer", "refund"];
  const isTransfer = () => draft.type === "transfer";
  const dupBanner = (d.duplicates && d.duplicates.length) ? `<div class="banner">Mirip transaksi sebelumnya — tetap simpan?</div>` : "";
  const render = () => {
    $("sheetBody").innerHTML = `
      <h3>Konfirmasi transaksi</h3>
      ${dupBanner}
      <div class="seg" id="seg">${types.map((t) => `<span data-t="${t}" class="${draft.type === t ? "on" : ""}">${TYPE_LABEL[t]}</span>`).join("")}</div>
      <div class="amount-big">${rp(draft.amount || 0)}</div>
      <label class="fl">Nominal (Rp)</label>
      <input class="field" id="d-amt" inputmode="numeric" value="${draft.amount || ""}" />
      ${isTransfer() ? `
        <label class="fl">Dari akun</label><select class="field" id="d-from">${accountOptions(draft.from_account_id)}</select>
        <label class="fl">Ke akun</label><select class="field" id="d-to">${accountOptions(draft.to_account_id)}</select>
      ` : `
        <label class="fl">Akun</label><select class="field" id="d-acc">${accountOptions(draft.account_id)}</select>
        <label class="fl">Kategori</label><input class="field" id="d-cat" value="${esc(draft.category || "")}" placeholder="mis. Makanan & Minuman" />
      `}
      <label class="fl">Catatan</label><input class="field" id="d-note" value="${esc(draft.note || "")}" />
      <div class="btns"><button class="btn ghost" id="d-cancel">Batal</button><button class="btn primary" id="d-save">Simpan</button></div>`;
    $("seg").querySelectorAll("span").forEach((s) => s.addEventListener("click", () => { syncFromInputs(); draft.type = s.dataset.t; render(); }));
    $("d-amt").addEventListener("input", (e) => { const n = parseInt(e.target.value.replace(/\D/g, ""), 10); document.querySelector(".amount-big").textContent = rp(n || 0); });
    $("d-cancel").addEventListener("click", closeSheet);
    $("d-save").addEventListener("click", saveDraft);
  };
  const syncFromInputs = () => {
    const amt = $("d-amt"); if (amt) draft.amount = parseInt(amt.value.replace(/\D/g, ""), 10) || 0;
    const note = $("d-note"); if (note) draft.note = note.value;
    if (!isTransfer()) { const c = $("d-cat"); if (c) draft.category = c.value; const a = $("d-acc"); if (a) draft.account_id = a.value; }
    else { const f = $("d-from"); if (f) draft.from_account_id = f.value; const t = $("d-to"); if (t) draft.to_account_id = t.value; }
  };
  render();

  async function saveDraft() {
    syncFromInputs();
    if (!ACCOUNTS.length) { toast("Tambah akun dulu di menu Akun", true); return; }
    const f = { type: draft.type, amount: draft.amount, note: draft.note || null, occurred_at: draft.occurred_at };
    if (draft.type === "transfer") { f.from_account_id = draft.from_account_id; f.to_account_id = draft.to_account_id; }
    else { f.account_id = draft.account_id; f.category = draft.category || null; }
    if (!f.amount || f.amount <= 0) return toast("Nominal harus > 0", true);
    try { await api("POST", "/api/transactions", f); closeSheet(); toast("Tercatat ✓"); go("home"); }
    catch (e) { toast(e.message, true); }
  }
}

// ---- helpers ------------------------------------------------------- //
function qs(obj) {
  const p = Object.entries(obj).filter(([, v]) => v).map(([k, v]) => `${k}=${encodeURIComponent(v)}`);
  return p.length ? "?" + p.join("&") : "";
}

// ---- boot ---------------------------------------------------------- //
$("fab").addEventListener("click", async () => {
  try { ACCOUNTS = await api("GET", "/api/accounts"); } catch (_) {}
  openCapture();
});
async function init() {
  if (!getToken()) { showAuth("login"); return; }
  try { await api("GET", "/api/auth/me"); $("fab").hidden = false; render(); }
  catch (_) { /* 401 sudah memunculkan layar login */ }
}
init();
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}
