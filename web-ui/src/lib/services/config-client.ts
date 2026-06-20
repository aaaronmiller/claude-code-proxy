/** Typed HTTP client for Configuration API.
 *
 * All methods return promises and throw on non-2xx status.
 * The backend runs on http://127.0.0.1:8082 by default.
 *
 * Task: T037 (Phase 3 — US1)
 */

export interface Assignment {
	id: string;
	kind: "tier" | "slot";
	model: string;
	provider: string;
	base_url: string;
	api_key: string;
	enabled: boolean;
	cascade: string[];
}

export interface IdentifierMapping {
	id: string;
	incoming_identifier: string;
	assignment_id: string;
	enabled: boolean;
	priority: number;
	notes: string;
}

const BASE = "http://127.0.0.1:8082";

// ── Manifest-driven settings (the 64-setting config surface) ──────────────────

export interface ConfigSetting {
	key: string;
	env_var: string;
	type: "str" | "int" | "float" | "bool";
	default: unknown;
	description: string;
	group: string;
	cli_flag: string | null;
	choices: string[] | null;
	tui_widget: string;
	web_component: "input" | "switch" | "select" | "number" | "textarea" | "slider";
	secret: boolean;
	units: string | null;
}

export interface ConfigGroup {
	name: string;
	label: string;
	settings: ConfigSetting[];
}

/** GET /api/config/schema — manifest metadata (groups + render hints). */
export async function getConfigSchema(): Promise<{ groups: ConfigGroup[] }> {
	const res = await fetch(`${BASE}/api/config/schema`);
	if (!res.ok) throw new Error(`getConfigSchema: ${res.status} ${res.statusText}`);
	return res.json();
}

/** GET /api/config — current values keyed by lowercased env var. */
export async function getConfigValues(): Promise<Record<string, unknown>> {
	const res = await fetch(`${BASE}/api/config`);
	if (!res.ok) throw new Error(`getConfigValues: ${res.status} ${res.statusText}`);
	return res.json();
}

/** POST /api/config/manifest — generic save of any manifest setting(s). */
export async function saveSettings(
	updates: Record<string, unknown>,
): Promise<{ status: string; saved: string[]; rejected: Record<string, string> }> {
	const res = await fetch(`${BASE}/api/config/manifest`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(updates),
	});
	if (!res.ok) throw new Error(`saveSettings: ${res.status} ${res.statusText}`);
	return res.json();
}

/** GET /api/assignments */
export async function listAssignments(): Promise<{ assignments: Assignment[] }> {
	const res = await fetch(`${BASE}/api/assignments`);
	if (!res.ok) throw new Error(`listAssignments: ${res.status} ${res.statusText}`);
	return res.json();
}

/** GET /api/assignments/{id} */
export async function getAssignment(
	id: string,
): Promise<Assignment> {
	const res = await fetch(`${BASE}/api/assignments/${id}`);
	if (!res.ok) throw new Error(`getAssignment: ${res.status} ${res.statusText}`);
	return res.json();
}

/** POST /api/assignments */
export async function createAssignment(
	payload: Omit<Assignment, "id">,
): Promise<Assignment> {
	const res = await fetch(`${BASE}/api/assignments`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	if (!res.ok) throw new Error(`createAssignment: ${res.status} ${res.statusText}`);
	return res.json();
}

/** PATCH /api/assignments/{id} */
export async function updateAssignment(
	id: string,
	payload: Partial<Omit<Assignment, "id">>,
): Promise<Assignment> {
	const res = await fetch(`${BASE}/api/assignments/${id}`, {
		method: "PATCH",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	if (!res.ok) throw new Error(`updateAssignment: ${res.status} ${res.statusText}`);
	return res.json();
}

/** DELETE /api/assignments/{id} */
export async function deleteAssignment(id: string): Promise<void> {
	const res = await fetch(`${BASE}/api/assignments/${id}`, {
		method: "DELETE",
	});
	if (!res.ok) throw new Error(`deleteAssignment: ${res.status} ${res.statusText}`);
}

/** GET /api/identifier-mappings */
export async function listIdentifierMappings(): Promise<{
	identifier_mappings: IdentifierMapping[];
}> {
	const res = await fetch(`${BASE}/api/identifier-mappings`);
	if (!res.ok) throw new Error(`listIdentifierMappings: ${res.status} ${res.statusText}`);
	return res.json();
}

/** POST /api/identifier-mappings */
export async function createIdentifierMapping(
	payload: Omit<IdentifierMapping, "id">,
): Promise<IdentifierMapping> {
	const res = await fetch(`${BASE}/api/identifier-mappings`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	if (!res.ok) throw new Error(`createIdentifierMapping: ${res.status} ${res.statusText}`);
	return res.json();
}

/** PATCH /api/identifier-mappings/{id} */
export async function updateIdentifierMapping(
	id: string,
	payload: Partial<Omit<IdentifierMapping, "id">>,
): Promise<IdentifierMapping> {
	const res = await fetch(`${BASE}/api/identifier-mappings/${id}`, {
		method: "PATCH",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	if (!res.ok) throw new Error(`updateIdentifierMapping: ${res.status} ${res.statusText}`);
	return res.json();
}

/** DELETE /api/identifier-mappings/{id} */
export async function deleteIdentifierMapping(id: string): Promise<void> {
	const res = await fetch(`${BASE}/api/identifier-mappings/${id}`, {
		method: "DELETE",
	});
	if (!res.ok) throw new Error(`deleteIdentifierMapping: ${res.status} ${res.statusText}`);
}
