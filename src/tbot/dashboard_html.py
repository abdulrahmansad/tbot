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
.formrow{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}.field{min-width:170px;flex:1}.field label{display:block;color:var(--muted);font-size:11px;margin-bottom:6px;text-transform:uppercase;letter-spacing:.08em}.field input{width:100%;background:#0a0e14;border:1px solid var(--line);color:var(--text);border-radius:10px;padding:11px}.action{background:var(--accent);color:#0b0e12;border:0;border-radius:10px;padding:11px 16px;font-weight:800;cursor:pointer}.action:disabled{opacity:.5;cursor:not-allowed}
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
    <button data-tab="test">Test Strategy</button>
    <button data-tab="demo">Demo</button>
    <button data-tab="plans">Plans</button>
    <button data-tab="performance">Performance</button>
    <button data-tab="history">History</button>
    <button data-tab="review">Review</button>
  </div>

  <section id="live" class="tab">
    <div class="grid">
      <div class="card">
        <div class="eyebrow">Market</div>
        <div class="price">XAUUSD <span id="marketPrice" style="font-size:18px;color:var(--muted)">—</span></div>
        <div id="liveStatus" class="status">Monitoring</div>
        <div class="tf">
          <button class="active" data-tf="5M">5M</button>
          <button data-tf="15M">15M</button>
          <button data-tf="1H">1H · secondary</button>
        </div>
        <div id="livePlan" class="plan"><div class="empty">Loading latest planning state…</div></div>
        <div id="liveDiagnostics" class="notice"></div>
        <div class="notice">Primary entries: 5M and 15M. 1H→4H is a valid secondary entry mode and appears here even when the current worker has it disabled.</div>
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
          <div class="kv"><b>Market</b><span id="marketState">Checking…</span></div>
          <div class="kv"><b>Trading window</b><span id="tradingWindow">Checking…</span></div>
          <div class="kv"><b>News gate</b><span id="newsGate">Checking…</span></div>
          <div class="kv"><b>Active TFs</b><span id="activeTfs">—</span></div>
        </div>
        <div id="nextNews" class="notice"></div>
        <div class="notice">A READY plan is a hypothetical planning signal. TBOT does not place broker orders.</div>
        <div id="newsAttribution" class="notice"></div>
      </div>
    </div>
  </section>

  <section id="test" class="tab hidden">
    <div class="card">
      <div class="eyebrow">Historical strategy test</div>
      <div class="metric">What would this strategy have done?</div>
      <div class="notice">Choose a past interval. Phase 0 interactive tests are limited to 14 days so 5M history is not silently truncated.</div>
      <div class="formrow">
        <div class="field"><label>From</label><input id="testFrom" type="datetime-local"></div>
        <div class="field"><label>To</label><input id="testTo" type="datetime-local"></div>
        <div class="field"><label>Starting balance ($)</label><input id="testBalance" type="number" min="1" value="100"></div>
        <div class="field"><label>Risk per trade (%)</label><input id="testRisk" type="number" min="0.1" max="5" step="0.1" value="5"></div>
      </div>
      <div class="formrow">
        <label class="kv" style="display:flex;gap:8px;align-items:center"><input id="test1h" type="checkbox"> Include secondary 1H → 4H (experimental unless separately calibrated)</label>
        <button class="action" id="runHistoricalTest">Run historical test</button>
      </div>
      <div id="testMessage" class="notice"></div>
    </div>
    <div id="testResults" class="hidden">
      <div class="stats">
        <div class="stat"><b id="testEndBalance">—</b><span>Ending balance scenario</span></div>
        <div class="stat"><b id="testProfit">—</b><span>Net profit scenario</span></div>
        <div class="stat"><b id="testReturn">—</b><span>Return scenario</span></div>
        <div class="stat"><b id="testDrawdown">—</b><span>Max drawdown</span></div>
      </div>
      <div class="grid">
        <div class="card"><div class="eyebrow">Outcomes</div><div id="testOutcomes"></div></div>
        <div class="card"><div class="eyebrow">Timeframe summary</div><div id="testTimeframes"></div></div>
      </div>
      <div class="card" style="margin-top:16px"><div class="eyebrow">Historical setups</div><div id="testSetups"></div><div id="testScenarioNote" class="notice"></div></div>
    </div>
  </section>

  <section id="demo" class="tab hidden">
    <div class="grid">
      <div class="card">
        <div class="eyebrow">Forward demo session</div>
        <div class="metric">Run the strategy without trading</div>
        <div class="formrow">
          <div class="field"><label>Session name</label><input id="demoName" value="Flip & Dip Demo"></div>
          <div class="field"><label>Start</label><input id="demoStart" type="datetime-local"></div>
          <div class="field"><label>End</label><input id="demoEnd" type="datetime-local"></div>
        </div>
        <div class="formrow"><button class="action" id="saveDemoSession">Save demo session</button></div>
        <div class="notice">The worker may stay running. New demo plans are recorded only while a configured session is ACTIVE.</div>
      </div>
      <div class="card">
        <div class="eyebrow">Current session</div>
        <div class="metric" id="demoStatus">Loading…</div>
        <div id="demoDetails" class="notice"></div>
        <div class="kvs">
          <div class="kv"><b>Plans</b><span id="demoPlanCount">0</span></div>
          <div class="kv"><b>Open</b><span id="demoOpenCount">0</span></div>
          <div class="kv"><b>Terminal</b><span id="demoTerminalCount">0</span></div>
        </div>
        <div id="demoOutcomes" class="notice"></div>
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
    <div class="card" style="margin-bottom:16px"><div class="eyebrow">Historical calibration outcomes</div><div id="outcomes"></div><div class="notice">R values here use stabilized structural sizing distance. They are calibration metrics, not broker-realized P&L.</div></div>
    <div class="grid">
      <div class="card"><div class="eyebrow">By entry timeframe</div><div id="byTimeframe"></div></div>
      <div class="card"><div class="eyebrow">By execution #</div><div id="byExecution"></div></div>
    </div>
    <div class="card" style="margin-top:16px"><div class="eyebrow">By direction</div><div id="byDirection"></div></div>
  </section>

  <section id="history" class="tab hidden"><div class="card"><div class="eyebrow">Plan history</div><div id="historyBody"></div></div></section>

  <section id="review" class="tab hidden">
    <div class="grid">
      <div class="card">
        <div class="eyebrow">Phase 0 contract</div>
        <div class="metric">Owner Flip & Dip</div>
        <div class="kvs">
          <div class="kv"><b>Primary entries</b><span>5M → 15M · 15M → 1H</span></div>
          <div class="kv"><b>Secondary entry</b><span>1H → 4H</span></div>
          <div class="kv"><b>Executions / zone</b><span>Max 3</span></div>
          <div class="kv"><b>Invalidation</b><span>Entry-TF candle close</span></div>
          <div class="kv"><b>Risk cap</b><span>5% / execution</span></div>
          <div class="kv"><b>Minimum target</b><span>5R</span></div>
        </div>
      </div>
      <div class="card">
        <div class="eyebrow">Forward-demo readiness</div>
        <div class="metric" id="reviewState">Checking…</div>
        <div id="reviewDetails" class="notice"></div>
      </div>
    </div>
    <div class="card" style="margin-top:16px">
      <div class="eyebrow">Still intentionally configurable</div>
      <div class="kvs">
        <div class="kv"><b>Flip Zone definition</b><span>Candidate v1</span></div>
        <div class="kv"><b>Healthy rejection</b><span>Configurable threshold</span></div>
        <div class="kv"><b>CHOCH/BOS swing model</b><span>Candidate pivot-break model</span></div>
        <div class="kv"><b>Partial TP ladder</b><span>Owner configuration required</span></div>
      </div>
    </div>
  </section>
</div>
<script>
const q=s=>document.querySelector(s), qa=s=>[...document.querySelectorAll(s)];
let tf="5M";
const fmt=n=>n==null?"—":Number(n).toFixed(2);
async function get(url){try{const r=await fetch(url);return await r.json()}catch(e){return {status:"error"}}}
async function post(url,body){try{const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)return {status:"error",detail:d.detail||("HTTP "+r.status)};return d}catch(e){return {status:"error",detail:String(e)}}}
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
 q("#marketState").textContent=d.market_status==="OPEN"?"OPEN":d.market_status==="CLOSED_OR_STALE"?"CLOSED / DATA STALE":d.market_status||"—";
 q("#tradingWindow").textContent=d.trading_window_open===true?"OPEN":d.trading_window_open===false?"BLOCKED":"—";
 q("#newsGate").textContent=d.news_clear===true?"CLEAR":d.news_clear===false?"BLACKOUT":"—";
 q("#activeTfs").textContent=(d.active_entry_timeframes||[]).join(" · ")||"—";
 const next=d.next_high_impact_event;
 q("#nextNews").textContent=next?("Next high-impact USD event: "+next.title+" · "+next.scheduled_at):"No upcoming high-impact USD event in the current calendar window.";
 q("#reviewState").textContent=cal.ready_for_forward_demo&&worker.fresh?"DEMO ACTIVE":cal.ready_for_forward_demo?"READY / WORKER OFFLINE":"NOT READY";
 q("#reviewDetails").textContent="Schema "+(cal.schema_version??"—")+" · "+(cal.primary_events??0)+" primary historical events · "+(cal.ambiguous_primary_events??0)+" ambiguous · worker "+(worker.status||"unknown")+".";
 const ds=d.demo_session||{};q("#demoStatus").textContent=ds.status||"UNBOUNDED";q("#demoDetails").textContent=ds.configured?((ds.name||"Demo")+" · "+ds.start+" → "+ds.end):"No bounded demo session configured. Worker behaves as an unbounded forward demo.";
}
async function live(){
  q("#livePlan").innerHTML='<div class="empty">Refreshing…</div>';
  const d=await get("/api/live?entry_timeframe="+tf+"&bars=500");
  if(d.status==="not_configured"){q("#liveStatus").textContent="Server data key not configured";q("#livePlan").innerHTML='<div class="empty">Configure the server-side market-data secret to enable live scanning.</div>';return}
  if(d.status==="worker_snapshot_unavailable"&&tf==="1H"){q("#liveStatus").textContent="1H secondary mode · not active";q("#marketPrice").textContent="—";q("#livePlan").innerHTML='<div class="empty">1H → 4H is supported, but this worker was started without the optional 1H mode.</div>';q("#liveDiagnostics").textContent="To validate 1H properly, include it in calibration and start the worker with --include-1h.";return}
  if(d.status!=="ok"){q("#liveStatus").textContent="Unavailable";q("#livePlan").innerHTML='<div class="empty">Live data unavailable.</div>';return}
  q("#liveStatus").textContent="Monitoring · "+tf+" → "+d.confirmation_timeframe;
  q("#marketPrice").textContent=d.latest_close==null?"—":Number(d.latest_close).toFixed(2);
  const skips=d.skip_reason_counts||{};
  const executions=d.ready_execution_counts||{};
  q("#liveDiagnostics").textContent="Scan candidates "+(d.candidate_count??0)+" · fresh primary "+(d.fresh_primary_count??0)+" · READY executions e1/e2/e3 "+(executions["1"]??0)+"/"+(executions["2"]??0)+"/"+(executions["3"]??0)+(Object.keys(skips).length?" · top skip "+Object.entries(skips).sort((a,b)=>b[1]-a[1])[0].join(": "):"");
  const p=d.latest_ready_plan;
  if(!p){
    let reason="No valid Flip & Dip setup is READY in the current scan window.";
    if(d.market_status==="CLOSED_OR_STALE") reason="Market appears closed or the latest market data is stale.";
    else if(d.trading_window_open===false) reason="Market data is available, but your strategy entry window is currently blocked (20:00–23:00 Istanbul).";
    else if(d.news_clear===false) reason="New entries are blocked by the high-impact news blackout.";
    else if(d.demo_session&&d.demo_session.configured&&d.demo_session.status!=="ACTIVE") reason="The configured demo session is "+d.demo_session.status.toLowerCase()+", so new demo plans are not being recorded.";
    q("#livePlan").innerHTML='<div class="empty">'+reason+'</div>';return
  }
  q("#livePlan").innerHTML=`
    <div class="eyebrow">Latest ready plan</div>
    <div class="plan-title ${p.direction}">${p.direction}</div>
    <div class="kvs">
      <div class="kv"><b>Flip zone</b><span>${fmt(p.zone_lower)} – ${fmt(p.zone_upper)}</span></div>
      <div class="kv"><b>Rejection</b><span>${fmt(p.rejection_score)}</span></div>
      <div class="kv"><b>HTF structure</b><span>${p.confirmation_timeframe} ${p.structure_kind||"—"}</span></div>
      <div class="kv"><b>Retest</b><span>${p.retest_at||"—"}</span></div>
      <div class="kv"><b>Execution</b><span>#${p.execution_number||"—"} / 3</span></div>
      <div class="kv"><b>5R target</b><span>${fmt(p.target_5r_price)}</span></div>
      <div class="kv"><b>Entry reference</b><span>${fmt(p.entry_reference_price)}</span></div>
      <div class="kv"><b>Sizing reference</b><span>${fmt(p.sizing_reference_price)}</span></div>
    </div>
    <div class="notice">${p.invalidation_rule}. Intended risk ${p.risk_percent}% · minimum target ${p.minimum_rr}R · partial TP ${p.partial_tp_configured?"configured":"awaiting owner ladder"}.</div>`;
}
async function performance(){
 const balance=Math.max(1,Number(q("#simBalance")?.value||100));
 const risk=Math.max(.1,Math.min(100,Number(q("#simRisk")?.value||5)));
 const d=await get("/api/performance?starting_balance="+encodeURIComponent(balance)+"&risk_percent="+encodeURIComponent(risk));
 q("#candidateCount").textContent=d.candidate_count??0;q("#readyCount").textContent=d.ready_zone_count??0;
 q("#eventCount").textContent=d.independent_event_count??0;q("#secondaryCount").textContent=d.secondary_zone_count??0;
 const o=d.outcomes_primary_events||{};
 q("#outcomes").innerHTML=Object.keys(o).length?'<div class="kvs">'+Object.entries(o).map(([k,v])=>`<div class="kv"><b>${k}</b><span>${v}</span></div>`).join("")+'</div>':'<div class="empty">Run the enhanced calibration to populate outcomes.</div>';
 const breakdown=src=>Object.keys(src||{}).length?'<div class="kvs">'+Object.entries(src).map(([k,v])=>`<div class="kv"><b>${k} · ${v.events} events</b><span>${Object.entries(v.outcomes||{}).map(([s,n])=>s+":"+n).join(" · ")}</span></div>`).join("")+'</div>':'<div class="empty">No data.</div>';
 q("#byTimeframe").innerHTML=breakdown(d.by_timeframe);
 q("#byExecution").innerHTML=breakdown(d.by_execution_number);
 q("#byDirection").innerHTML=breakdown(d.by_direction);
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
async function loadDemoSession(){
 const d=await get("/api/demo/session");
 q("#demoStatus").textContent=d.status||"—";
 q("#demoDetails").textContent=d.configured?((d.name||"Demo")+" · "+d.start+" → "+d.end):"No bounded demo session configured.";
 const s=await get("/api/demo/session/summary");
 q("#demoPlanCount").textContent=s.plan_count??0;
 q("#demoOpenCount").textContent=s.open_count??0;
 q("#demoTerminalCount").textContent=s.terminal_count??0;
 q("#demoOutcomes").textContent=Object.keys(s.outcomes||{}).length?Object.entries(s.outcomes).map(([k,v])=>k+": "+v).join(" · "):"No plans recorded for this session yet.";
}
async function saveDemoSession(){
 const name=q("#demoName").value.trim();
 const start=q("#demoStart").value,end=q("#demoEnd").value;
 if(!name||!start||!end){q("#demoDetails").textContent="Name, start and end are required.";return}
 const d=await post("/api/demo/session",{name,start:new Date(start).toISOString(),end:new Date(end).toISOString()});
 if(d.status==="error"){q("#demoDetails").textContent=d.detail||"Could not save session.";return}
 await loadDemoSession();await health();
}
async function runHistoricalTest(){
 const btn=q("#runHistoricalTest"),start=q("#testFrom").value,end=q("#testTo").value;
 if(!start||!end){q("#testMessage").textContent="Choose both From and To.";return}
 btn.disabled=true;q("#testMessage").textContent="Running the exact Flip & Dip rules on that historical interval…";
 const d=await post("/api/historical-test",{
   start:new Date(start).toISOString(),end:new Date(end).toISOString(),
   starting_balance:Number(q("#testBalance").value||100),
   risk_percent:Number(q("#testRisk").value||5),
   include_1h:q("#test1h").checked
 });
 btn.disabled=false;
 if(d.status==="error"){q("#testMessage").textContent=d.detail||"Historical test failed.";return}
 q("#testMessage").textContent=d.independent_events+" independent events · "+d.historical_news_events_loaded+" high-impact calendar events loaded.";
 q("#testResults").classList.remove("hidden");
 const s=d.account_scenario||{};
 q("#testEndBalance").textContent="$"+Number(s.ending_balance||0).toFixed(2);
 q("#testProfit").textContent=(Number(s.net_profit||0)>=0?"+":"")+"$"+Number(s.net_profit||0).toFixed(2);
 q("#testReturn").textContent=Number(s.return_percent||0).toFixed(1)+"%";
 q("#testDrawdown").textContent=Number(s.max_drawdown_percent||0).toFixed(1)+"%";
 q("#testOutcomes").innerHTML='<div class="kvs">'+Object.entries(d.outcomes||{}).map(([k,v])=>'<div class="kv"><b>'+k+'</b><span>'+v+'</span></div>').join("")+'</div>';
 q("#testTimeframes").innerHTML='<div class="kvs">'+Object.entries(d.timeframes||{}).map(([k,v])=>'<div class="kv"><b>'+k+' → '+v.confirmation_timeframe+'</b><span>'+v.independent_events+' events · '+v.ready_executions+' READY executions</span></div>').join("")+'</div>';
 q("#testSetups").innerHTML=table(d.setups||[]);
 q("#testScenarioNote").textContent=s.note||"";
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
qa(".nav button").forEach(b=>b.onclick=()=>{qa(".nav button").forEach(x=>x.classList.remove("active"));b.classList.add("active");qa(".tab").forEach(x=>x.classList.add("hidden"));q("#"+b.dataset.tab).classList.remove("hidden");if(b.dataset.tab==="test"){};if(b.dataset.tab==="demo")loadDemoSession();if(b.dataset.tab==="plans")plans();if(b.dataset.tab==="performance")performance();if(b.dataset.tab==="history")history();if(b.dataset.tab==="review")health()});
qa(".tf button").forEach(b=>b.onclick=()=>{qa(".tf button").forEach(x=>x.classList.remove("active"));b.classList.add("active");tf=b.dataset.tf;live()});
q("#runSim").onclick=performance;
q("#runHistoricalTest").onclick=runHistoricalTest;
q("#saveDemoSession").onclick=saveDemoSession;
const now=new Date(),day=24*60*60*1000;
const localInput=d=>{const z=new Date(d.getTime()-d.getTimezoneOffset()*60000);return z.toISOString().slice(0,16)};
q("#testTo").value=localInput(now);q("#testFrom").value=localInput(new Date(now-day*7));
q("#demoStart").value=localInput(now);q("#demoEnd").value=localInput(new Date(now+day*7));
health();live();
</script>
</body>
</html>
"""