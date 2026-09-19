DASHBOARD_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TBOT — XAUUSD Flip & Dip Lab</title>
<style>
:root{
  --bg:#07090d;--panel:#0e1219;--panel2:#111722;--line:#202938;
  --text:#f4f7fb;--muted:#8e9bad;--accent:#d7ff54;--good:#68e0a0;
  --warn:#ffcc66;--bad:#ff7a86;--blue:#7cb8ff;
}
*{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 20% 0%,#121b25 0,#07090d 38%);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}
.shell{max-width:1180px;margin:auto;padding:28px 20px 60px}
.top{display:flex;gap:20px;justify-content:space-between;align-items:center;margin-bottom:26px}
.brand{font-weight:800;letter-spacing:.18em;font-size:20px}.brand span{color:var(--accent)}
.badge{border:1px solid var(--line);background:#0b1016;padding:8px 12px;border-radius:999px;color:var(--muted);font-size:12px}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--good);margin-right:7px}
.nav{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:18px}
.nav button,.tf button{background:transparent;border:1px solid var(--line);color:var(--muted);padding:10px 14px;border-radius:10px;cursor:pointer}
.nav button.active,.tf button.active{background:var(--accent);color:#0b0e12;border-color:var(--accent);font-weight:700}
.grid{display:grid;grid-template-columns:1.4fr .8fr;gap:16px}.card{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 18px 50px rgba(0,0,0,.22)}
.eyebrow{font-size:11px;letter-spacing:.16em;color:var(--muted);text-transform:uppercase}.price{font-size:42px;font-weight:800;margin:8px 0}.muted{color:var(--muted)}
.tf{display:flex;gap:7px;margin-top:18px}.status{display:inline-flex;align-items:center;padding:8px 11px;border-radius:999px;background:rgba(104,224,160,.08);color:var(--good);font-size:12px;border:1px solid rgba(104,224,160,.25)}
.plan{margin-top:16px;border-top:1px solid var(--line);padding-top:16px}.plan-title{font-size:30px;font-weight:900}.SELL{color:var(--bad)}.BUY{color:var(--good)}
.kvs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:14px}.kv{background:#0a0e14;border:1px solid var(--line);border-radius:12px;padding:12px}.kv b{display:block;font-size:12px;color:var(--muted);margin-bottom:6px}.metric{font-size:30px;font-weight:800;margin-top:6px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}.stat{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}.stat b{font-size:26px;display:block}.stat span{font-size:12px;color:var(--muted)}
.table{width:100%;border-collapse:collapse;margin-top:8px}.table th,.table td{text-align:left;padding:12px 8px;border-bottom:1px solid var(--line);font-size:13px}.table th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em}
.empty{color:var(--muted);padding:26px 0}.notice{margin-top:14px;font-size:12px;color:var(--muted);line-height:1.5}
.hidden{display:none!important}
@media(max-width:800px){.grid{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}.kvs{grid-template-columns:1fr}.price{font-size:34px}.top{align-items:flex-start;flex-direction:column}}
</style>
</head>
<body>
<div class="shell">
  <div class="top">
    <div><div class="brand">T<span>BOT</span></div><div class="muted" style="font-size:12px;margin-top:4px">XAUUSD Flip & Dip Lab · planning/demo only · execution disabled</div></div>
    <div id="workerBadge" class="badge"><span class="dot"></span>Checking worker…</div>
  </div>

  <div class="nav">
    <button class="active" data-tab="live">Live</button>
    <button data-tab="plans">Plans</button>
    <button data-tab="performance">Performance</button>
    <button data-tab="history">History</button>
  </div>

  <section id="live" class="tab">
    <div class="grid">
      <div class="card">
        <div class="eyebrow">Market</div>
        <div class="price">XAUUSD</div>
        <div id="liveStatus" class="status">Monitoring</div>
        <div class="tf">
          <button class="active" data-tf="5M">5M</button>
          <button data-tf="15M">15M</button>
          <button data-tf="1H">1H</button>
        </div>
        <div id="livePlan" class="plan"><div class="empty">Loading latest planning state…</div></div>
      </div>
      <div class="card">
        <div class="eyebrow">System</div>
        <div class="metric" id="strategyVersion">—</div>
        <div class="muted">Strategy version</div>
        <div class="kvs">
          <div class="kv"><b>Execution</b><span>Disabled</span></div>
          <div class="kv"><b>Symbol</b><span>XAUUSD</span></div>
          <div class="kv"><b>Minimum target</b><span>5R</span></div>
          <div class="kv"><b>Risk plan</b><span>5%</span></div>
          <div class="kv"><b>Calibration</b><span id="calibrationReady">Checking…</span></div>
        </div>
        <div class="notice">A READY plan is a hypothetical planning signal. TBOT does not place broker orders.</div>
        <div id="newsAttribution" class="notice"></div>
      </div>
    </div>
  </section>

  <section id="plans" class="tab hidden"><div class="card"><div class="eyebrow">Open demo plans</div><div id="plansBody"></div></div></section>

  <section id="performance" class="tab hidden">
    <div class="stats">
      <div class="stat"><b id="candidateCount">—</b><span>Candidates</span></div>
      <div class="stat"><b id="readyCount">—</b><span>Ready zones</span></div>
      <div class="stat"><b id="eventCount">—</b><span>Independent events</span></div>
      <div class="stat"><b id="secondaryCount">—</b><span>Secondary zones</span></div>
    </div>
    <div class="card" style="margin-bottom:16px">
      <div class="eyebrow">What if I started with…</div>
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:12px">
        <label class="kv" style="min-width:180px"><b>Starting balance ($)</b><input id="simBalance" type="number" min="1" step="1" value="100" style="width:100%;background:transparent;color:var(--text);border:0;outline:0;font-size:20px"></label>
        <label class="kv" style="min-width:180px"><b>Risk per event (%)</b><input id="simRisk" type="number" min="0.1" max="100" step="0.1" value="5" style="width:100%;background:transparent;color:var(--text);border:0;outline:0;font-size:20px"></label>
        <button id="runSim" style="align-self:stretch;background:var(--accent);border:0;border-radius:12px;padding:0 18px;font-weight:800;cursor:pointer">Calculate</button>
      </div>
      <div class="stats" style="grid-template-columns:repeat(4,minmax(0,1fr));margin-top:16px">
        <div class="stat"><b id="simEnd">—</b><span>Ending balance</span></div>
        <div class="stat"><b id="simProfit">—</b><span>Net profit</span></div>
        <div class="stat"><b id="simReturn">—</b><span>Return</span></div>
        <div class="stat"><b id="simDD">—</b><span>Max drawdown</span></div>
      </div>
      <div id="simValidity" class="notice"></div>
      <div id="simCurve" style="margin-top:14px"></div>
      <div class="notice">Hypothetical compounding scenario on primary historical events only. Default payout assumptions: 5R=+5R, 3.5R=+3.5R, 2R=+2R, invalidation=-1R, ambiguous=0R. Candle-close invalidation does not guarantee a real trade would lose exactly 1R.</div>
    </div>
    <div class="card"><div class="eyebrow">Historical calibration outcomes</div><div id="outcomes"></div><div class="notice">R values here use stabilized structural sizing distance. They are calibration metrics, not broker-realized P&L.</div></div>
  </section>

  <section id="history" class="tab hidden"><div class="card"><div class="eyebrow">Plan history</div><div id="historyBody"></div></div></section>
</div>
<script>
const q=s=>document.querySelector(s), qa=s=>[...document.querySelectorAll(s)];
let tf="5M";
const fmt=n=>n==null?"—":Number(n).toFixed(2);
async function get(url){try{const r=await fetch(url);return await r.json()}catch(e){return {status:"error"}}}
async function health(){
 const d=await get("/api/health");
 q("#strategyVersion").textContent=d.strategy_version||"—";
 const worker=d.worker||{};
 const badge=q("#workerBadge");
 if(worker.fresh){
   badge.innerHTML='<span class="dot"></span>Worker online · '+(worker.news_provider_connected?'news protected':'news not connected');
 }else if(worker.status==="stale"){
   badge.innerHTML='<span class="dot" style="background:var(--warn)"></span>Worker stale';
 }else{
   badge.innerHTML='<span class="dot" style="background:var(--bad)"></span>Worker '+(worker.status||"offline");
 }
 const provider=worker.news_provider_name||"";
 const attribution=q("#newsAttribution");
 if(provider==="XoomarEconomicCalendarProvider"){
   attribution.innerHTML='Economic calendar: <a href="https://xoomar.com/markets" target="_blank" rel="noopener noreferrer" style="color:var(--blue)">xoomar.com/markets</a>';
 }else if(provider==="FinanceCalendarProvider"){
   attribution.innerHTML='Economic calendar: <a href="https://www.financecalendar.com" target="_blank" rel="noopener noreferrer" style="color:var(--blue)">financecalendar.com</a>';
 }else if(provider){
   attribution.textContent='Economic calendar: '+provider;
 }else{
   attribution.textContent='';
 }
 const cal=await get("/api/calibration/status");
 q("#calibrationReady").textContent=cal.ready_for_forward_demo?"Forward-demo ready":"Needs calibration";
}
async function live(){
  q("#livePlan").innerHTML='<div class="empty">Refreshing…</div>';
  const d=await get("/api/live?entry_timeframe="+tf+"&bars=500");
  if(d.status==="not_configured"){q("#liveStatus").textContent="Server data key not configured";q("#livePlan").innerHTML='<div class="empty">Configure the server-side market-data secret to enable live scanning.</div>';return}
  if(d.status!=="ok"){q("#liveStatus").textContent="Unavailable";q("#livePlan").innerHTML='<div class="empty">Live data unavailable.</div>';return}
  q("#liveStatus").textContent="Monitoring · "+tf+" → "+d.confirmation_timeframe;
  const p=d.latest_ready_plan;
  if(!p){q("#livePlan").innerHTML='<div class="empty">No READY plan in the current scan window.</div>';return}
  q("#livePlan").innerHTML=`
    <div class="eyebrow">Latest ready plan</div>
    <div class="plan-title ${p.direction}">${p.direction}</div>
    <div class="kvs">
      <div class="kv"><b>Flip zone</b><span>${fmt(p.zone_lower)} – ${fmt(p.zone_upper)}</span></div>
      <div class="kv"><b>Rejection</b><span>${fmt(p.rejection_score)}</span></div>
      <div class="kv"><b>HTF structure</b><span>${p.confirmation_timeframe} ${p.structure_kind||"—"}</span></div>
      <div class="kv"><b>Retest</b><span>${p.retest_at||"—"}</span></div>
    </div>
    <div class="notice">${p.invalidation_rule}. Minimum target ${p.minimum_rr}R.</div>`;
}
async function performance(){
 const balance=Math.max(1,Number(q("#simBalance")?.value||100));
 const risk=Math.max(.1,Math.min(100,Number(q("#simRisk")?.value||5)));
 const d=await get("/api/performance?starting_balance="+encodeURIComponent(balance)+"&risk_percent="+encodeURIComponent(risk));
 q("#candidateCount").textContent=d.candidate_count??0;q("#readyCount").textContent=d.ready_zone_count??0;
 q("#eventCount").textContent=d.independent_event_count??0;q("#secondaryCount").textContent=d.secondary_zone_count??0;
 const o=d.outcomes_primary_events||{};
 q("#outcomes").innerHTML=Object.keys(o).length?'<div class="kvs">'+Object.entries(o).map(([k,v])=>`<div class="kv"><b>${k}</b><span>${v}</span></div>`).join("")+'</div>':'<div class="empty">Run the enhanced calibration to populate outcomes.</div>';
 const s=d.account_simulation||{};
 const simValidity=q("#simValidity");
 if(s.valid_for_current_strategy_contract===false){
   simValidity.textContent="Current historical files are not validated for the authoritative strategy contract. Re-run calibration before using this scenario for review.";
 }else if(s.strategy_profit_estimate_available===false){
   simValidity.textContent="Milestone scenario only — exact strategy P&L is unavailable until you define the partial TP ladder.";
 }else{
   simValidity.textContent="";
 }
 q("#simEnd").textContent=s.ending_balance==null?"—":"$"+Number(s.ending_balance).toFixed(2);
 q("#simProfit").textContent=s.net_profit==null?"—":(Number(s.net_profit)>=0?"+":"")+"$"+Number(s.net_profit).toFixed(2);
 q("#simReturn").textContent=s.return_percent==null?"—":Number(s.return_percent).toFixed(1)+"%";
 q("#simDD").textContent=s.max_drawdown_percent==null?"—":Number(s.max_drawdown_percent).toFixed(1)+"%";
 const pts=s.equity_curve||[];
 if(!pts.length){q("#simCurve").innerHTML='<div class="empty">No simulated events.</div>';return}
 const w=900,h=180,pad=18,vals=[Number(s.starting_balance),...pts.map(x=>Number(x.balance_after))];
 const min=Math.min(...vals),max=Math.max(...vals),span=Math.max(max-min,1e-9);
 const xy=vals.map((v,i)=>[pad+(w-2*pad)*(i/Math.max(vals.length-1,1)),h-pad-(h-2*pad)*((v-min)/span)]);
 const points=xy.map(p=>p.join(",")).join(" ");
 q("#simCurve").innerHTML=`<svg viewBox="0 0 ${w} ${h}" style="width:100%;height:auto;display:block"><polyline fill="none" stroke="currentColor" stroke-width="3" points="${points}"/><text x="${pad}" y="16" fill="currentColor" font-size="12">High ${Number(s.highest_balance).toFixed(2)}</text><text x="${pad}" y="${h-2}" fill="currentColor" font-size="12">Low ${Number(s.lowest_balance).toFixed(2)}</text></svg>`;
}
function outcomeLabel(x){
 const status=x.outcome_status||"OPEN";
 if(x.terminal){
   if(x.terminal_reason==="invalidated_after_2r") return "2R reached · later invalidated";
   if(x.terminal_reason==="invalidated_after_3_5r") return "3.5R reached · later invalidated";
   if(x.terminal_reason==="target_5r_reached") return "5R reached · terminal";
   if(x.terminal_reason==="candle_close_invalidation") return "Invalidated";
   if(x.terminal_reason==="ambiguous_target_vs_invalidation_order") return "Ambiguous";
   return status+" · terminal";
 }
 if(status==="TARGET_2R") return "2R reached · active";
 if(status==="TARGET_3_5R") return "3.5R reached · active";
 return status;
}
function table(items){
 if(!items||!items.length)return '<div class="empty">No plans available.</div>';
 return '<table class="table"><thead><tr><th>Time</th><th>TF</th><th>Side</th><th>Zone</th><th>Outcome</th></tr></thead><tbody>'+
 items.map(x=>`<tr><td>${x.retest_at||x.created_at||"—"}</td><td>${x.entry_timeframe||"—"}</td><td class="${x.direction}">${x.direction||"—"}</td><td>${fmt(x.zone_lower)}–${fmt(x.zone_upper)}</td><td>${outcomeLabel(x)}</td></tr>`).join("")+'</tbody></table>';
}
async function plans(){const d=await get("/api/plans");q("#plansBody").innerHTML=table(d.items)}
async function history(){const d=await get("/api/history?limit=100&primary_only=true");q("#historyBody").innerHTML=table(d.items)}
qa(".nav button").forEach(b=>b.onclick=()=>{qa(".nav button").forEach(x=>x.classList.remove("active"));b.classList.add("active");qa(".tab").forEach(x=>x.classList.add("hidden"));q("#"+b.dataset.tab).classList.remove("hidden");if(b.dataset.tab==="plans")plans();if(b.dataset.tab==="performance")performance();if(b.dataset.tab==="history")history()});
qa(".tf button").forEach(b=>b.onclick=()=>{qa(".tf button").forEach(x=>x.classList.remove("active"));b.classList.add("active");tf=b.dataset.tf;live()});
q("#runSim").onclick=performance;
health();live();
</script>
</body>
</html>
"""