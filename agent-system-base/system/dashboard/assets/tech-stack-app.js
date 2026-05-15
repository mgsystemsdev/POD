/**
 * Standalone Tech Stack composer (ES module). Catalog: tech-stack-catalog.js
 */
import { CATALOG, DOMAIN_ORDER } from "/dashboard-assets/tech-stack-catalog.js";

const DOMAINS = CATALOG.DOMAINS;
const PRESETS = CATALOG.PRESETS;

const SEP = "\x01";
const key = (d, c, i) => d + SEP + c + SEP + i;

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function selectionsToPayload(set) {
  const selections = {};
  set.forEach((k) => {
    const parts = k.split(SEP);
    if (parts.length !== 3) return;
    const [d, c, item] = parts;
    if (!selections[d]) selections[d] = {};
    if (!selections[d][c]) selections[d][c] = [];
    selections[d][c].push(item);
  });
  return { selections };
}

function hydrateFromPayload(obj, set) {
  set.clear();
  if (!obj || !obj.selections || typeof obj.selections !== "object") return;
  Object.entries(obj.selections).forEach(([d, cats]) => {
    if (!cats || typeof cats !== "object") return;
    Object.entries(cats).forEach(([c, items]) => {
      if (!Array.isArray(items)) return;
      items.forEach((item) => set.add(key(d, c, item)));
    });
  });
}

function findCategoryForItem(domain, itemName) {
  const dc = DOMAINS[domain]?.categories || {};
  for (const [cat, arr] of Object.entries(dc)) {
    if (arr.includes(itemName)) return cat;
  }
  return null;
}

function applyPreset(domain, presetName, set) {
  const items = (PRESETS[domain] || {})[presetName] || [];
  items.forEach((item) => {
    const c = findCategoryForItem(domain, item);
    if (c) set.add(key(domain, c, item));
  });
}

function generateMarkdown(set, projectName) {
  let total = 0;
  set.forEach(() => {
    total += 1;
  });
  let md = `# Tech Stack${projectName ? ` — ${projectName}` : ""}\n\n> ${total} technologies selected\n\n`;
  DOMAIN_ORDER.forEach((dN) => {
    const dD = DOMAINS[dN];
    const blocks = [];
    Object.entries(dD.categories).forEach(([cat, items]) => {
      const sel = items.filter((i) => set.has(key(dN, cat, i)));
      if (sel.length) blocks.push({ cat, sel });
    });
    if (!blocks.length) return;
    md += `---\n\n## ${dD.icon} ${dN}\n\n`;
    blocks.forEach(({ cat, sel }) => {
      md += `### ${cat}\n\n`;
      sel.forEach((s) => {
        md += `- [x] ${s}\n`;
      });
      md += "\n";
    });
  });
  return md;
}

async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined && body !== null) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const r = await fetch("/api" + path, opts);
  if (!r.ok) {
    const raw = await r.text();
    let msg = raw;
    try {
      const j = JSON.parse(raw);
      if (j && j.detail != null) msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch (_) {
      /* ignore */
    }
    throw new Error(msg);
  }
  if (r.status === 204) return null;
  const ct = r.headers.get("content-type") || "";
  if (ct.indexOf("application/json") === -1) return null;
  return r.json();
}

function toast(msg, ok = true) {
  const el = document.createElement("div");
  el.textContent = msg;
  Object.assign(el.style, {
    position: "fixed",
    bottom: "20px",
    right: "20px",
    padding: "12px 18px",
    borderRadius: "8px",
    fontSize: "13px",
    zIndex: "9999",
    background: ok ? "#064e3b" : "#7f1d1d",
    color: "#fff",
    border: "1px solid " + (ok ? "#10b981" : "#ef4444"),
  });
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2800);
}

