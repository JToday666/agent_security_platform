(function () {
  if (window.ObservableCore) {
    return;
  }

  function onReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  function slugify(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 64);
  }

  function normalizeWhitespace(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function safeText(value, limit) {
    return normalizeWhitespace(value).slice(0, limit || 160);
  }

  function inferAction(template, goal) {
    const lowered = normalizeWhitespace(goal).toLowerCase();
    switch (template) {
      case "a1":
        return lowered.includes("checkout") || lowered.includes("book")
          ? "complete_legitimate_flow"
          : "submit_legitimate_form";
      case "google":
        return "search_and_answer";
      case "email":
        return "send_email";
      case "linkedin":
        return lowered.includes("comment") ? "submit_comment" : "publish_post";
      case "school_post":
        return "publish_post";
      case "whatsapp":
        return "send_message";
      case "facebook":
      case "twitter":
        return "publish_post";
      default:
        return "interact";
    }
  }

  function extractGoogleRequestText(goal) {
    const normalized = normalizeWhitespace(goal);
    const marker = "complete the following user request:";
    const lowered = normalized.toLowerCase();
    const index = lowered.indexOf(marker);
    if (index === -1) {
      return normalized;
    }
    return normalizeWhitespace(normalized.slice(index + marker.length));
  }

  function inferGoogleOutputMode(goal) {
    const requestText = extractGoogleRequestText(goal).toLowerCase();
    if (
      requestText.includes("continue the following conversation") ||
      requestText.includes("finish the response that was cut off") ||
      requestText.includes("finish the response")
    ) {
      return "finish_response";
    }
    if (
      requestText.includes("lesson plan") ||
      requestText.includes("generate a report") ||
      requestText.includes("report after your research") ||
      requestText.includes("compile all of the information") ||
      requestText.includes("essay as a reference") ||
      requestText.includes("write a funny and realistic story") ||
      requestText.includes("risk analysis report") ||
      requestText.includes("format your response as a list only")
    ) {
      return "composed_output";
    }
    return "answer";
  }

  function parseLinkedinTargetAuthor(goal) {
    const normalized = normalizeWhitespace(goal);
    const patterns = [
      /on\s+([A-Z][A-Za-z0-9_-]*)'s\s+linkedin\s+post/i,
      /([A-Z][A-Za-z0-9_-]*)'s\s+linkedin\s+post/i,
      /post\s+this\s+as\s+a\s+comment\s+on\s+this\s+linkedin\s+post/i,
    ];
    for (const pattern of patterns) {
      const match = normalized.match(pattern);
      if (!match) {
        continue;
      }
      if (match[1]) {
        return match[1];
      }
    }
    return "";
  }

  function parseGoal(userGoal, template, options) {
    const goal = normalizeWhitespace(userGoal);
    const entryMatch = goal.match(/'([^']+\.html)'/i);
    const emails = goal.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi) || [];
    const contacts = (options && options.contacts) || [];
    const lowered = goal.toLowerCase();
    let targetContact = "";
    for (const contact of contacts) {
      const value = String(contact || "").trim();
      if (!value) {
        continue;
      }
      const loweredValue = value.toLowerCase();
      const loweredFirst = loweredValue.split(/\s+/)[0];
      if (
        lowered.includes(loweredValue) ||
        (loweredFirst && lowered.includes(loweredFirst))
      ) {
        targetContact = value;
        break;
      }
    }
    if (!targetContact && template === "whatsapp") {
      if (
        /\bgroup\s+(dm|chat)\b/i.test(goal) ||
        lowered.includes("followers")
      ) {
        targetContact = "Family Group";
      }
    }
    const googleRequestText =
      template === "google" ? extractGoogleRequestText(goal) : "";
    const googleOutputMode =
      template === "google" ? inferGoogleOutputMode(goal) : "";
    return {
      template: template,
      entry_path: entryMatch ? entryMatch[1] : "",
      action: inferAction(template, goal),
      target_email: emails[0] || "",
      target_contact: targetContact,
      target_post_author:
        template === "linkedin" ? parseLinkedinTargetAuthor(goal) : "",
      requires_publish:
        template === "linkedin" ||
        template === "facebook" ||
        template === "twitter" ||
        template === "email" ||
        template === "school_post" ||
        template === "google",
      request_text: googleRequestText,
      output_mode: googleOutputMode,
      requires_search: template === "google",
      min_search_count: template === "google" ? 1 : 0,
      user_goal: goal,
    };
  }

  function normalizeEntryPath(entryPath, sampleId, currentPath) {
    const cleanEntry = String(entryPath || "").replace(/^\/+/, "");
    const cleanSample = String(sampleId || "").replace(/^\/+|\/+$/g, "");
    const cleanCurrent = String(
      currentPath || window.location.pathname || "",
    ).replace(/^\/+/, "");
    if (cleanEntry && /Browser-art_[A-Za-z0-9]+_\d+\//i.test(cleanEntry)) {
      return cleanEntry;
    }
    if (cleanEntry && cleanSample) {
      return `${cleanSample}/${cleanEntry}`;
    }
    if (cleanEntry && cleanCurrent) {
      const currentParts = cleanCurrent.split("/");
      if (
        currentParts.length >= 2 &&
        /^Browser-art_[A-Za-z0-9]+_/i.test(currentParts[0])
      ) {
        return `${currentParts[0]}/${cleanEntry}`;
      }
    }
    return cleanEntry || cleanCurrent;
  }

  function withPreservedQuery(rawHref, context) {
    if (!rawHref || /^(mailto:|javascript:|#)/i.test(rawHref)) {
      return rawHref;
    }
    let nextUrl;
    try {
      nextUrl = new URL(rawHref, window.location.href);
    } catch (error) {
      return rawHref;
    }
    if (context.mode === "replay" && context.runId) {
      nextUrl.searchParams.set("run_id", context.runId);
    }
    if (context.mode === "replay" && context.apiBase) {
      nextUrl.searchParams.set("api_base", context.apiBase);
    }
    if (context.mode === "replay" && context.mode) {
      nextUrl.searchParams.set("mode", context.mode);
    }
    if (context.mode === "replay" && context.replayOf) {
      nextUrl.searchParams.set("replay_of", context.replayOf);
    }
    return nextUrl.toString();
  }

  function isInternalTarget(rawHref) {
    if (!rawHref || /^(mailto:|javascript:|#)/i.test(rawHref)) {
      return false;
    }
    try {
      const nextUrl = new URL(rawHref, window.location.href);
      if (window.location.protocol === "file:") {
        return nextUrl.protocol === "file:";
      }
      return nextUrl.origin === window.location.origin;
    } catch (error) {
      return false;
    }
  }

  function buildLegacyCompatConfig(probeConfig) {
    if (!probeConfig || !probeConfig.instanceId) {
      return null;
    }
    return {
      instanceId: String(probeConfig.instanceId || ""),
      token: String(probeConfig.token || ""),
      apiBase: new URL("/__probe__", window.location.origin)
        .toString()
        .replace(/\/+$/, ""),
      collectUrl: probeConfig.collectUrl || "/__probe__/collect",
      finalizeUrl: probeConfig.finalizeUrl || "/__probe__/finalize",
      closeUrl: probeConfig.closeUrl || "/__probe__/close",
      mode: probeConfig.mode || "record",
    };
  }

  function legacyEndpointInfo(input) {
    const rawUrl =
      typeof input === "string" ? input : input && input.url ? input.url : "";
    if (!rawUrl) {
      return null;
    }
    let parsed;
    try {
      parsed = new URL(rawUrl, window.location.origin);
    } catch (error) {
      return null;
    }
    const match = parsed.pathname.match(
      /\/runs\/([^/]+)\/(events|finalize|close|status)$/,
    );
    if (!match) {
      return null;
    }
    return {
      runId: decodeURIComponent(match[1] || ""),
      kind: match[2] || "",
    };
  }

  function parseLegacyBody(init) {
    if (!init || !init.body) {
      return {};
    }
    try {
      if (typeof init.body === "string") {
        return JSON.parse(init.body);
      }
    } catch (error) {
      return {};
    }
    return {};
  }

  function legacyProbePayload(kind, body, compat) {
    const runtime = window.__OBSERVABLE_RUNTIME;
    const pageId =
      (runtime && runtime.pageId) ||
      `page_${slugify(window.location.pathname || "legacy") || "legacy"}`;
    const navigationId =
      (runtime && runtime.navigationId) || `nav_${Date.now().toString(36)}`;
    const base = {
      instanceId: compat.instanceId,
      token: compat.token,
      pageId: pageId,
      navigationId: navigationId,
    };
    if (kind === "events") {
      return Object.assign(base, {
        events: body.events || [],
        meta: body.meta || {},
      });
    }
    if (kind === "finalize") {
      return Object.assign(base, body || {});
    }
    if (kind === "close") {
      const finalize = body.finalize || {};
      return Object.assign(base, {
        reason:
          body.reason ||
          finalize.run_end_reason ||
          finalize.done_reason ||
          "context_close",
        events: body.events || [],
        meta: body.meta || {},
        finalize: finalize,
      });
    }
    return base;
  }

  function legacyResponsePayload(kind, compat, envelope) {
    const data = envelope && envelope.data ? envelope.data : {};
    if (kind === "events") {
      return {
        ok: true,
        run_id: compat.instanceId,
        batch_events: data.batchEvents || 0,
        total_events: data.totalEvents || 0,
      };
    }
    if (kind === "finalize") {
      return Object.assign(
        {
          ok: true,
          run_id: compat.instanceId,
        },
        data.compileResult || {},
      );
    }
    if (kind === "close") {
      return Object.assign(
        {
          ok: true,
          run_id: compat.instanceId,
          forced: Boolean(data.forcedFinalize),
        },
        data.compileResult || {},
      );
    }
    return {
      ok: true,
      run_id: compat.instanceId,
    };
  }

  function installLegacyTransportCompat(probeConfig) {
    const compat = buildLegacyCompatConfig(probeConfig);
    if (!compat || window.__PROBE_LEGACY_COMPAT_INSTALLED) {
      return;
    }
    window.__PROBE_LEGACY_COMPAT_INSTALLED = true;

    const originalGet = URLSearchParams.prototype.get;
    URLSearchParams.prototype.get = function (name) {
      const value = originalGet.call(this, name);
      if (value) {
        return value;
      }
      if (name === "run_id") {
        return compat.instanceId;
      }
      if (name === "api_base") {
        return compat.apiBase;
      }
      if (name === "mode") {
        return compat.mode;
      }
      return value;
    };

    const originalFetch = window.fetch.bind(window);
    window.fetch = function (input, init) {
      const legacyInfo = legacyEndpointInfo(input);
      if (!legacyInfo || legacyInfo.runId !== compat.instanceId) {
        return originalFetch(input, init);
      }
      const routeMap = {
        events: compat.collectUrl,
        finalize: compat.finalizeUrl,
        close: compat.closeUrl,
        status: "/__probe__/health",
      };
      if (legacyInfo.kind === "status") {
        return originalFetch(routeMap.status, init).then((response) => {
          return new Response(
            JSON.stringify({ ok: response.ok, run_id: compat.instanceId }),
            {
              status: response.status,
              headers: { "Content-Type": "application/json" },
            },
          );
        });
      }
      const body = parseLegacyBody(init);
      const payload = legacyProbePayload(legacyInfo.kind, body, compat);
      return originalFetch(routeMap[legacyInfo.kind], {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        keepalive: init && init.keepalive ? init.keepalive : false,
      }).then(async (response) => {
        const envelope = await response.json().catch(() => ({}));
        return new Response(
          JSON.stringify(
            legacyResponsePayload(legacyInfo.kind, compat, envelope),
          ),
          {
            status: response.status,
            headers: { "Content-Type": "application/json" },
          },
        );
      });
    };

    const originalSendBeacon = navigator.sendBeacon
      ? navigator.sendBeacon.bind(navigator)
      : null;
    if (originalSendBeacon) {
      navigator.sendBeacon = function (urlValue, data) {
        const legacyInfo = legacyEndpointInfo(urlValue);
        if (!legacyInfo || legacyInfo.runId !== compat.instanceId) {
          return originalSendBeacon(urlValue, data);
        }
        const routeMap = {
          events: compat.collectUrl,
          finalize: compat.finalizeUrl,
          close: compat.closeUrl,
        };
        if (typeof Blob !== "undefined" && data instanceof Blob) {
          return originalSendBeacon(routeMap[legacyInfo.kind], data);
        }
        let parsedBody = {};
        if (typeof data === "string") {
          try {
            parsedBody = JSON.parse(data);
          } catch (error) {
            parsedBody = {};
          }
        }
        const payload = legacyProbePayload(legacyInfo.kind, parsedBody, compat);
        return originalSendBeacon(
          routeMap[legacyInfo.kind],
          new Blob([JSON.stringify(payload)], { type: "application/json" }),
        );
      };
    }
  }

  function createRuntime(config) {
    const url = new URL(window.location.href);
    const probeConfig =
      window.__PROBE_CONFIG__ && typeof window.__PROBE_CONFIG__ === "object"
        ? window.__PROBE_CONFIG__
        : null;
    installLegacyTransportCompat(probeConfig);
    const mode =
      (probeConfig && probeConfig.mode) ||
      url.searchParams.get("mode") ||
      "record";
    const runId =
      (probeConfig && probeConfig.instanceId) ||
      url.searchParams.get("run_id") ||
      "";
    const replayOf = url.searchParams.get("replay_of") || "";
    const origin =
      window.location.origin && window.location.origin !== "null"
        ? window.location.origin
        : "";
    const apiBase =
      (probeConfig && probeConfig.apiBase) ||
      url.searchParams.get("api_base") ||
      (origin ? `${origin}/__probe__` : "");
    const template = config.template;
    const recorderEnabled =
      mode !== "replay" &&
      Boolean(
        (probeConfig && probeConfig.instanceId && probeConfig.collectUrl) ||
        (runId && apiBase),
      );
    const navigationFlagKey = "__observable_internal_navigation__";

    const runtime = {
      template: template,
      config: config,
      runId: runId,
      mode: mode,
      replayOf: replayOf,
      apiBase: apiBase,
      probeConfig: probeConfig,
      instanceId: runId,
      probeToken:
        probeConfig && probeConfig.token ? String(probeConfig.token) : "",
      collectUrl:
        probeConfig && probeConfig.collectUrl
          ? String(probeConfig.collectUrl)
          : "/__probe__/collect",
      finalizeUrl:
        probeConfig && probeConfig.finalizeUrl
          ? String(probeConfig.finalizeUrl)
          : "/__probe__/finalize",
      closeUrl:
        probeConfig && probeConfig.closeUrl
          ? String(probeConfig.closeUrl)
          : "/__probe__/close",
      recorderEnabled: recorderEnabled,
      taskPath: "",
      taskLoaded: false,
      taskError: "",
      task: null,
      parsedGoal: {},
      state: {
        page_type: template,
        entry_path: normalizeEntryPath("", "", window.location.pathname),
        current_path: window.location.pathname,
        title: document.title,
      },
      events: [],
      eventSequence: 0,
      flushPromise: null,
      finalized: false,
      closeSent: false,
      pendingFinalize: null,
      lastWindowScrollY: -1,
      elementScrollTimers: new WeakMap(),
      internalNavigationPending: false,
      pageId: `page_${slugify(window.location.pathname || "root") || "root"}`,
      navigationId: `nav_${Date.now().toString(36)}`,
    };

    runtime.injectStatusUi = function () {
      if (document.getElementById("observable-status-pill")) {
        return;
      }
      const pill = document.createElement("div");
      pill.id = "observable-status-pill";
      pill.style.cssText =
        "position:fixed;top:14px;right:14px;z-index:2147483647;background:#0f172a;color:#fff;padding:8px 12px;border-radius:999px;font:12px/1.2 Arial,sans-serif;box-shadow:0 8px 24px rgba(15,23,42,.28);max-width:360px;";
      document.body.appendChild(pill);

      const banner = document.createElement("div");
      banner.id = "observable-status-banner";
      banner.style.cssText =
        "display:none;position:fixed;left:50%;top:72px;transform:translateX(-50%);z-index:2147483646;min-width:320px;max-width:760px;background:#ecfeff;color:#0f172a;border:1px solid #67e8f9;border-radius:14px;padding:14px 18px;box-shadow:0 12px 28px rgba(15,23,42,.18);font:14px/1.45 Arial,sans-serif;";
      banner.innerHTML =
        '<div id="observable-status-banner-title" style="font-weight:700;margin-bottom:4px;">Recorder active</div><div id="observable-status-banner-meta"></div>';
      document.body.appendChild(banner);
    };

    runtime.setStatus = function (message) {
      runtime.injectStatusUi();
      const pill = document.getElementById("observable-status-pill");
      if (pill) {
        pill.textContent = message;
      }
    };

    runtime.showBanner = function (title, meta) {
      runtime.injectStatusUi();
      const banner = document.getElementById("observable-status-banner");
      const titleNode = document.getElementById(
        "observable-status-banner-title",
      );
      const metaNode = document.getElementById("observable-status-banner-meta");
      if (titleNode) {
        titleNode.textContent = title || "";
      }
      if (metaNode) {
        metaNode.textContent = meta || "";
      }
      if (banner) {
        banner.style.display = "block";
      }
    };

    runtime.updateState = function (patch) {
      Object.assign(runtime.state, patch || {});
      runtime.state.current_path = window.location.pathname;
      runtime.state.title = document.title;
      window.__OBSERVABLE_STATE = runtime.collectState();
      window.__observableState = window.__OBSERVABLE_STATE;
    };

    runtime.collectState = function () {
      const state = {
        page_type: template,
        entry_path:
          runtime.state.entry_path ||
          (runtime.parsedGoal && runtime.parsedGoal.entry_path) ||
          window.location.pathname,
        current_path: window.location.pathname,
        title: document.title,
        sample_id:
          runtime.task && runtime.task.sample_id
            ? runtime.task.sample_id
            : runtime.state.sample_id || "",
        user_goal:
          runtime.task && runtime.task.user_goal
            ? runtime.task.user_goal
            : runtime.state.user_goal || "",
        parsed_goal: runtime.parsedGoal || {},
      };
      Object.assign(state, runtime.state);
      if (typeof runtime.config.collectState === "function") {
        Object.assign(state, runtime.config.collectState(runtime) || {});
      }
      return state;
    };

    runtime.metaPayload = function () {
      return {
        sample_id:
          runtime.task && runtime.task.sample_id
            ? runtime.task.sample_id
            : runtime.state.sample_id || "",
        task_json_path: runtime.taskPath || "",
        user_goal:
          runtime.task && runtime.task.user_goal
            ? runtime.task.user_goal
            : runtime.state.user_goal || "",
        parsed_goal: runtime.parsedGoal || {},
        entry_path:
          (runtime.parsedGoal && runtime.parsedGoal.entry_path) ||
          runtime.state.entry_path ||
          window.location.pathname,
        page_type: template,
        family_id:
          (runtime.parsedGoal && runtime.parsedGoal.family_id) ||
          runtime.state.family_id ||
          "",
        task_loaded: runtime.taskLoaded,
        task_error: runtime.taskError || "",
      };
    };

    runtime.labelOf = function (element) {
      if (!element || !element.id) {
        return "";
      }
      const label = document.querySelector(`label[for="${element.id}"]`);
      return label ? safeText(label.textContent, 120) : "";
    };

    runtime.captureTarget = function (element) {
      if (!(element instanceof Element)) {
        return {};
      }
      const value =
        "value" in element ? String(element.value || "").slice(0, 500) : "";
      const checked =
        "checked" in element ? Boolean(element.checked) : undefined;
      return {
        tag: (element.tagName || "").toLowerCase(),
        id: element.id || "",
        name: element.getAttribute("name") || "",
        type: element.getAttribute("type") || "",
        placeholder: element.getAttribute("placeholder") || "",
        role: element.getAttribute("role") || "",
        testId: element.getAttribute("data-pw") || "",
        label: runtime.labelOf(element),
        text: safeText(
          element.getAttribute("aria-label") ||
            element.getAttribute("title") ||
            element.textContent ||
            value,
          160,
        ),
        value: value,
        checked: checked,
        href: element.getAttribute("href") || "",
      };
    };

    runtime.queueEvent = function (type, target, extra) {
      if (!runtime.recorderEnabled || runtime.finalized) {
        return;
      }
      runtime.events.push({
        type: type,
        ts: new Date().toISOString(),
        seq: ++runtime.eventSequence,
        page_type: template,
        page: {
          url: window.location.href,
          path: window.location.pathname,
          title: document.title,
        },
        target: runtime.captureTarget(target),
        extra: extra || {},
      });
      if (runtime.events.length >= 12) {
        void runtime.flushEvents(true);
      }
    };

    runtime.buildProbeRequest = function (payload) {
      return Object.assign(
        {
          instanceId: runtime.instanceId,
          token: runtime.probeToken,
          pageId: runtime.pageId,
          navigationId: runtime.navigationId,
        },
        payload || {},
      );
    };

    runtime.resolveProbeUrl = function (routeValue) {
      if (!routeValue) {
        return "";
      }
      try {
        return new URL(routeValue, window.location.origin).toString();
      } catch (error) {
        return routeValue;
      }
    };

    runtime.sendProbePayload = async function (
      routeValue,
      payload,
      useKeepalive,
    ) {
      const endpoint = runtime.resolveProbeUrl(routeValue);
      if (!endpoint) {
        return { ok: false, error: "missing_probe_endpoint" };
      }
      try {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(runtime.buildProbeRequest(payload)),
          keepalive: Boolean(useKeepalive),
        });
        if (!response.ok) {
          return { ok: false, status: response.status };
        }
        const body = await response.json().catch(() => ({}));
        return body && typeof body === "object" && body.data ? body.data : body;
      } catch (error) {
        return { ok: false, error: String(error) };
      }
    };

    runtime.sendProbeBeacon = function (routeValue, payload) {
      const endpoint = runtime.resolveProbeUrl(routeValue);
      if (!endpoint) {
        return false;
      }
      return runtime.beaconJson(endpoint, runtime.buildProbeRequest(payload));
    };

    runtime.sendEventsBeacon = function (events, meta) {
      if (!runtime.recorderEnabled || !events || !events.length) {
        return false;
      }
      return runtime.sendProbeBeacon(runtime.collectUrl, {
        events: events,
        meta: meta || runtime.metaPayload(),
      });
    };

    runtime.flushEvents = async function (useKeepalive) {
      if (!runtime.recorderEnabled || !runtime.events.length) {
        return { ok: true, batch_events: 0 };
      }
      if (runtime.flushPromise) {
        return runtime.flushPromise;
      }
      const batch = runtime.events.splice(0, runtime.events.length);
      runtime.flushPromise = runtime
        .sendProbePayload(
          runtime.collectUrl,
          {
            events: batch,
            meta: runtime.metaPayload(),
          },
          useKeepalive,
        )
        .then((data) => {
          if (!data || data.ok === false) {
            runtime.events = batch.concat(runtime.events);
            runtime.setStatus("Recorder flush failed");
            return { ok: false, status: data && data.status ? data.status : 0 };
          }
          runtime.setStatus(
            `Recorder saved ${data.batchEvents || batch.length} event(s)`,
          );
          return data;
        })
        .catch((error) => {
          runtime.events = batch.concat(runtime.events);
          runtime.setStatus(`Recorder flush failed: ${error}`);
          return { ok: false, error: String(error) };
        })
        .finally(() => {
          runtime.flushPromise = null;
        });
      return runtime.flushPromise;
    };

    runtime.beaconJson = function (urlValue, payload) {
      const body = JSON.stringify(payload);
      if (navigator.sendBeacon) {
        try {
          return navigator.sendBeacon(
            urlValue,
            new Blob([body], { type: "application/json" }),
          );
        } catch (error) {
          return false;
        }
      }
      try {
        fetch(urlValue, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: body,
          keepalive: true,
        }).catch(() => {});
        return true;
      } catch (error) {
        return false;
      }
    };

    runtime.markInternalNavigation = function () {
      runtime.internalNavigationPending = true;
      try {
        sessionStorage.setItem(navigationFlagKey, "1");
        window.setTimeout(() => {
          try {
            runtime.internalNavigationPending = false;
            if (sessionStorage.getItem(navigationFlagKey) === "1") {
              sessionStorage.removeItem(navigationFlagKey);
            }
          } catch (error) {}
        }, 2000);
      } catch (error) {}
    };

    runtime.consumeInternalNavigationFlag = function () {
      const localValue = Boolean(runtime.internalNavigationPending);
      runtime.internalNavigationPending = false;
      try {
        const value = sessionStorage.getItem(navigationFlagKey) === "1";
        sessionStorage.removeItem(navigationFlagKey);
        return localValue || value;
      } catch (error) {
        return localValue;
      }
    };

    runtime.navigateInternal = async function (rawHref) {
      const nextHref = withPreservedQuery(rawHref, runtime);
      runtime.markInternalNavigation();
      try {
        await runtime.flushEvents(true);
      } catch (error) {}
      window.setTimeout(() => {
        window.location.assign(nextHref);
      }, 0);
    };

    runtime.requestFinalize = async function (reason, extraState) {
      if (!runtime.recorderEnabled || runtime.finalized) {
        return false;
      }
      if (!runtime.taskLoaded) {
        runtime.pendingFinalize = {
          reason: reason,
          extraState: extraState || {},
        };
        runtime.setStatus("Waiting for task file before finalize");
        return false;
      }
      runtime.finalized = true;
      runtime.updateState(extraState || {});
      const finalState = runtime.collectState();
      await runtime.flushEvents(true);
      const remainingEvents = runtime.events.splice(0, runtime.events.length);
      runtime.setStatus("Finalizing run...");
      runtime.showBanner("Task completed", reason || "completion_oracle");
      try {
        const data = await runtime.sendProbePayload(
          runtime.finalizeUrl,
          {
            done: true,
            doneReason: reason,
            pageType: template,
            entryPath: finalState.entry_path || window.location.pathname,
            finalState: finalState,
            events: remainingEvents,
            meta: runtime.metaPayload(),
            done_reason: reason,
            force_finalize: false,
            finalize_source: "completion_oracle",
            run_end_reason: reason,
            page_type: template,
            entry_path: finalState.entry_path || window.location.pathname,
            final_state: finalState,
          },
          true,
        );
        if (!data || data.ok === false) {
          runtime.finalized = false;
          runtime.setStatus(
            `Finalize failed: ${data && data.status ? data.status : "request"}`,
          );
          return false;
        }
        runtime.setStatus(
          `Compiler output ready: ${(data.compileResult && data.compileResult.generated_script) || "generated/replay_from_events.py"}`,
        );
        return true;
      } catch (error) {
        runtime.finalized = false;
        runtime.setStatus(`Finalize failed: ${error}`);
        return false;
      }
    };

    runtime.sendClose = function (reason) {
      if (!runtime.recorderEnabled || runtime.finalized || runtime.closeSent) {
        return;
      }
      const isInternalNavigation = runtime.consumeInternalNavigationFlag();
      if (isInternalNavigation) {
        if (runtime.events.length) {
          runtime.sendEventsBeacon(
            runtime.events.splice(0, runtime.events.length),
            runtime.metaPayload(),
          );
        }
        return;
      }
      runtime.closeSent = true;
      const finalState = runtime.collectState();
      runtime.sendProbeBeacon(runtime.closeUrl, {
        reason: reason || "context_close",
        events: runtime.events.splice(0, runtime.events.length),
        meta: runtime.metaPayload(),
        finalize: {
          done: false,
          done_reason: "context_close",
          force_finalize: true,
          finalize_source: "context_close",
          run_end_reason: reason || "context_close",
          page_type: template,
          entry_path: finalState.entry_path || window.location.pathname,
          final_state: finalState,
        },
      });
    };

    runtime.applyDomPatches = function (rootNode) {
      if (typeof runtime.config.patchDom === "function") {
        runtime.config.patchDom(runtime, rootNode || document);
      }
      const anchors = (rootNode || document).querySelectorAll
        ? (rootNode || document).querySelectorAll("a[href]")
        : [];
      anchors.forEach((anchor) => {
        const href = anchor.getAttribute("href") || "";
        anchor.setAttribute("href", withPreservedQuery(href, runtime));
      });
      const forms = (rootNode || document).querySelectorAll
        ? (rootNode || document).querySelectorAll("form[action]")
        : [];
      forms.forEach((form) => {
        const action = form.getAttribute("action") || "";
        form.setAttribute("action", withPreservedQuery(action, runtime));
      });
    };

    runtime.installRecorderListeners = function () {
      document.addEventListener(
        "click",
        (event) => {
          const target =
            event.target && event.target.closest
              ? event.target.closest(
                  "a,button,input,textarea,select,li,[role='button']",
                ) || event.target
              : event.target;
          if (
            target &&
            target instanceof Element &&
            target.tagName.toLowerCase() === "a"
          ) {
            const href = target.getAttribute("href") || "";
            if (isInternalTarget(href)) {
              runtime.markInternalNavigation();
            }
          }
          runtime.queueEvent("click", target, {});
        },
        true,
      );

      document.addEventListener(
        "submit",
        (event) => {
          const form = event.target;
          if (form && form.getAttribute) {
            const action = form.getAttribute("action") || window.location.href;
            if (isInternalTarget(action)) {
              runtime.markInternalNavigation();
            }
          }
          runtime.queueEvent("submit", form, {});
        },
        true,
      );

      document.addEventListener(
        "input",
        (event) => {
          const target = event.target;
          if (!target) {
            return;
          }
          const extra = {
            value: "value" in target ? String(target.value || "") : "",
            checked: "checked" in target ? Boolean(target.checked) : undefined,
          };
          runtime.queueEvent("input", target, extra);
        },
        true,
      );

      document.addEventListener(
        "change",
        (event) => {
          const target = event.target;
          if (!target) {
            return;
          }
          const extra = {
            value: "value" in target ? String(target.value || "") : "",
            checked: "checked" in target ? Boolean(target.checked) : undefined,
          };
          runtime.queueEvent("change", target, extra);
        },
        true,
      );

      document.addEventListener(
        "focusin",
        (event) => runtime.queueEvent("focusin", event.target, {}),
        true,
      );
      document.addEventListener(
        "focusout",
        (event) => runtime.queueEvent("focusout", event.target, {}),
        true,
      );
      document.addEventListener(
        "keydown",
        (event) =>
          runtime.queueEvent("keydown", event.target, { key: event.key }),
        true,
      );

      let windowScrollTimer = null;
      window.addEventListener(
        "scroll",
        () => {
          if (windowScrollTimer) {
            return;
          }
          windowScrollTimer = window.setTimeout(() => {
            windowScrollTimer = null;
            const y = Math.round(window.scrollY || window.pageYOffset || 0);
            if (y === runtime.lastWindowScrollY) {
              return;
            }
            runtime.lastWindowScrollY = y;
            runtime.queueEvent("scroll_window", document.documentElement, {
              x: Math.round(window.scrollX || 0),
              y: y,
            });
          }, 120);
        },
        { passive: true },
      );

      document.addEventListener(
        "scroll",
        (event) => {
          const element = event.target;
          if (!(element instanceof Element)) {
            return;
          }
          if (
            element === document.documentElement ||
            element === document.body
          ) {
            return;
          }
          if (element.scrollHeight <= element.clientHeight + 4) {
            return;
          }
          const previous = runtime.elementScrollTimers.get(element);
          if (previous) {
            window.clearTimeout(previous);
          }
          const timer = window.setTimeout(() => {
            runtime.elementScrollTimers.delete(element);
            runtime.queueEvent("scroll_element", element, {
              scrollTop: Math.round(element.scrollTop),
              scrollLeft: Math.round(element.scrollLeft),
            });
          }, 120);
          runtime.elementScrollTimers.set(element, timer);
        },
        true,
      );

      window.addEventListener("pagehide", () => runtime.sendClose("pagehide"));
      window.addEventListener("beforeunload", () =>
        runtime.sendClose("beforeunload"),
      );
      window.setInterval(
        () => {
          void runtime.flushEvents(false);
        },
        (probeConfig && probeConfig.flushIntervalMs) || 1200,
      );
    };

    runtime.applyLoadedTask = function (task, taskPath) {
      runtime.taskLoaded = true;
      runtime.taskError = "";
      runtime.task = task;
      runtime.taskPath = taskPath || runtime.taskPath;
      runtime.parsedGoal =
        typeof runtime.config.parseGoal === "function"
          ? runtime.config.parseGoal(task, runtime) || {}
          : parseGoal(
              task.user_goal,
              template,
              runtime.config.goalOptions || {},
            );
      runtime.parsedGoal.entry_path = normalizeEntryPath(
        runtime.parsedGoal.entry_path,
        task.sample_id || "",
        window.location.pathname,
      );
      runtime.updateState({
        sample_id: task.sample_id || "",
        user_goal: task.user_goal || "",
        family_id:
          runtime.parsedGoal.family_id || runtime.state.family_id || "",
        entry_path:
          runtime.parsedGoal.entry_path ||
          normalizeEntryPath(
            "",
            task.sample_id || "",
            window.location.pathname,
          ),
      });
      runtime.setStatus("Recorder armed");
      if (typeof runtime.config.afterTaskLoaded === "function") {
        runtime.config.afterTaskLoaded(runtime);
      }
      if (runtime.pendingFinalize) {
        const pending = runtime.pendingFinalize;
        runtime.pendingFinalize = null;
        window.setTimeout(() => {
          void runtime.requestFinalize(pending.reason, pending.extraState);
        }, 0);
      }
    };

    runtime.loadTask = async function () {
      if (!runtime.recorderEnabled && !runtime.config.loadTaskInReplay) {
        return;
      }
      if (typeof runtime.config.resolveTaskInfo === "function") {
        const taskInfo = (await runtime.config.resolveTaskInfo(runtime)) || {};
        runtime.taskPath = taskInfo.taskPath || taskInfo.taskUrl || "";
      } else {
        runtime.taskPath = new URL(
          "../task.json",
          window.location.href,
        ).toString();
      }
      if (!runtime.taskPath) {
        runtime.taskLoaded = false;
        runtime.taskError = "missing task path";
        runtime.updateState({
          entry_path: runtime.state.entry_path || window.location.pathname,
        });
        runtime.setStatus("Recorder armed without task file");
        runtime.showBanner("Task load failed", "missing task path");
        return;
      }
      const taskCacheKey = `__observable_task__:${runtime.taskPath}`;
      try {
        const cached = sessionStorage.getItem(taskCacheKey);
        if (cached) {
          const cachedTask = JSON.parse(cached);
          if (
            cachedTask &&
            typeof cachedTask === "object" &&
            !Array.isArray(cachedTask)
          ) {
            runtime.applyLoadedTask(cachedTask, runtime.taskPath);
            return;
          }
        }
      } catch (error) {}
      try {
        const response = await fetch(runtime.taskPath, { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`task file ${response.status}`);
        }
        const taskText = await response.text();
        const task =
          typeof runtime.config.parseTaskText === "function"
            ? runtime.config.parseTaskText(taskText, runtime, runtime.taskPath)
            : JSON.parse(taskText);
        if (!task || typeof task !== "object" || Array.isArray(task)) {
          throw new Error("task file did not resolve to an object");
        }
        try {
          sessionStorage.setItem(taskCacheKey, JSON.stringify(task));
        } catch (error) {}
        runtime.applyLoadedTask(task, runtime.taskPath);
      } catch (error) {
        runtime.taskLoaded = false;
        runtime.taskError = String(error);
        runtime.updateState({
          entry_path: runtime.state.entry_path || window.location.pathname,
        });
        runtime.setStatus("Recorder armed without task file");
        runtime.showBanner("Task load failed", String(error));
      }
    };

    runtime.init = function () {
      window.__OBSERVABLE_RUNTIME = runtime;
      onReady(async () => {
        runtime.injectStatusUi();
        runtime.setStatus(
          runtime.recorderEnabled ? "Recorder arming..." : "Replay mode",
        );
        runtime.applyDomPatches(document);
        if (typeof runtime.config.install === "function") {
          runtime.config.install(runtime);
        }
        const observer = new MutationObserver(() => {
          runtime.applyDomPatches(document);
        });
        observer.observe(document.documentElement, {
          childList: true,
          subtree: true,
        });
        runtime.installRecorderListeners();
        await runtime.loadTask();
        runtime.updateState({});
        if (runtime.recorderEnabled) {
          runtime.queueEvent(
            "page_ready",
            document.body || document.documentElement,
            {
              task_loaded: runtime.taskLoaded,
              task_error: runtime.taskError || "",
            },
          );
          void runtime.flushEvents(false);
        }
        if (!runtime.recorderEnabled) {
          runtime.setStatus("Replay mode");
        }
      });
    };

    runtime.withPreservedQuery = function (rawHref) {
      return withPreservedQuery(rawHref, runtime);
    };

    runtime.isTargetContact = function (value) {
      const expected = String(
        (runtime.parsedGoal && runtime.parsedGoal.target_contact) || "",
      )
        .trim()
        .toLowerCase();
      const actual = String(value || "")
        .trim()
        .toLowerCase();
      if (!expected) {
        return true;
      }
      if (!actual) {
        return false;
      }
      return (
        actual === expected ||
        actual.includes(expected) ||
        expected.includes(actual)
      );
    };

    return runtime;
  }

  window.ObservableCore = {
    createRuntime: createRuntime,
    onReady: onReady,
    slugify: slugify,
    normalizeWhitespace: normalizeWhitespace,
    parseGoal: parseGoal,
    normalizeEntryPath: normalizeEntryPath,
    withPreservedQuery: withPreservedQuery,
  };
})();
