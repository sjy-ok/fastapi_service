const state = { page: "assignments", assignments: [], personnels: [], tms: [], pls: [], departments: [] };
const $ = (selector) => document.querySelector(selector);
const resources = {
  "tm-groups": { title: "TM", items: "tms", path: "/tm-groups", leader: true },
  "pl-groups": { title: "PL", items: "pls", path: "/pl-groups", leader: true },
  departments: { title: "Department", items: "departments", path: "/departments", leader: false },
};

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { "Content-Type": "application/json", ...(options.headers || {}) } });
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || `请求失败 (${response.status})`); }
  return response.status === 204 ? null : response.json();
}
function esc(value = "") { return String(value).replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"})[c]); }
function toast(message, error = false) { const el = $("#toast"); el.textContent = message; el.className = `toast${error ? " error" : ""}`; setTimeout(() => el.classList.add("hidden"), 2600); }
function openModal(html) { $("#modalContent").innerHTML = html; $("#modalBackdrop").classList.remove("hidden"); }
function closeModal() { $("#modalBackdrop").classList.add("hidden"); }
function fmt(value) { return value ? new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "至今"; }
function fmtDate(value) { return value || "至今"; }
function toLocal(value) { if (!value) return ""; const date = new Date(value); date.setMinutes(date.getMinutes() - date.getTimezoneOffset()); return date.toISOString().slice(0, 16); }
function personLabel(p) { return [p.w3_account, p.name, p.employee_id].filter(Boolean).join(" / "); }

async function load() {
  try {
    [state.assignments, state.personnels, state.tms, state.pls, state.departments] = await Promise.all([
      api("/personnel-assignments?limit=200"), api("/personnels?limit=200"), api("/tm-groups?limit=200"), api("/pl-groups?limit=200"), api("/departments?limit=200"),
    ]);
    $("#assignmentCount").textContent = state.assignments.length; $("#personnelCount").textContent = state.personnels.length;
    $("#groupCount").textContent = state.tms.length + state.pls.length; $("#departmentCount").textContent = state.departments.length;
    render();
  } catch (error) { toast(error.message, true); }
}

function render() {
  const query = $("#searchInput").value.toLowerCase().trim();
  if (state.page === "assignments") renderAssignments(query);
  else if (state.page === "personnels") renderPersonnels(query);
  else renderOrganizations(query);
}
function setTable(head, rows, colspan) {
  $("#tableHead").innerHTML = `<tr>${head.map(x => `<th>${x}</th>`).join("")}<th></th></tr>`;
  $("#dataTable").innerHTML = rows || `<tr><td colspan="${colspan}" class="empty">暂无数据</td></tr>`;
}
function actions(type, id) { return `<td class="actions"><button class="more" data-type="${type}" data-id="${id}">•••</button></td>`; }

function renderAssignments(query) {
  const items = state.assignments.filter(x => JSON.stringify(x).toLowerCase().includes(query));
  setTable(["人员", "TM", "PL", "Department", "开始", "结束", "操作人", "录入时间", "备注"], items.map(x => `<tr>
    <td><div class="person"><span class="avatar">${esc((x.personnel.name || x.personnel.w3_account)[0])}</span><div><strong>${esc(x.personnel.name || "—")}</strong><small>${esc(x.personnel.w3_account)}${x.personnel.employee_id ? ` · ${esc(x.personnel.employee_id)}` : ""}</small></div></div></td>
    <td>${esc(x.tm_group?.name || "—")}</td><td>${esc(x.pl_group?.name || "—")}</td><td>${esc(x.department?.name || "—")}</td>
    <td>${fmtDate(x.start_time)}</td><td>${fmtDate(x.end_time)}</td><td>${esc(x.creator || "—")}</td><td>${fmt(x.insert_time)}</td><td title="${esc(x.notes || "")}">${esc(x.notes || "—")}</td>${actions("assignment", x.id)}</tr>`).join(""), 10);
  $("#resultCount").textContent = `共 ${items.length} 条记录`;
}
function renderPersonnels(query) {
  const items = state.personnels.filter(x => personLabel(x).toLowerCase().includes(query));
  setTable(["人员", "W3 账号", "员工工号"], items.map(x => `<tr><td><div class="person"><span class="avatar">${esc((x.name || x.w3_account)[0])}</span><strong>${esc(x.name || "—")}</strong></div></td><td>${esc(x.w3_account)}</td><td>${esc(x.employee_id || "—")}</td>${actions("personnel", x.id)}</tr>`).join(""), 4);
  $("#resultCount").textContent = `共 ${items.length} 人`;
}
function renderOrganizations(query) {
  const config = resources[state.page]; const items = state[config.items].filter(x => x.name.toLowerCase().includes(query));
  const heads = config.leader ? ["名称", "Leader"] : ["名称"];
  setTable(heads, items.map(x => `<tr><td><strong>${esc(x.name)}</strong></td>${config.leader ? `<td>${esc(state.personnels.find(p => p.id === x.leader_personnel_id)?.name || "—")}</td>` : ""}${actions("organization", x.id)}</tr>`).join(""), heads.length + 1);
  $("#resultCount").textContent = `共 ${items.length} 项`;
}

function selectOptions(items, selected, label) { return `<option value="">${label}</option>` + items.map(x => `<option value="${x.id}" ${x.id === selected ? "selected" : ""}>${esc(x.name || personLabel(x))}</option>`).join(""); }
function searchable(name, label, items, selected, kind, required = false) {
  const item = items.find(x => x.id === selected); const current = item ? (kind === "personnels" ? personLabel(item) : item.name) : "";
  return `<div class="field${name === "personnel" ? " full" : ""}"><label>${label}${required ? " *" : ""}</label><div class="remote-select"><input autocomplete="off" name="${name}_label" data-remote="${kind}" value="${esc(current)}" placeholder="输入关键词搜索并选择" ${required ? "required" : ""}><button type="button" class="select-toggle" aria-label="展开">⌄</button><div class="select-menu hidden"></div></div></div>`;
}
function resolveExisting(kind, label, required = false) {
  if (!label.trim() && !required) return null;
  const items = kind === "personnels" ? state.personnels : state[resources[kind].items];
  const found = items.find(x => (kind === "personnels" ? personLabel(x) : x.name) === label.trim());
  if (!found) throw new Error(`${required ? "人员" : resources[kind].title} 必须从搜索结果中选择`);
  return found.id;
}
function merge(existing, incoming) { return [...new Map([...existing, ...incoming].map(x => [x.id, x])).values()]; }
function bindRemoteSearch(root) {
  root.querySelectorAll("[data-remote]").forEach(input => { let timer; let controller; const box = input.closest(".remote-select"); const menu = box.querySelector(".select-menu");
    const showItems = items => { menu.innerHTML = items.length ? items.map(x => { const label = input.dataset.remote === "personnels" ? personLabel(x) : x.name; return `<button type="button" class="select-option" data-value="${esc(label)}"><strong>${esc(label)}</strong>${input.dataset.remote === "personnels" && x.name ? `<small>${esc(x.w3_account)}</small>` : ""}</button>`; }).join("") : '<div class="select-empty">没有匹配的已有数据</div>'; menu.classList.remove("hidden"); };
    const search = async () => { if (controller) controller.abort(); const kind = input.dataset.remote; controller = new AbortController(); const query = encodeURIComponent(input.value.trim());
      const path = kind === "personnels" ? `/personnels?q=${query}&limit=50` : `${resources[kind].path}?q=${query}&limit=50`;
      menu.innerHTML = '<div class="select-empty">正在搜索…</div>'; menu.classList.remove("hidden");
      try { const items = await api(path, { signal: controller.signal }); if (kind === "personnels") state.personnels = merge(state.personnels, items); else state[resources[kind].items] = merge(state[resources[kind].items], items); showItems(items); }
      catch (error) { if (error.name !== "AbortError") { menu.classList.add("hidden"); toast(error.message, true); } }
    };
    input.addEventListener("focus", search);
    input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(search, 300); });
    box.querySelector(".select-toggle").addEventListener("click", () => { input.focus(); search(); });
    menu.addEventListener("mousedown", event => { const option = event.target.closest(".select-option"); if (!option) return; event.preventDefault(); input.value = option.dataset.value; menu.classList.add("hidden"); input.dispatchEvent(new Event("change")); });
    input.addEventListener("blur", () => setTimeout(() => menu.classList.add("hidden"), 120));
  });
}