function mount() {
  const root = document.getElementById("ts-root");
  if (!root) return;

  const state = {
    activeDomain: DOMAIN_ORDER[0],
    selected: new Set(),
    search: "",
    projectName: "",
    collapsed: new Set(),
    projects: [],
    projectId: "",
    copied: false,
  };

  const qs = new URLSearchParams(location.search);
  const prePid = qs.get("project");

  const shell = document.createElement("div");
  shell.style.cssText =
    "display:flex;min-height:calc(100vh - 48px);background:#07090F;color:#E2E8F0;font-family:system-ui,sans-serif;overflow:hidden;";
  root.appendChild(shell);

  const sidebar = document.createElement("div");
  sidebar.style.cssText =
    "width:200px;min-width:200px;background:#0B0E18;border-right:1px solid #161B2B;display:flex;flex-direction:column;overflow:hidden;";
  shell.appendChild(sidebar);

  const main = document.createElement("div");
  main.style.cssText = "flex:1;display:flex;flex-direction:column;overflow:hidden;";
  shell.appendChild(main);

  function renderSidebar() {
    sidebar.innerHTML = "";
    const head = document.createElement("div");
    head.style.cssText = "padding:14px;border-bottom:1px solid #161B2B;";
    head.innerHTML =
      '<div style="font-size:14px;font-weight:700;color:#F8FAFC">Tech Stack</div><div style="font-size:10px;color:#475569;margin-top:2px">select · compose · export</div>';
    sidebar.appendChild(head);
    const scroll = document.createElement("div");
    scroll.style.cssText = "flex:1;overflow-y:auto;padding:6px;";
    DOMAIN_ORDER.forEach((name) => {
      const d = DOMAINS[name];
      let c = 0;
      state.selected.forEach((k) => {
        if (k.split(SEP)[0] === name) c += 1;
      });
      const btn = document.createElement("button");
      btn.type = "button";
      const active = state.activeDomain === name;
      btn.style.cssText = [
        "width:100%",
        "background:" + (active ? d.accent + "12" : "transparent"),
        "border:1px solid " + (active ? d.accent + "25" : "transparent"),
        "border-radius:7px",
        "padding:9px 10px",
        "margin-bottom:1px",
        "cursor:pointer",
        "color:inherit",
        "text-align:left",
        "display:flex",
        "justify-content:space-between",
        "align-items:center",
      ].join(";");
      const left = document.createElement("span");
      left.innerHTML = `<span style="font-size:14px">${d.icon}</span> <span style="font-size:12px;font-weight:${active ? 600 : 400};color:${active ? "#F8FAFC" : "#8896AB"}">${esc(name)}</span>`;
      btn.appendChild(left);
      if (c > 0) {
        const badge = document.createElement("span");
        badge.textContent = String(c);
        badge.style.cssText = `font-size:10px;font-weight:700;color:${d.accent};background:${d.accent}18;padding:1px 6px;border-radius:8px`;
        btn.appendChild(badge);
      }
      btn.onclick = () => {
        state.activeDomain = name;
        state.search = "";
        renderAll();
      };
      scroll.appendChild(btn);
    });
    sidebar.appendChild(scroll);

    const foot = document.createElement("div");
    foot.style.cssText = "padding:10px;border-top:1px solid #161B2B;";
    const n = state.selected.size;
    foot.innerHTML = `<div style="font-size:11px;font-weight:600;color:${n ? "#F59E0B" : "#475569"};text-align:center;margin-bottom:6px">${n} selected</div>`;
    const row = document.createElement("div");
    row.style.cssText = "display:flex;gap:4px;";
    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.textContent = state.copied ? "Copied!" : "Copy MD";
    copyBtn.style.cssText =
      "flex:1;background:" +
      (state.copied ? "#059669" : "#151A28") +
      ";border:1px solid #1E293B;border-radius:5px;padding:5px;cursor:pointer;color:" +
      (state.copied ? "#fff" : "#8896AB") +
      ";font-size:10px;font-weight:600";
    copyBtn.onclick = async () => {
      try {
        await navigator.clipboard.writeText(generateMarkdown(state.selected, state.projectName));
        state.copied = true;
        renderAll();
        setTimeout(() => {
          state.copied = false;
          renderAll();
        }, 2000);
      } catch {
        toast("Copy failed — use HTTPS or localhost", false);
      }
    };
    const resetBtn = document.createElement("button");
    resetBtn.type = "button";
    resetBtn.textContent = "Reset";
    resetBtn.style.cssText =
      "background:#151A28;border:1px solid #1E293B;border-radius:5px;padding:5px 8px;cursor:pointer;color:#8896AB;font-size:10px;font-weight:600";
    resetBtn.onclick = () => {
      state.selected.clear();
      state.projectName = "";
      state.search = "";
      renderAll();
    };
    row.appendChild(copyBtn);
    row.appendChild(resetBtn);
    foot.appendChild(row);
    sidebar.appendChild(foot);
  }

  function renderMain() {
    main.innerHTML = "";
    const domain = DOMAINS[state.activeDomain];
    const sl = state.search.toLowerCase();

    const top = document.createElement("div");
    top.style.cssText =
      "padding:10px 16px;border-bottom:1px solid #161B2B;display:flex;gap:8px;align-items:center;background:#090C14;flex-wrap:wrap;";
    top.innerHTML = `<span style="font-size:18px">${domain.icon}</span><span style="font-size:15px;font-weight:700;color:#F8FAFC;flex:1">${esc(state.activeDomain)}</span>`;

    const projWrap = document.createElement("label");
    projWrap.style.cssText = "display:flex;align-items:center;gap:6px;font-size:11px;color:#8896AB;";
    projWrap.innerHTML = "Project ";
    const projSel = document.createElement("select");
    projSel.style.cssText =
      "background:#111525;border:1px solid #1C2235;border-radius:5px;padding:5px 8px;color:#E2E8F0;font-size:11px;min-width:140px";
    const o0 = document.createElement("option");
    o0.value = "";
    o0.textContent = "— select —";
    projSel.appendChild(o0);
    state.projects.forEach((p) => {
      const o = document.createElement("option");
      o.value = String(p.id);
      o.textContent = p.name || p.slug;
      if (String(p.id) === String(state.projectId)) o.selected = true;
      projSel.appendChild(o);
    });
    projSel.onchange = async () => {
      state.projectId = projSel.value;
      if (!state.projectId) return;
      try {
        const p = await api("GET", "/projects/" + state.projectId);
        hydrateFromPayload(p.tech_stack, state.selected);
        state.projectName = p.name || "";
        renderAll();
      } catch (e) {
        toast(e.message, false);
      }
    };
    projWrap.appendChild(projSel);
    top.appendChild(projWrap);

    const pn = document.createElement("input");
    pn.type = "text";
    pn.placeholder = "Label…";
    pn.value = state.projectName;
    pn.style.cssText =
      "background:#111525;border:1px solid #1C2235;border-radius:5px;padding:5px 9px;color:#E2E8F0;font-size:11px;width:120px";
    pn.oninput = () => {
      state.projectName = pn.value;
    };
    top.appendChild(pn);

    const search = document.createElement("input");
    search.type = "text";
    search.placeholder = "Search…";
    search.value = state.search;
    search.style.cssText =
      "background:#111525;border:1px solid #1C2235;border-radius:5px;padding:5px 9px;color:#E2E8F0;font-size:11px;width:130px";
    search.oninput = () => {
      state.search = search.value;
      renderMain();
    };
    top.appendChild(search);

    const addBtn = document.createElement("button");
    addBtn.type = "button";
    addBtn.textContent = "Add to project";
    addBtn.style.cssText =
      "background:#4f46e5;border:1px solid #6366f1;border-radius:6px;padding:6px 12px;cursor:pointer;color:#fff;font-size:11px;font-weight:600";
    addBtn.disabled = !state.projectId;
    addBtn.onclick = async () => {
      if (!state.projectId) {
        toast("Select a project first", false);
        return;
      }
      try {
        await api("PUT", "/projects/" + state.projectId + "/tech-stack", selectionsToPayload(state.selected));
        toast("Saved to project", true);
      } catch (e) {
        toast(e.message, false);
      }
    };
    top.appendChild(addBtn);

    main.appendChild(top);

    const content = document.createElement("div");
    content.style.cssText = "flex:1;overflow-y:auto;padding:10px 16px 40px;";

    const presets = PRESETS[state.activeDomain];
    if (presets) {
      const box = document.createElement("div");
      box.style.cssText =
        "margin-bottom:10px;padding:10px 12px;background:#0C1019;border:1px solid #161B2B;border-radius:8px;";
      box.innerHTML =
        '<div style="font-size:10px;color:#475569;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.08em;font-weight:700">Quick Patterns</div>';
      const wrap = document.createElement("div");
      wrap.style.cssText = "display:flex;gap:4px;flex-wrap:wrap;";
      Object.keys(presets).forEach((pName) => {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = pName;
        b.style.cssText =
          "background:#111525;border:1px solid #1C2235;border-radius:5px;padding:4px 9px;color:#8896AB;font-size:10px;cursor:pointer";
        b.onmouseenter = () => {
          b.style.borderColor = domain.accent;
          b.style.color = domain.accent;
        };
        b.onmouseleave = () => {
          b.style.borderColor = "#1C2235";
          b.style.color = "#8896AB";
        };
        b.onclick = () => {
          applyPreset(state.activeDomain, pName, state.selected);
          renderAll();
        };
        wrap.appendChild(b);
      });
      box.appendChild(wrap);
      content.appendChild(box);
    }

    Object.entries(domain.categories).forEach(([catName, items]) => {
      const fi = state.search ? items.filter((i) => i.toLowerCase().includes(sl)) : items;
      if (state.search && fi.length === 0) return;
      const ck = state.activeDomain + SEP + catName;
      const isC = state.collapsed.has(ck);
      const sc = items.filter((i) => state.selected.has(key(state.activeDomain, catName, i))).length;

      const block = document.createElement("div");
      block.style.cssText = [
        "margin-bottom:4px",
        "background:#0C1019",
        "border:1px solid " + (sc > 0 ? domain.accent + "25" : "#12172280"),
        "border-radius:8px",
        "overflow:hidden",
      ].join(";");

      const hdr = document.createElement("div");
      hdr.style.cssText = "display:flex;align-items:center;padding:10px 12px;gap:6px;";
      const left = document.createElement("button");
      left.type = "button";
      left.style.cssText =
        "background:transparent;border:none;cursor:pointer;flex:1;text-align:left;color:#94A3B8;display:flex;align-items:center;gap:7px;";
      left.innerHTML = `<span style="display:inline-block;transition:transform 0.15s;transform:rotate(${isC ? "-90deg" : "0"})">▼</span><span style="width:3px;height:14px;border-radius:1px;background:${sc > 0 ? domain.accent : "#1E293B"}"></span><span style="font-size:12px;font-weight:600;color:#CBD5E1">${esc(catName)}</span>${sc > 0 ? `<span style="font-size:9px;font-weight:700;color:${domain.accent};background:${domain.accent}15;padding:1px 5px;border-radius:3px">${sc}/${items.length}</span>` : ""}`;
      left.onclick = () => {
        if (state.collapsed.has(ck)) state.collapsed.delete(ck);
        else state.collapsed.add(ck);
        renderAll();
      };
      const allBtn = document.createElement("button");
      allBtn.type = "button";
      allBtn.textContent = sc === items.length ? "Clear" : "All";
      allBtn.style.cssText =
        "background:transparent;border:1px solid #1C2235;border-radius:4px;padding:2px 7px;cursor:pointer;font-size:9px;color:#64748B;font-weight:600";
      allBtn.onclick = () => {
        const allSel = items.every((i) => state.selected.has(key(state.activeDomain, catName, i)));
        items.forEach((i) => {
          const k = key(state.activeDomain, catName, i);
          if (allSel) state.selected.delete(k);
          else state.selected.add(k);
        });
        renderAll();
      };
      hdr.appendChild(left);
      hdr.appendChild(allBtn);
      block.appendChild(hdr);

      if (!isC) {
        const grid = document.createElement("div");
        grid.style.cssText = "padding:0 8px 8px;display:flex;flex-wrap:wrap;gap:3px;";
        fi.forEach((item) => {
          const k = key(state.activeDomain, catName, item);
          const isSel = state.selected.has(k);
          const b = document.createElement("button");
          b.type = "button";
          b.style.cssText = [
            "background:" + (isSel ? domain.accent + "10" : "#0F1320"),
            "border:1px solid " + (isSel ? domain.accent + "35" : "#161B2B"),
            "border-radius:6px",
            "padding:6px 10px",
            "cursor:pointer",
            "color:inherit",
            "display:flex",
            "align-items:center",
            "gap:6px",
          ].join(";");
          b.innerHTML = `<span style="width:15px;height:15px;border-radius:3px;border:1.5px solid ${isSel ? domain.accent : "#334155"};background:${isSel ? domain.accent : "transparent"};flex-shrink:0"></span><span style="font-size:11px;font-weight:${isSel ? 600 : 400};color:${isSel ? "#F1F5F9" : "#8896AB"};white-space:nowrap">${esc(item)}</span>`;
          b.onclick = () => {
            if (state.selected.has(k)) state.selected.delete(k);
            else state.selected.add(k);
            renderAll();
          };
          grid.appendChild(b);
        });
        block.appendChild(grid);
      }
      content.appendChild(block);
    });

    main.appendChild(content);
  }

  function renderAll() {
    renderSidebar();
    renderMain();
  }

  (async () => {
    try {
      state.projects = await api("GET", "/projects");
      if (prePid && state.projects.some((p) => String(p.id) === String(prePid))) {
        state.projectId = String(prePid);
        const p = await api("GET", "/projects/" + prePid);
        hydrateFromPayload(p.tech_stack, state.selected);
        state.projectName = p.name || "";
        state.activeDomain = DOMAIN_ORDER[0];
      }
    } catch (e) {
      toast("Failed to load projects: " + e.message, false);
    }
    renderAll();
  })();
}

mount();
