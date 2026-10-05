import { ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { Link, NavLink, Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import * as api from "./api";

/* ---------- config: only doctypes/fields that exist in the repo ---------- */
interface Cfg { dt: string; label: string; cols: string[]; search: string[]; dateField: string }
const DOCS: Record<string, Cfg> = {
  sdv: { dt: "SDV", label: "SDV", dateField: "service_date",
    cols: ["name", "customer", "jcr", "service_date", "docstatus", "inv_no"], search: ["name", "customer", "jcr"] },
  customers: { dt: "Customer", label: "Customers", dateField: "creation",
    cols: ["name", "customer_name", "customer_group", "territory", "mobile_no", "email_id"], search: ["name", "customer_name"] },
  items: { dt: "Item", label: "Items", dateField: "creation",
    cols: ["name", "item_name", "item_group", "stock_uom", "is_rental_item", "disabled"], search: ["name", "item_name"] },
  "sales-invoices": { dt: "Sales Invoice", label: "Sales Invoices", dateField: "posting_date",
    cols: ["name", "customer", "posting_date", "docstatus", "grand_total", "outstanding_amount"], search: ["name", "customer"] },
  payments: { dt: "Payment Entry", label: "Payments", dateField: "posting_date",
    cols: ["name", "party", "posting_date", "payment_type", "paid_amount", "docstatus"], search: ["name", "party"] },
  leads: { dt: "Lead", label: "Leads", dateField: "creation",
    cols: ["name", "lead_name", "company_name", "status", "email_id", "mobile_no"], search: ["name", "lead_name", "company_name"] },
  quotations: { dt: "Quotation", label: "Quotations", dateField: "transaction_date",
    cols: ["name", "party_name", "transaction_date", "custom_deal_type", "status", "grand_total"], search: ["name", "party_name"] },
  "sales-orders": { dt: "Sales Order", label: "Sales Orders", dateField: "transaction_date",
    cols: ["name", "customer", "transaction_date", "custom_deal_type", "status", "grand_total"], search: ["name", "customer"] },
  dispatch: { dt: "Rental Dispatch Note", label: "Dispatch Notes", dateField: "dispatch_datetime",
    cols: ["name", "customer", "rental_contract", "dispatch_datetime", "docstatus", "delivery_note"], search: ["name", "customer", "rental_contract"] },
  jcr: { dt: "JCR", label: "JCRs", dateField: "modified",
    cols: ["name", "client_name", "project_name", "lpo_number", "docstatus", "modified"], search: ["name", "client_name", "project_name"] },
  "return-notes": { dt: "Rental Return Note", label: "Return Notes", dateField: "return_datetime",
    cols: ["name", "customer", "rental_contract", "return_datetime", "docstatus", "total_damage_charges"], search: ["name", "customer", "rental_contract"] },
};
const formPath = (dt: string, name?: string) => `/form/${encodeURIComponent(dt)}${name ? "/" + encodeURIComponent(name) : ""}`;
const deskSlug = (dt: string) => dt.toLowerCase().replace(/ /g, "-");
const MAPPERS: Record<string, { label: string; method: string; returnsName?: boolean }[]> = {
  Lead: [{ label: "Create Quotation", method: "erpnext.crm.doctype.lead.lead.make_quotation" }],
  Quotation: [{ label: "Create Sales Order", method: "erpnext.selling.doctype.quotation.quotation.make_sales_order" }],
  "Sales Order": [
    { label: "Create Dispatch Note", method: "equip_rental.utils.sales_order_to_dispatch.make_dispatch_note" },
    { label: "Create JCR", method: "equip_rental.utils.sales_order_to_jcr.make_jcr" }],
  "Rental Dispatch Note": [{ label: "Create Return Note", method: "equip_rental.utils.rental_dispatch_to_return.make_return_note" }],
  JCR: [{ label: "Create Sales Invoice", method: "equip_rental.equipment_rental.doctype.jcr.jcr.create_sales_invoice", returnsName: true }],
};
const pretty = (s: string) => s.replace(/^custom_/, "").replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
const SKIP = new Set(["owner", "creation", "modified_by", "idx", "doctype", "parent", "parenttype", "parentfield", "docstatus", "name", "naming_series", "amended_from"]);
const fmt = (k: string, v: any) => (k === "docstatus" ? <Badge ds={v} /> : v ?? "—");

/* ---------- small shared pieces ---------- */
const Badge = ({ ds }: { ds: number }) => (
  <span className={`badge ds${ds}`}>{["Draft", "Submitted", "Cancelled"][ds] ?? ds}</span>);
const Spinner = () => <p className="muted">Loading…</p>;
const ErrorBox = ({ e }: { e: string }) => <p className="error">{e}</p>;

type Toast = { msg: string; err?: boolean } | null;
function useToast(): [Toast, (m: string, err?: boolean) => void] {
  const [t, set] = useState<Toast>(null);
  useEffect(() => { if (t) { const id = setTimeout(() => set(null), 4000); return () => clearTimeout(id); } }, [t]);
  return [t, (msg, err) => set({ msg, err })];
}
const ToastView = ({ t }: { t: Toast }) => (t ? <div className={`toast ${t.err ? "err" : ""}`}>{t.msg}</div> : null);

/* ---------- login ---------- */
function Login() {
  const [usr, setUsr] = useState(""); const [pwd, setPwd] = useState("");
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const go = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setErr("");
    try { await api.login(usr, pwd); window.location.reload(); } // reload => fresh CSRF token
    catch (x: any) { setErr(x.status === 401 ? "Incorrect email or password." : x.message); setBusy(false); }
  };
  return (<div className="login"><form onSubmit={go} className="card">
    <h2>Rental Portal</h2>
    <input placeholder="Email" value={usr} onChange={(e) => setUsr(e.target.value)} autoFocus />
    <input type="password" placeholder="Password" value={pwd} onChange={(e) => setPwd(e.target.value)} />
    {err && <ErrorBox e={err} />}
    <button disabled={busy || !usr || !pwd}>{busy ? "Signing in…" : "Sign in"}</button>
  </form></div>);
}

/* ---------- layout ---------- */
function Layout({ me, children }: { me: api.Me; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const out = async () => { await api.logout().catch(() => 0); window.location.reload(); };
  const nav = me.is_staff
    ? [["/dashboard", "Dashboard"], ["/leads", "Leads"], ["/quotations", "Quotations"], ["/sales-orders", "Sales Orders"], ["/dispatch", "Dispatch"], ["/returns", "Returns Due"],
       ["/return-notes", "Return Notes"], ["/jcr", "JCR"], ["/sdv", "SDV"], ["/sales-invoices", "Invoices"], ["/payments", "Payments"],
       ["/customers", "Customers"], ["/items", "Items"], ["/profile", "Profile"]]
    : [["/profile", "Profile"]];
  return (<div className="shell">
    <header><button className="burger" onClick={() => setOpen(!open)}>☰</button><b>Rental Portal</b>
      <span className="grow" /><span className="muted">{me.full_name || me.user}</span><button onClick={out}>Log out</button></header>
    <nav className={open ? "open" : ""} onClick={() => setOpen(false)}>
      {nav.map(([to, l]) => <NavLink key={to} to={to}>{l}</NavLink>)}</nav>
    <main>{children}</main></div>);
}

/* ---------- dashboard ---------- */
function Dashboard() {
  const [d, setD] = useState<any>(); const [e, setE] = useState("");
  useEffect(() => { api.summary().then(setD).catch((x) => setE(x.message)); }, []);
  if (e) return <ErrorBox e={e} />; if (!d) return <Spinner />;
  const L: Record<string, string> = { sales_orders_awaiting_dispatch: "Hire SOs awaiting dispatch", dispatch_drafts: "Draft dispatches",
    dispatches_submitted: "Submitted dispatches", jcr_drafts: "Draft JCRs", jcr_submitted: "Submitted JCRs", return_notes_submitted: "Submitted returns" };
  const route: Record<string, string> = { "Rental Dispatch Note": "dispatch", JCR: "jcr", "Rental Return Note": "return-notes" };
  return (<><h1>Dashboard</h1>
    <div className="cards">{Object.entries(d.cards).map(([k, v]) => <div className="card stat" key={k}><b>{v as number}</b><span>{L[k]}</span></div>)}</div>
    {Object.entries(d.recent).map(([dt, rows]) => (<section key={dt}><h3>Recent {dt}</h3>
      {(rows as any[]).length === 0 ? <p className="muted">Nothing yet.</p> : (rows as any[]).map((r) => (
        <div className="row" key={r.name}><Link to={`/doc/${dt}/${encodeURIComponent(r.name)}`}>{r.name}</Link>
          <span className="muted">{r.customer || r.client_name}</span><Badge ds={r.docstatus} /></div>))}
      <Link to={`/${route[dt]}`} className="muted">View all →</Link></section>))}</>);
}

/* ---------- generic server-side list ---------- */
const PAGE = 20;
function List({ cfg }: { cfg: Cfg }) {
  const [rows, setRows] = useState<any[]>([]); const [total, setTotal] = useState(0); const [page, setPage] = useState(0);
  const [q, setQ] = useState(""); const [ds, setDs] = useState(""); const [from, setFrom] = useState(""); const [to, setTo] = useState("");
  const [sort, setSort] = useState("modified desc"); const [busy, setBusy] = useState(true); const [e, setE] = useState("");
  useEffect(() => setPage(0), [cfg, q, ds, from, to]);
  useEffect(() => {
    const filters: any[] = [];
    if (ds) filters.push([cfg.dt, "docstatus", "=", ds]);
    if (from) filters.push([cfg.dt, cfg.dateField, ">=", from]);
    if (to) filters.push([cfg.dt, cfg.dateField, "<=", to + " 23:59:59"]);
    const or_filters = q ? cfg.search.map((f) => [cfg.dt, f, "like", `%${q}%`]) : undefined;
    setBusy(true); setE("");
    Promise.all([
      api.getList(cfg.dt, { fields: cfg.cols, filters, or_filters, order_by: sort, start: page * PAGE, limit: PAGE }),
      api.call<number>("frappe.client.get_count", { doctype: cfg.dt, filters, or_filters }).catch(() => 0),
    ]).then(([r, c]) => { setRows(r); setTotal(c); }).catch((x) => setE(x.message)).finally(() => setBusy(false));
  }, [cfg, q, ds, from, to, sort, page]);
  const toggle = (c: string) => setSort(sort === `${c} asc` ? `${c} desc` : `${c} asc`);
  return (<><h1>{cfg.label} <Link className="btnlink" to={formPath(cfg.dt)}>+ New</Link></h1>
    <div className="filters"><input placeholder="Search…" value={q} onChange={(e) => setQ(e.target.value)} />
      <select value={ds} onChange={(e) => setDs(e.target.value)}><option value="">Any status</option>
        <option value="0">Draft</option><option value="1">Submitted</option><option value="2">Cancelled</option></select>
      <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} /><input type="date" value={to} onChange={(e) => setTo(e.target.value)} /></div>
    {e && <ErrorBox e={e} />}
    <div className="scroll"><table><thead><tr>{cfg.cols.map((c) => <th key={c} onClick={() => toggle(c)}>{pretty(c)}{sort.startsWith(c + " ") ? (sort.endsWith("asc") ? " ▲" : " ▼") : ""}</th>)}</tr></thead>
      <tbody>{rows.map((r) => <tr key={r.name}>{cfg.cols.map((c) => <td key={c}>{c === "name"
        ? <Link to={`/doc/${cfg.dt}/${encodeURIComponent(r.name)}`}>{r.name}</Link> : fmt(c, r[c])}</td>)}</tr>)}</tbody></table></div>
    {busy && <Spinner />}{!busy && !rows.length && !e && <p className="muted">No records match.</p>}
    <div className="pager"><button disabled={page === 0} onClick={() => setPage(page - 1)}>Prev</button>
      <span>{total ? `${page * PAGE + 1}–${Math.min((page + 1) * PAGE, total)} of ${total}` : ""}</span>
      <button disabled={(page + 1) * PAGE >= total} onClick={() => setPage(page + 1)}>Next</button></div></>);
}

/* ---------- generic detail (fields, child tables, actions, related, timeline) ---------- */
function Detail() {
  const { dt = "", name = "" } = useParams(); const nav = useNavigate(); const [toast, say] = useToast();
  const [doc, setDoc] = useState<any>(); const [info, setInfo] = useState<any>(); const [rel, setRel] = useState<any[]>([]);
  const [can, setCan] = useState<{ submit?: boolean; cancel?: boolean }>({}); const [e, setE] = useState("");
  const load = useCallback(() => {
    setDoc(undefined); setE("");
    api.getDoc(dt, name).then(async (r) => {
      const d = r.docs[0]; setDoc(d); setInfo(r.docinfo);
      api.related(dt, name).then(setRel).catch(() => setRel([]));
      if (d.docstatus === 0) setCan({ submit: await api.hasPerm(dt, name, "submit").catch(() => false) });
      else if (d.docstatus === 1) setCan({ cancel: await api.hasPerm(dt, name, "cancel").catch(() => false) });
    }).catch((x) => setE(x.message));
  }, [dt, name]);
  useEffect(load, [load]);
  const run = async (fn: () => Promise<any>, ok: string, confirmMsg?: string) => {
    if (confirmMsg && !window.confirm(confirmMsg)) return;
    try { await fn(); say(ok); load(); } catch (x: any) { say(x.message, true); }
  };
  const map = (m: { label: string; method: string; returnsName?: boolean }) => async () => {
    try {
      if (m.returnsName) { const n = await api.mapDoc(m.method, name); say(`${n} created`); nav(formPath("Sales Invoice", n)); return; }
      const draft = await api.mapDoc(m.method, name); const saved = await api.insertDoc(draft);
      say(`${saved.doctype} ${saved.name} created`); nav(formPath(saved.doctype, saved.name));
    } catch (x: any) { say(x.message, true); }
  };
  if (e) return <ErrorBox e={e} />; if (!doc) return <Spinner />;
  const scalars = Object.entries(doc).filter(([k, v]) => !SKIP.has(k) && !k.startsWith("__") && v !== null && v !== "" && typeof v !== "object");
  const tables = Object.entries(doc).filter(([, v]) => Array.isArray(v) && (v as any[]).length);
  return (<><ToastView t={toast} />
    <h1>{dt} <small>{name}</small> {dt !== "Lead" && <Badge ds={doc.docstatus} />}</h1>
    <div className="actions">
      <Link className="btnlink" to={formPath(dt, name)}>{doc.docstatus === 0 ? "Edit" : "Open form"}</Link>
      {doc.docstatus === 0 && can.submit && <button onClick={() => run(() => api.submitDoc(doc), "Submitted", `Submit ${name}?`)}>Submit</button>}
      {doc.docstatus === 1 && can.cancel && <button className="danger" onClick={() => run(() => api.cancelDoc(dt, name), "Cancelled", `Cancel ${name}?`)}>Cancel</button>}
      {(doc.docstatus === 1 || dt === "Lead") && (MAPPERS[dt] || []).filter((m) => dt !== "Rental Dispatch Note" || doc.delivery_note).map((m) => <button key={m.label} onClick={map(m)}>{m.label}</button>)}
    </div>
    <div className="card grid">{scalars.map(([k, v]) => <div key={k}><span className="muted">{pretty(k)}</span><br />{String(v)}</div>)}</div>
    {tables.map(([k, rows]) => { const cols = Object.keys((rows as any[])[0]).filter((c) => !SKIP.has(c) && !c.startsWith("__") && typeof (rows as any[])[0][c] !== "object");
      return (<section key={k}><h3>{pretty(k)}</h3><div className="scroll"><table><thead><tr>{cols.map((c) => <th key={c}>{pretty(c)}</th>)}</tr></thead>
        <tbody>{(rows as any[]).map((r, i) => <tr key={i}>{cols.map((c) => <td key={c}>{r[c] ?? "—"}</td>)}</tr>)}</tbody></table></div></section>); })}
    <section><h3>Related documents</h3>{rel.length ? rel.map((r) => <div className="row" key={r.doctype + r.name}>
      <span className="muted">{r.doctype}</span><Link to={`/doc/${r.doctype}/${encodeURIComponent(r.name)}`}>{r.name}</Link><Badge ds={r.docstatus} /></div>) : <p className="muted">None found.</p>}</section>
    <section><h3>Timeline</h3>
      {[...(info?.comments || []).map((c: any) => ({ at: c.creation, who: c.comment_email || c.owner, what: c.content?.replace(/<[^>]*>/g, "") })),
        ...(info?.versions || []).map((v: any) => ({ at: v.creation, who: v.owner, what: "Updated" })),
        ...(info?.communications || []).map((c: any) => ({ at: c.creation, who: c.sender, what: c.subject }))]
        .sort((a, b) => (a.at < b.at ? 1 : -1)).map((t, i) => <div className="row" key={i}><span className="muted">{t.at?.slice(0, 16)}</span><span>{t.who}</span><span>{t.what}</span></div>)}
      <div className="row"><span className="muted">{doc.creation?.slice(0, 16)}</span><span>{doc.owner}</span><span>Created</span></div></section></>);
}

/* ---------- embedded Frappe form: full form, client scripts, Create menu, calculations ---------- */
function DeskForm() {
  const { dt = "", name = "" } = useParams(); const nav = useNavigate();
  const ref = useRef<HTMLIFrameElement>(null); const [path, setPath] = useState(""); const [loaded, setLoaded] = useState(false);
  const src = `/app/${deskSlug(dt)}/${name ? encodeURIComponent(name) : "new"}`;
  const tidy = () => {
    try {
      const d = ref.current?.contentDocument; if (!d) return;
      if (!d.getElementById("portal-tidy")) {
        const st = d.createElement("style"); st.id = "portal-tidy";
        st.textContent = ":root{--navbar-height:0px !important}header.navbar,.navbar{display:none !important}body{padding-top:0 !important}.page-head{top:0 !important}";
        d.head.appendChild(st);
      }
      setPath(ref.current!.contentWindow!.location.pathname + ref.current!.contentWindow!.location.search);
    } catch { /* cross-origin: leave as is */ }
  };
  useEffect(() => { setLoaded(false); const id = setInterval(tidy, 800); return () => clearInterval(id); }, [src]);
  return (<div className="deskform">
    <div className="actions"><button className="ghost" onClick={() => nav(-1)}>← Back</button>
      <Link className="btnlink" to={name ? `/doc/${encodeURIComponent(dt)}/${encodeURIComponent(name)}` : "/dashboard"}>Summary view</Link>
      <a className="btnlink" href={path || src} target="_blank" rel="noreferrer">Open in new tab</a></div>
    {!loaded && <Spinner />}
    <iframe ref={ref} key={src} src={src} title={dt} onLoad={() => { setLoaded(true); tidy(); }} />
  </div>);
}

/* ---------- returns due ---------- */
function Returns() {
  const [rows, setRows] = useState<any[]>(); const [e, setE] = useState("");
  useEffect(() => { api.outstandingReturns().then(setRows).catch((x) => setE(x.message)); }, []);
  if (e) return <ErrorBox e={e} />; if (!rows) return <Spinner />;
  return (<><h1>Returns Due</h1>{!rows.length && <p className="muted">Nothing outstanding.</p>}
    {rows.map((r) => <section className="card" key={r.name}>
      <div className="row"><Link to={`/doc/Rental Dispatch Note/${encodeURIComponent(r.name)}`}>{r.name}</Link><span>{r.customer}</span>
        <Link to={`/doc/Sales Order/${encodeURIComponent(r.rental_contract)}`}>{r.rental_contract}</Link></div>
      <div className="scroll"><table><thead><tr><th>Item</th><th>Dispatched</th><th>Returned</th><th>Outstanding</th></tr></thead>
        <tbody>{r.items.map((i: any) => <tr key={i.item_code}><td>{i.item_name || i.item_code}</td><td>{i.dispatched}</td><td>{i.returned}</td><td>{i.outstanding}</td></tr>)}</tbody></table></div></section>)}</>);
}

function Profile({ me }: { me: api.Me }) {
  return (<><h1>Profile</h1><div className="card grid"><div><span className="muted">Name</span><br />{me.full_name}</div>
    <div><span className="muted">User</span><br />{me.user}</div><div><span className="muted">Roles</span><br />{me.roles.join(", ")}</div></div>
    {!me.is_staff && <p className="muted">Customer self-service pages are not enabled yet.</p>}</>);
}

/* ---------- app shell with auth guard ---------- */
export default function App() {
  const [me, setMe] = useState<api.Me | null>(null); const [ready, setReady] = useState(false);
  useEffect(() => { api.getMe().then(setMe).catch(() => 0).finally(() => setReady(true));
    const exp = () => setMe(null); window.addEventListener("session-expired", exp); return () => window.removeEventListener("session-expired", exp); }, []);
  if (!ready) return <Spinner />;
  if (!me || me.user === "Guest") return <Login />;
  return (<Layout me={me}><Routes>
    <Route path="/" element={<Navigate to={me.is_staff ? "/dashboard" : "/profile"} replace />} />
    <Route path="/dashboard" element={<Dashboard />} /><Route path="/returns" element={<Returns />} />
    {Object.entries(DOCS).map(([p, c]) => <Route key={p} path={`/${p}`} element={<List cfg={c} />} />)}
    <Route path="/doc/:dt/:name" element={<Detail />} /><Route path="/form/:dt" element={<DeskForm />} /><Route path="/form/:dt/:name" element={<DeskForm />} /><Route path="/profile" element={<Profile me={me} />} />
    <Route path="*" element={<p>Page not found. <Link to="/">Home</Link></p>} /></Routes></Layout>);
}
