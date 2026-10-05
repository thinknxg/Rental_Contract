declare global { interface Window { csrf_token?: string } }

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

const strip = (s: string) => s.replace(/<[^>]*>/g, "").trim();

function message(status: number, body: any): string {
  try {
    if (body?._server_messages) {
      const msgs = JSON.parse(body._server_messages).map((m: string) => strip(JSON.parse(m).message));
      if (msgs.length) return msgs.join("\n");
    }
  } catch { /* fall through */ }
  if (status === 401) return "Your session has expired. Please sign in again.";
  if (status === 403) return "You do not have permission to do that.";
  if (status === 404) return "Document not found.";
  return "Something went wrong on the server. Please try again.";
}

export async function call<T = any>(method: string, args: Record<string, any> = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api/method/${method}`, {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-Frappe-CSRF-Token": window.csrf_token || "" },
      body: JSON.stringify(args),
    });
  } catch { throw new ApiError(0, "Network error. Check your connection."); }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 401 || (res.status === 403 && body.exc_type === "AuthenticationError"))
      window.dispatchEvent(new Event("session-expired"));
    throw new ApiError(res.status, message(res.status, body));
  }
  return body.message as T;
}

export interface Me { user: string; full_name: string; roles: string[]; is_staff: boolean }
export const getMe = () => call<Me>("equip_rental.portal_api.me");
export const login = (usr: string, pwd: string) => call("login", { usr, pwd });
export const logout = () => call("logout");

export const getList = (doctype: string, o: { fields: string[]; filters?: any; or_filters?: any; order_by?: string; start?: number; limit?: number }) =>
  call<any[]>("frappe.client.get_list", { doctype, fields: o.fields, filters: o.filters, or_filters: o.or_filters,
    order_by: o.order_by || "modified desc", limit_start: o.start || 0, limit_page_length: o.limit || 20 });
export const getCount = (doctype: string, filters?: any) => call<number>("frappe.client.get_count", { doctype, filters });
export const getDoc = (doctype: string, name: string) =>
  call<{ docs: any[]; docinfo: any }>("frappe.desk.form.load.getdoc", { doctype, name });
export const hasPerm = (doctype: string, docname: string, ptype: string) =>
  call<boolean>("frappe.client.has_permission", { doctype, docname, ptype });
export const submitDoc = (doc: any) => call("frappe.client.submit", { doc });
export const cancelDoc = (doctype: string, name: string) => call("frappe.client.cancel", { doctype, name });
export const insertDoc = (doc: any) => call<any>("frappe.client.insert", { doc });
// Existing backend mappers (business logic stays in Frappe)
export const mapDoc = (method: string, source_name: string) => call<any>(method, { source_name });
export const summary = () => call<any>("equip_rental.portal_api.portal_summary");
export const outstandingReturns = () => call<any[]>("equip_rental.portal_api.outstanding_returns");
export const related = (doctype: string, name: string) =>
  call<{ doctype: string; name: string; docstatus: number }[]>("equip_rental.portal_api.related_documents", { doctype, name });