function assignmentForm(item = null) {
  openModal(`<h2>${item ? "编辑人员变动" : "新增人员变动"}</h2><p class="lead">所有关联字段必须从已有基础数据中搜索并选择。</p>
  <form id="recordForm"><div class="form-grid">${searchable("personnel", "人员", state.personnels, item?.personnel.id, "personnels", true)}
  ${searchable("tm", "TM", state.tms, item?.tm_group?.id, "tm-groups")}${searchable("pl", "PL", state.pls, item?.pl_group?.id, "pl-groups")}${searchable("department", "Department", state.departments, item?.department?.id, "departments")}
  <div class="field"><label>开始日期</label><input name="start_time" type="date" value="${item ? (item.start_time || "") : "1900-01-01"}"></div><div class="field"><label>结束日期（留空表示至今）</label><input name="end_time" type="date" value="${item?.end_time || ""}"></div>
  <div class="field"><label>操作人</label><input name="creator" maxlength="64" value="${esc(item?.creator || "")}"></div><div class="field full"><label>备注</label><textarea name="notes">${esc(item?.notes || "")}</textarea></div></div>
  <div class="form-actions"><button type="button" class="secondary" data-close>取消</button><button class="primary">保存</button></div></form>`);
  bindRemoteSearch($("#recordForm"));
  $("#recordForm").addEventListener("submit", async event => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.target));
    try {
      const payload = { personnel_id: resolveExisting("personnels", data.personnel_label, true), tm_group_id: resolveExisting("tm-groups", data.tm_label), pl_group_id: resolveExisting("pl-groups", data.pl_label), department_id: resolveExisting("departments", data.department_label),
        start_time: data.start_time || null, end_time: data.end_time || null, creator: data.creator || null, notes: data.notes || null };
      await api(item ? `/personnel-assignments/${item.id}` : "/personnel-assignments", { method: item ? "PATCH" : "POST", body: JSON.stringify(payload) });
      closeModal(); toast(item ? "记录已更新" : "记录已创建"); await load();
    } catch (error) { toast(error.message, true); }
  });
}

