/** Svelte reactive store for configuration data.
 *
 * Loads initial state via GET /api/assignments and GET /api/identifier-mappings.
 * Subscribes to SSE /api/config/events to keep data fresh across surfaces.
 * Tracks SSE connection health for UI feedback (T057, T058).
 *
 * Tasks: T038 (Phase 3 — US1), T057 (Phase 5 — US3).
 */

import { writable, get } from "svelte/store";
import type { Assignment, IdentifierMapping } from "$lib/services/config-client";

type ConnectionStatus = "connected" | "disconnected" | "stale";

const _assignments = writable<Assignment[]>([]);
const _mappings = writable<IdentifierMapping[]>([]);
const _connectionStatus = writable<ConnectionStatus>("disconnected");
const _lastSeen = writable<number>(0);

export const assignments = { subscribe: _assignments.subscribe };
export const identifierMappings = { subscribe: _mappings.subscribe };
export const connectionStatus = { subscribe: _connectionStatus.subscribe };
export const lastSeen = { subscribe: _lastSeen.subscribe };

let _eventSource: EventSource | null = null;
let _reconnectAttempts = 0;
let _reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
let _staleCheckInterval: ReturnType<typeof setInterval> | null = null;

async function fetchAssignments(): Promise<void> {
	try {
		const resp = await fetch("/api/assignments");
		if (!resp.ok) return;
		const data = await resp.json();
		_assignments.set(Array.isArray(data) ? data : data.assignments ?? []);
	} catch {
		// Network failure — leave existing state intact
	}
}

async function fetchMappings(): Promise<void> {
	try {
		const resp = await fetch("/api/identifier-mappings");
		if (!resp.ok) return;
		const data = await resp.json();
		_mappings.set(Array.isArray(data) ? data : data.identifier_mappings ?? []);
	} catch {
		// Network failure — leave existing state intact
	}
}

function setConnected(): void {
	_connectionStatus.set("connected");
	_lastSeen.set(Date.now());
	_reconnectAttempts = 0;
}

function setDisconnected(): void {
	_connectionStatus.set("disconnected");
}

function setStale(): void {
	_connectionStatus.set("stale");
}

function scheduleReconnect(): void {
	if (_reconnectTimeout) clearTimeout(_reconnectTimeout);
	_reconnectAttempts++;
	const delay = Math.min(1000 * Math.pow(2, _reconnectAttempts - 1), 30000);
	_reconnectTimeout = setTimeout(startSSE, delay);
}

function startSSE(): void {
	if (_eventSource) {
		_eventSource.close();
		_eventSource = null;
	}

	const es = new EventSource("/api/config/events");
	_eventSource = es;

	es.onopen = () => setConnected();

	es.addEventListener("config.change", (ev) => {
		try {
			const msg = JSON.parse((ev as MessageEvent).data);
			const fp: string = msg.field_path || "";
			if (fp.startsWith("assignments.")) {
				fetchAssignments();
			} else if (fp.startsWith("identifier_mappings.")) {
				fetchMappings();
			}
			setConnected();
		} catch {
			// ignore malformed
		}
	});

	es.onmessage = () => setConnected();

	es.onerror = () => {
		setDisconnected();
		es.close();
		scheduleReconnect();
	};
}

/** Bootstrap config state and start live-reload subscription. Call once. */
export function initConfigStore(): void {
	fetchAssignments();
	fetchMappings();
	startSSE();

	if (_staleCheckInterval) clearInterval(_staleCheckInterval);
	_staleCheckInterval = setInterval(() => {
		const last = get(_lastSeen);
		if (last === 0) return;
		const age = Date.now() - last;
		if (age > 30000 && get(_connectionStatus) === "connected") {
			setStale();
		}
	}, 10000);
}

/** Force immediate SSE reconnect (e.g., refresh button in ConnectionStatus). */
export function reconnectSSE(): void {
	if (_reconnectTimeout) {
		clearTimeout(_reconnectTimeout);
		_reconnectTimeout = null;
	}
	_reconnectAttempts = 0;
	startSSE();
}
