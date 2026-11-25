"use strict";

const $ = id => document.getElementById(id);
const state = {data:null, tab:"qualification", sort:"total", timer:null, lastFocus:null};
const fmt = new Intl.NumberFormat("en");
const shortId = uuid => uuid ? uuid.slice(0,8) : "unknown";
const label = value => ({required:"Required",preferred:"Preferred",unclear:"Unclear",work_duty:"Work duty",work_context:"Work context",interest_only:"Interest only",ACTIVE:"Active",INACTIVE:"Inactive",UNKNOWN:"Unknown"})[value] || value;
const elt = (tag, className, text) => {const node=document.createElement(tag); if(className)node.className=className; if(text!==undefined)node.textContent=String(text); return node;};
const clear = node => node.replaceChildren();
const localDate = value => {if(!value)return "Date unavailable"; const d=new Date(value+"T00:00:00"); return Number.isNaN(d.getTime())?"Date unavailable":d.toLocaleDateString("en",{day:"numeric",month:"short",year:"numeric"});};
const stamp = value => {if(!value)return "Not recorded"; const d=new Date(value); return Number.isNaN(d.getTime())?"Not recorded":d.toLocaleString("en",{dateStyle:"medium",timeStyle:"short"});};

function params(){
  const query=new URLSearchParams({period:$("period").value,status:$("status-filter").value,search:$("skill-search").value});
  if($("period").value==="custom") {query.set("from",$("date-from").value);query.set("to",$("date-to").value);}
  return query;
}
async function jsonRequest(url, options){
  const response=await fetch(url,{cache:"no-store",...options});
  let data; try{data=await response.json();}catch{throw new Error("The dashboard returned an unreadable response.");}
  if(!response.ok)throw new Error(data.error||`Request failed (${response.status}).`);
  return data;
}
async function loadData(){
  try{
    const data=await jsonRequest("/api/data?"+params());
    state.data=data;
    $("filter-message").classList.remove("error");
    const note=data.filter.missing_dates_excluded;
    const range=data.filter.from&&data.filter.to?`Publication dates: ${localDate(data.filter.from)} – ${localDate(data.filter.to)}.`:"No saved publication dates in this selection.";
    $("filter-message").textContent=range+(note?` ${note} ad${note===1?"":"s"} without a saved publication date excluded.`:"");
    renderData();
  }catch(error){
    $("filter-message").textContent=error.message;
    $("filter-message").classList.add("error");
    if(!state.data){$("dataset-state").textContent="Saved data unavailable"; $("table-empty").hidden=false;}
  }
}
function renderData(){
  const data=state.data;
  $("card-ads").textContent=fmt.format(data.cards.advertisements);
  $("card-skills").textContent=fmt.format(data.cards.qualification_skill_names);
  $("card-groups").textContent=fmt.format(data.cards.alternative_groups);
  $("tab-count-qualification").textContent=data.tables.qualification.length;
  $("tab-count-alternatives").textContent=data.tables.alternatives.length;
  $("tab-count-other").textContent=data.tables.other.length+data.tables.other_alternatives.length;
  $("scope-note").textContent=`${data.coverage.selected_dataset_ads} selected ads in saved dataset. Not complete market coverage.`;
  renderTable();
  renderQuality(data.quality);
}
function tabRows(){
  const t=state.data.tables;
  return state.tab==="other"?[...t.other,...t.other_alternatives]:t[state.tab];
}
function renderTable(){
  if(!state.data)return;
  const validSort=state.tab==="other"?["total","work_duty","work_context","interest_only","name"]:["total","required","preferred","unclear","name"];
  for(const option of $("sort").options)option.hidden=!validSort.includes(option.value);
  if(!validSort.includes(state.sort)){state.sort="total";$("sort").value="total";}
  const headings={qualification:["Applicant skills","Single skills stated as applicant qualifications. One ad counts once per classification."],alternatives:["OR alternatives","Each group is counted together. Its individual skills are not independently mandatory."],other:["Other technical mentions","Duties, work context and interest are shown apart from applicant qualifications."]};
  $("table-title").textContent=headings[state.tab][0];
  $("table-description").textContent=headings[state.tab][1];
  const columns=state.tab==="other"?["Technical mention","Work duty","Work context","Interest only","Total ads"]:[state.tab==="alternatives"?"OR group":"Skill","Required","Preferred","Unclear","Total ads"];
  const head=$("table-head");clear(head);const tr=elt("tr");for(const col of columns)tr.append(elt("th",null,col));head.append(tr);
  const rows=[...tabRows()];
  const rowCount=(row,kind)=>row.counts?.[kind]??(kind==="total"||row.mention_type===kind?row.count:0);
  if(state.sort==="name")rows.sort((a,b)=>(a.skill||a.skills.join(" OR ")).localeCompare(b.skill||b.skills.join(" OR ")));
  else rows.sort((a,b)=>(rowCount(b,state.sort)-rowCount(a,state.sort))||((a.skill||a.skills.join(" OR ")).localeCompare(b.skill||b.skills.join(" OR "))));
  const body=$("table-body");clear(body);
  for(const row of rows){
    const line=elt("tr"); const first=elt("td"); const button=elt("button","row-button",row.skill||row.skills.join(" OR "));
    button.type="button";button.addEventListener("click",()=>showSupport(row,button));first.append(button);line.append(first);
    const count=row.counts||{};
    const values=state.tab==="other" ? (row.skill?[count.work_duty,count.work_context,count.interest_only,count.total]:[row.mention_type==="work_duty"?row.count:0,row.mention_type==="work_context"?row.count:0,row.mention_type==="interest_only"?row.count:0,row.count]) : [count.required,count.preferred,count.unclear,count.total];
    values.forEach((value,i)=>line.append(elt("td",i===3?"count-strong":null,fmt.format(value||0))));body.append(line);
  }
  $("table-empty").hidden=rows.length>0;
  $("table-empty").querySelector("h3").textContent=state.data.coverage.selected_dataset_ads===0?"No statistics are available yet":state.data.cards.advertisements===0?"No collected advertisements match these filters":"No mentions in this category";
  $("table-empty").querySelector("p").textContent=state.data.coverage.selected_dataset_ads===0?"Run an update to begin.":state.data.cards.advertisements===0?"Try another period, status or skill search.":"Try another tab or change the skill search.";
  $("table-wrap").hidden=rows.length===0;
}
function showSupport(row,focus){
  $("drawer-label").textContent="Supporting advertisements";
  state.lastFocus=focus;
  const title=row.skill||row.skills.join(" OR ");
  $("drawer-title").textContent=title;
  $("drawer-description").textContent=row.skills?"Explicit alternatives are kept as one group.":"Saved quotations behind this count.";
  const list=$("drawer-list");clear(list);
  const supporters=state.data.support[row.id]||[];
  if(!supporters.length)list.append(elt("p","notice","No displayable supporting quotations are available."));
  for(const ad of supporters){
    const card=elt("article","support-card");
    card.append(elt("h3",null,ad.title||`Advertisement ${shortId(ad.uuid)}`));
    card.append(elt("p","uuid",ad.uuid));
    const meta=elt("div","support-meta");
    [localDate(ad.publication_date),`Last saved status: ${label(ad.activity_status)}`,label(ad.classification),label(ad.mention_type)].forEach(v=>meta.append(elt("span","pill",v)));
    card.append(meta);
    if(ad.skill_evidence){const q=elt("blockquote",null,ad.skill_evidence);card.append(q);}else card.append(elt("p","notice","Quotation withheld because a contact-data pattern was detected."));
    if(ad.classification_context){card.append(elt("div","metric-label","CLASSIFICATION CONTEXT"));card.append(elt("blockquote","context",ad.classification_context));}
    const link=elt("a",null,"Open original NAV advertisement ↗");link.href=ad.source_url;link.target="_blank";link.rel="noopener noreferrer";card.append(link);list.append(card);
  }
  openDrawer();
}
async function showCases(){
  state.lastFocus=$("view-cases");
  $("drawer-label").textContent="Update details";
  $("drawer-title").textContent="Ads to review";
  $("drawer-description").textContent="Failed extractions and advertisements held for review in the saved dataset.";
  const list=$("drawer-list");clear(list);
  const content=elt("div",null,"Loading cases…");list.append(content);
  openDrawer();
  try{
    const {cases}=await jsonRequest("/api/cases");
    clear(content);
    if(!cases.length)content.append(elt("p",null,"There are no saved cases to review."));
    for(const ad of cases){
      const card=elt("article","support-card");
      card.append(elt("span","pill",ad.status),elt("h3",null,ad.title||"Advertisement"),elt("p","uuid",ad.uuid),elt("p",null,ad.reason));
      if(ad.previous_validation_failed)card.append(elt("strong",null,"Earlier AI answer for this version failed validation"));
      for(const detail of ad.details||[])card.append(elt("p",null,detail));
      const link=elt("a",null,"View advertisement on NAV ↗");
      link.href="https://arbeidsplassen.nav.no/stillinger/stilling/"+encodeURIComponent(ad.uuid);
      link.target="_blank";link.rel="noopener noreferrer";card.append(link);content.append(card);
    }
  }catch(error){content.textContent=error.message;}
}
function openDrawer(){
  $("drawer-backdrop").hidden=false;$("drawer").hidden=false;document.body.style.overflow="hidden";$("close-drawer").focus();
}
function closeDrawer(){$("drawer").hidden=true;$("drawer-backdrop").hidden=true;document.body.style.overflow="";state.lastFocus?.focus();}
function renderQuality(q){
  const root=$("quality-content");clear(root);
  const grid=elt("div","quality-grid");
  const entries=[[q.auto_contact_checked||0,"Newer automatic contact check"],[q.earlier_cleaner_accepted||0,"Earlier cleaner captures accepted for this dataset"],[q.queue_remaining??"—","Unfinished discovery/processing queue"]];
  for(const [count,labelText] of entries){const cell=elt("div","quality-cell");cell.append(elt("strong",null,count));cell.append(elt("span",null,labelText));grid.append(cell);}root.append(grid);
  const counts=q.status_counts||{};
  root.append(elt("p",null,`Selected: ${counts.current||0} · Blocked: ${counts.blocked||0} · Failed: ${counts.failed||0} · Stale: ${counts.stale||0} · Pending: ${counts.pending||0}. Feed phase: ${q.scan_phase||"unavailable"}.`));
  const review=q.skill_review;
  if(review){root.append(elt("p",null,`${review.decision_count} provisional source-review decisions affect the displayed skill counts. Original model outputs remain unchanged. ${review.unapplied_uuids.length} review records no longer match the selected ad version.`));}
  root.append(elt("p",null,"Contact screening and structural quotation checks do not prove extraction accuracy. Earlier cleaner captures were accepted for this project dataset and are included in the displayed counts. A status describes the last saved NAV check, not a live check. An inactive advertisement's original NAV page may no longer be available. Publication filters use saved dates; historical coverage is incomplete."));
}
function updateStatus(status){
  const button=$("run-update");button.disabled=!!status.running;
  button.firstChild.textContent=status.running?"Update in progress ":"Run update ";
  const last=status.last;
  $("last-update").textContent=last?.finished_at_utc?`Last update: ${stamp(last.finished_at_utc)}`:"Last update: not run from this dashboard";
  const q=status.quality||{};
  $("dataset-state").textContent=status.running?"Update running · saved results available":q.queue_remaining?`${fmt.format(q.queue_remaining)} queued · work remains`:"Saved results available";
  $("update-details").hidden=!last||status.running;
  if(status.running){$("update-status").textContent=`${last?.stage||"Working"} · ${last?.pages||0} pages · ${last?.details||0} details. Saved results remain visible.`;return;}
  if(!last){$("update-status").textContent="Saved results stay available while an update runs.";return;}
  const report=last.report||{};
  const names={finished_with_cases:"Update finished",caught_up:"Update complete",no_updates_found:"No new updates",partial_pending:"Progress saved — work remains",discovery_failed:"Update failed — progress saved",processing_failed:"Update failed — progress saved",failed:"Update failed"};
  const completeWithoutNewResults=last.status==="caught_up"&&report.processed===0;
  const held=report.blocked>0?` · ${report.blocked} held for review`:"";
  const earlier=report.earlier_failures||0;
  const previous=earlier ? ` · ${earlier} earlier ${earlier===1?"failure needs":"failures need"} review` : "";
  if(last.status==="processing_failed" && report.earlier_failures==null && report.extraction_requests===0){
    names.processing_failed="Saved run reported a failure · no new AI request";
  }
  $("update-status").textContent=last.error?`${names[last.status]||"Update failed"}: ${last.error}`:(completeWithoutNewResults?"Update complete — no new skill results":names[last.status]||last.status)+held+previous;
  $("update-detail-text").textContent=last.error||`Feed pages: ${report.pages??0} · Detail requests: ${report.details??0} · Extraction requests: ${report.extraction_requests??0} · Published: ${report.processed??0} · Resolved without extraction: ${report.reused??0} · Blocked during run: ${report.blocked??0} · ${report.earlier_failures==null?"Failed":"New failures"}: ${report.failed??0}${report.earlier_failures==null?"":` · Earlier failures: ${earlier}`} · Remaining: ${report.pending??0}. ${report.stop_reason&&report.stop_reason!==last.status?`Stop reason: ${report.stop_reason}.`:""}`;
}
async function pollStatus(){
  try{const status=await jsonRequest("/api/status");const wasRunning=!!state.wasRunning;state.wasRunning=status.running;updateStatus(status);if(wasRunning&&!status.running)await loadData();}
  catch(error){$("update-status").textContent=`Status unavailable: ${error.message}`;}
}
async function runUpdate(){
  const button=$("run-update");button.disabled=true;$("update-status").textContent="Starting update…";
  try{const status=await jsonRequest("/api/update",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});state.wasRunning=true;updateStatus(status);}
  catch(error){button.disabled=false;$("update-status").textContent=`Update did not start: ${error.message}`;}
}
function init(){
  $("period").addEventListener("change",()=>{$("custom-dates").hidden=$("period").value!=="custom";if($("period").value!=="custom")loadData();});
  for(const id of ["date-from","date-to","status-filter"])$(id).addEventListener("change",loadData);
  let searchTimer;$("skill-search").addEventListener("input",()=>{clearTimeout(searchTimer);searchTimer=setTimeout(loadData,220);});
  $("sort").addEventListener("change",()=>{state.sort=$("sort").value;renderTable();});
  document.querySelectorAll(".tab").forEach(button=>button.addEventListener("click",()=>{state.tab=button.dataset.tab;document.querySelectorAll(".tab").forEach(t=>{t.classList.toggle("active",t===button);t.setAttribute("aria-selected",String(t===button));});renderTable();}));
  $("view-cases").addEventListener("click",showCases);
  $("run-update").addEventListener("click",runUpdate);$("close-drawer").addEventListener("click",closeDrawer);$("drawer-backdrop").addEventListener("click",closeDrawer);
  document.addEventListener("keydown",event=>{if(event.key==="Escape"&&!$("drawer").hidden)closeDrawer();});
  loadData();pollStatus();state.timer=setInterval(pollStatus,2000);
}
init();