function personnelForm(item = null) {
  openModal(`<h2>${item ? "编辑人员" : "新增人员"}</h2><p class="lead">人员基础数据不包含任何组织信息。</p><form id="personForm"><div class="form-grid">
    <div class="field"><label>W3 账号 *</label><input name="w3_account" required value="${esc(item?.w3_account || "")}"></div><div class="field"><label>姓名</label><input name="name" value="${esc(item?.name || "")}"></div><div class="field"><label>员工工号</label><input name="employee_id" value="${esc(item?.employee_id || "")}"></div>
    </div><div class="form-actions"><button type="button" class="secondary" data-close>取消</button><button class="primary">保存</button></div></form>`);
  $("#personForm").addEventListener("submit", async event => { event.preventDefault(); const payload = Object.fromEntries(new FormData(event.target)); payload.name = payload.name || null; payload.employee_id = payload.employee_id || null;
    try { await api(item ? `/personnels/${item.id}` : "/personnels", { method: item ? "PATCH" : "POST", body: JSON.stringify(payload) }); closeModal(); toast("人员已保存"); await load(); } catch (error) { toast(error.message, true); }
  });
}

function organizationForm(item = null) {
  const config = resources[state.page]; openModal(`<h2>${item ? "编辑" : "新增"}${config.title}</h2><form id="orgForm"><div class="form-grid"><div class="field"><label>名称 *</label><input name="name" required value="${esc(item?.name || "")}"></div>
  ${config.leader ? searchable("leader", "Leader", state.personnels, item?.leader_personnel_id, "personnels") : ""}</div><div class="form-actions"><button type="button" class="secondary" data-close>取消</button><button class="primary">保存</button></div></form>`);
  bindRemoteSearch($("#orgForm"));
  $("#orgForm").addEventListener("submit", async event => { event.preventDefault(); const payload = Object.fromEntries(new FormData(event.target)); if (config.leader) { payload.leader_personnel_id = resolveExisting("personnels", payload.leader_label); delete payload.leader_label; }
    try { await api(item ? `${config.path}/${item.id}` : config.path, { method: item ? "PATCH" : "POST", body: JSON.stringify(payload) }); closeModal(); toast(`${config.title} 已保存`); await load(); } catch (error) { toast(error.message, true); }
  });
}
async function remove(type, item) {
  if (!confirm("确定删除这条数据吗？被其他数据引用时系统会阻止删除。")) return;
  const path = type === "assignment" ? `/personnel-assignments/${item.id}` : type === "personnel" ? `/personnels/${item.id}` : `${resources[state.page].path}/${item.id}`;
  try { await api(path, { method: "DELETE" }); toast("删除成功"); await load(); } catch (error) { toast(error.message, true); }
}

