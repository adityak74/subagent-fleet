/**
 * Fleet Dashboard — Real-time event handler.
 *
 * Connects to /api/events via the SSE EventSource API and updates each
 * dashboard panel as events arrive. Replaces the old 10-second polling
 * reload with live, incremental updates.
 */

(function () {
    'use strict';

    /* ── helpers ─────────────────────────────────────────── */

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function formatTs(iso) {
        try {
            var d = new Date(iso);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        } catch (_) {
            return iso || '';
        }
    }

     // Safe JSON parser for SSE events — prevents a malformed server response
     function parseSSE(e) {
         try { return JSON.parse(e.data); } catch (_) { return null; }
      }
    /* ── SSE connection ─────────────────────────────────── */

    var source = null;

    function connectSSE() {
        if (source) source.close();
        source = new EventSource('/api/events');

        source.addEventListener('node-status', handleNodeStatus);
        source.addEventListener('agent-route', handleAgentRoute);
        source.addEventListener('trace-log',   handleTraceLog);
        source.addEventListener('warmup-progress', handleWarmupProgress);
        source.addEventListener('error', function (e) {
            console.warn('[sse] error:', e.data || e.message);
        });

         var attempt = 0;
         var maxRetries = 10;

        source.onerror = function () {
            if (attempt++ >= maxRetries) {
                document.body.innerHTML += "<div class=\"alert alert-error\">Connection lost. <a href=\"javascript:connectSSE()\">Retry</a></div>";
                return;
              }
            var delay = Math.min(3000 * Math.pow(1.5, attempt), 30000);
            setTimeout(function () { connectSSE(); }, delay);
         };
    }

    /* ── Node Health panel ─────────────────────────────── */

    function handleNodeStatus(e) {
        var data = parseSSE(e);
        if (!data) return;
        var nodes = data.nodes || [];
        var container = document.getElementById('node-panel');

        if (nodes.length === 0) {
            container.innerHTML = '<div class="empty-state">No nodes configured</div>';
            return;
        }

        var html = '<table><thead><tr>' +
            '<th>Node</th><th>Status</th><th>Endpoint</th><th>Models</th>' +
            '</tr></thead><tbody>';

        for (var i = 0; i < nodes.length; i++) {
            var n = nodes[i];
            var statusClass = n.status === 'online' ? 'status-online' : 'status-offline';
            var statusText = n.status === 'online' ? 'Online' : 'Offline';
            var modelsStr = (n.models && n.models.length) ? n.models.join(', ') : '-';

            html += '<tr>' +
                '<td>' + escapeHtml(n.name) + '</td>' +
                '<td><span class="' + statusClass + '">' + statusText + '</span></td>' +
                '<td class="latency">' + escapeHtml(n.endpoint) + '</td>' +
                '<td class="models">' + escapeHtml(modelsStr) + '</td>' +
                '</tr>';
        }

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    /* ── Agent Routing panel ───────────────────────────── */

    function handleAgentRoute(e) {
        var data = parseSSE(e);
        if (!data) return;
        var routes = data.routes || [];
        var container = document.getElementById('route-panel');

        if (routes.length === 0) {
            container.innerHTML = '<div class="empty-state">No agents configured</div>';
            return;
        }

        var html = '<table><thead><tr>' +
            '<th>Agent</th><th>Node</th><th>Ollama Model</th><th>LiteLLM Alias</th>' +
            '</tr></thead><tbody>';

        for (var i = 0; i < routes.length; i++) {
            var r = routes[i];
            html += '<tr>' +
                '<td>' + escapeHtml(r.agent) + '</td>' +
                '<td>' + escapeHtml(r.node) + '</td>' +
                '<td>' + escapeHtml(r.ollama_model) + '</td>' +
                '<td class="latency">' + escapeHtml(r.litellm_alias) + '</td>' +
                '</tr>';
        }

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    /* ── Live Trace Stream panel ─────────────────────── */

    var tracePanel = document.getElementById('trace-panel');
    var autoScrollCheckbox = document.getElementById('auto-scroll');
    var clearBtn = document.getElementById('trace-clear');

    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            tracePanel.innerHTML = '';
        });
    }

    function handleTraceLog(e) {
        var data = parseSSE(e);
        if (!data) return;
        var level = data.level || 'info';
        var ts = formatTs(data.timestamp);
        var msg = escapeHtml(data.message);

        var entry = document.createElement('div');
        entry.className = 'trace-entry ' + level;
        entry.innerHTML = '<span class="trace-ts">' + ts + '</span><span class="trace-msg">' + msg + '</span>';

        tracePanel.appendChild(entry);

        // Keep max 500 entries to avoid memory issues.
        while (tracePanel.children.length > 500) {
            tracePanel.removeChild(tracePanel.firstChild);
        }

        if (autoScrollCheckbox && autoScrollCheckbox.checked) {
            tracePanel.scrollTop = tracePanel.scrollHeight;
        }
    }

    /* ── Warmup Progress panel ────────────────────────── */

    var warmupContainer = document.getElementById('warmup-panel');
    var warmupMap = {}; // keyed by "model|node" to deduplicate / update in place

    function handleWarmupProgress(e) {
        var data = parseSSE(e);
        if (!data) return;
        var key = (data.model_name || '') + '|' + (data.node_name || '');
        var icon, statusClass;

        var st = (data.status || '').toLowerCase();
        if (st === 'ok')            { icon = '&#x2705;';  statusClass = 'ok'; }
        else if ((data.status || '').indexOf('error') === 0) { icon = '&#x1F6AB;'; statusClass = 'error'; }
        else                        { icon = '&#x23F3;';  statusClass = 'pending'; }

        warmupMap[key] = {
            model: data.model_name || '',
            node: data.node_name || '',
            icon: icon,
            statusClass: statusClass,
            statusText: st === 'ok' ? 'OK' : (st.indexOf('error') === 0 ? 'Failed' : 'Warming…'),
        };

        renderWarmup();
    }

    function renderWarmup() {
        var entries = Object.keys(warmupMap);
        if (entries.length === 0) return; // leave empty state as-is

        var html = '';
        for (var i = 0; i < entries.length; i++) {
            var w = warmupMap[entries[i]];
            html += '<div class="warmup-item">' +
                '<span class="warmup-icon">' + w.icon + '</span>' +
                '<div class="warmup-info">' +
                    '<div class="warmup-model">' + escapeHtml(w.model) + '</div>' +
                    '<div class="warmup-node">' + escapeHtml(w.node) + '</div>' +
                '</div>' +
                '<span class="warmup-status ' + w.statusClass + '">' + w.statusText + '</span>' +
                '</div>';
        }
        warmupContainer.innerHTML = html;
    }

    /* ── Init ─────────────────────────────────────────── */

    connectSSE();
})();
