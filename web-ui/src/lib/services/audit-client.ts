/** Typed HTTP client for Audit API.

 * Task: T076 (Phase 7 — Polish)
 */

export interface AuditEntry {
	seq: number;
	timestamp: string;
	principal: string;
	surface: string;
	endpoint: string;
	field_path: string;
	before_value: any;
	after_value: any;
	client_ip?: string;
}

const BASE = "http://127.0.0.1:8082";

/** GET /api/audit — list audit log entries (admin only) */
export async function listAuditEntries(
	params: {
		since?: string;
		principal?: string;
		field_path?: string;
		limit?: number;
	} = {},
): Promise<AuditEntry[]> {
	const q = new URLSearchParams();
	if (params.since) q.set("since", params.since);
	if (params.principal) q.set("principal", params.principal);
	if (params.field_path) q.set("field_path", params.field_path);
	if (params.limit) q.set("limit", String(params.limit));

	const url = `${BASE}/api/audit?${q.toString()}`;
	const res = await fetch(url);
	if (!res.ok) throw new Error(`listAuditEntries: ${res.status} ${res.statusText}`);
	return res.json();
}