let pageSearchTimer;
let pageSearchController;
function schedulePageSearch() {
  clearTimeout(pageSearchTimer); if (pageSearchController) pageSearchController.abort();
  pageSearchTimer = setTimeout(async () => {
    const query = encodeURIComponent($("#searchInput").value.trim()); pageSearchController = new AbortController();
    const path = state.page === "assignments" ? `/personnel-assignments?q=${query}&limit=200` : state.page === "personnels" ? `/personnels?q=${query}&limit=200` : `${resources[state.page].path}?q=${query}&limit=200`;
    try { const items = await api(path, { signal: pageSearchController.signal });
      if (state.page === "assignments") state.assignments = items; else if (state.page === "personnels") state.personnels = merge(state.personnels, items); else state[resources[state.page].items] = merge(state[resources[state.page].items], items);
      render();
    } catch (error) { if (error.name !== "AbortError") toast(error.message, true); }
  }, 300);
}

$("#navigation").addEventListener("click", event => { const button = event.target.closest("[data-page]"); if (!button) return; state.page = button.dataset.page;
  document.querySelectorAll("[data-page]").forEach(x => x.classList.toggle("active", x === button)); const config = resources[state.page];
  $("#pageTitle").textContent = state.page === "assignments" ? "人员变动" : state.page === "personnels" ? "人员" : config.title;
  $("#pageSubtitle").textContent = state.page === "assignments" ? "维护人员组织变动记录" : "维护基础数据";
  $("#createButton").innerHTML = `<span>＋</span> ${state.page === "assignments" ? "新增记录" : "新增"}`; $("#searchInput").value = ""; render();
});
$("#dataTable").addEventListener("click", event => { const button = event.target.closest("[data-type]"); if (!button) return; document.querySelectorAll(".action-menu").forEach(x => x.remove());
  const type = button.dataset.type; const id = Number(button.dataset.id); const item = type === "assignment" ? state.assignments.find(x => x.id === id) : type === "personnel" ? state.personnels.find(x => x.id === id) : state[resources[state.page].items].find(x => x.id === id);
  const menu = document.createElement("div"); menu.className = "action-menu"; menu.innerHTML = '<button data-action="edit">编辑</button><button data-action="delete">删除</button>';
  menu.addEventListener("click", click => { if (click.target.dataset.action === "delete") remove(type, item); else if (type === "assignment") assignmentForm(item); else if (type === "personnel") personnelForm(item); else organizationForm(item); menu.remove(); }); button.parentElement.appendChild(menu);
});
$("#createButton").addEventListener("click", () => state.page === "assignments" ? assignmentForm() : state.page === "personnels" ? personnelForm() : organizationForm());
$("#refreshButton").addEventListener("click", load); $("#searchInput").addEventListener("input", schedulePageSearch);
document.addEventListener("click", event => { if (event.target.matches("[data-close]")) closeModal(); });
$("#modalBackdrop").addEventListener("click", event => { if (event.target.id === "modalBackdrop") closeModal(); });
load();
