/* kunji website: theme toggle, mobile menu, copy buttons, live stats, terminal demos. */
(function () {
  "use strict";
  var root = document.documentElement;
  var THEME_KEY = "starlight-theme"; // same key as the docs, so both stay in sync

  // Theme -----------------------------------------------------------------------
  function setTheme(theme) {
    root.dataset.theme = theme;
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) {}
    document.querySelectorAll(".theme-btn").forEach(function (b) {
      b.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    });
  }
  document.querySelectorAll(".theme-btn").forEach(function (btn) {
    btn.setAttribute("aria-pressed", root.dataset.theme === "dark" ? "true" : "false");
    btn.addEventListener("click", function () {
      setTheme(root.dataset.theme === "dark" ? "light" : "dark");
    });
  });

  // Header: shadow line when scrolled, mobile menu --------------------------------
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("scrolled", window.scrollY > 4); };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    var menuBtn = header.querySelector(".menu-btn");
    var close = function () { header.classList.remove("open"); if (menuBtn) menuBtn.setAttribute("aria-expanded", "false"); };
    if (menuBtn) {
      menuBtn.addEventListener("click", function () {
        var open = !header.classList.contains("open");
        header.classList.toggle("open", open);
        menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
      });
      header.querySelectorAll(".nav a").forEach(function (a) { a.addEventListener("click", close); });
      document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
    }
  }

  // Copy buttons -------------------------------------------------------------------
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    var label = btn.textContent;
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy");
      var done = function () { btn.textContent = btn.getAttribute("data-copied") || "Copied"; setTimeout(function () { btn.textContent = label; }, 1600); };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done, function () { fallback(text); done(); });
      } else { fallback(text); done(); }
    });
  });
  function fallback(text) {
    var t = document.createElement("textarea");
    t.value = text; t.setAttribute("readonly", ""); t.style.position = "absolute"; t.style.left = "-9999px";
    document.body.appendChild(t); t.select();
    try { document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(t);
  }

  // Live GitHub stars and latest version (silent on failure) -------------------------
  function cached(key, url, pick, done) {
    try { var hit = sessionStorage.getItem(key); if (hit) return done(hit); } catch (e) {}
    fetch(url, { headers: { Accept: "application/json" } })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (d) { var v = pick(d); if (v == null) return; try { sessionStorage.setItem(key, v); } catch (e) {} done(String(v)); })
      .catch(function () {});
  }
  cached("kunji-stars", "https://api.github.com/repos/testwithsuraj/kunji", function (d) { return d.stargazers_count; }, function (n) {
    document.querySelectorAll("[data-stars]").forEach(function (el) {
      el.querySelector("[data-stars-count]").textContent = Number(n) >= 1000 ? (Number(n) / 1000).toFixed(1) + "k" : n;
      el.hidden = false;
    });
  });
  cached("kunji-version", "https://pypi.org/pypi/kunji/json", function (d) { return d.info && d.info.version; }, function (v) {
    document.querySelectorAll("[data-version]").forEach(function (el) {
      el.textContent = (el.getAttribute("data-version") || "Version") + " " + v;
    });
  });

  // Terminal demos ---------------------------------------------------------------------
  var screen = document.getElementById("screen");
  if (!screen) return;
  var tabs = Array.prototype.slice.call(document.querySelectorAll(".tab"));
  var bars = Array.prototype.slice.call(document.querySelectorAll(".progress i"));
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function strip(title, head, row) {
    var h = head.map(function (c) { return "<th" + (c.opt ? ' class="opt"' : "") + ">" + c.t + "</th>"; }).join("");
    var r = row.map(function (c) { return "<td" + (c.cls ? ' class="' + c.cls + '"' : "") + ">" + c.t + "</td>"; }).join("");
    return '<div class="strip"><span class="chip">' + title + "</span><table><tr>" + h + "</tr><tr>" + r + "</tr></table></div>";
  }
  var chatHeader = strip("kunji chat",
    [{ t: "Provider" }, { t: "Model" }, { t: "Budget", opt: 1 }, { t: "State" }],
    [{ t: "Anthropic" }, { t: "claude-sonnet" }, { t: "$0.38 / $2", cls: "opt" }, { t: "READY", cls: "ok" }]);
  var gap = '<div class="gap"></div>';

  var DEMOS = {
    chat: [
      { sh: "kunji chat" },
      { html: chatHeader, wait: 300 },
      { html: '<p class="ln dim">enter send · / commands · ctrl+d menu</p>' + gap, wait: 400 },
      { you: "what does kunji mean?" },
      { stream: "Kunji (कुंजी) is Hindi for “key” — your own API keys open every model from one place." },
      { html: '<p class="ln dim ans">claude-sonnet · 14 in · 23 out · $0.0004 · 1.1s</p>' + gap, wait: 500 },
      { you: "/cost" },
      { html: strip("Cost", [{ t: "Session" }, { t: "Today" }, { t: "Price / 1M", opt: 1 }],
          [{ t: "$0.0004" }, { t: "$0.12" }, { t: "$3 in · $15 out", cls: "opt" }]), wait: 1200 },
    ],
    switch: [
      { you: "write a regex for an Indian PIN code" },
      { stream: "^[1-9][0-9]{5}$ — six digits, and the first one can't be 0." },
      { html: '<p class="ln dim ans">claude-sonnet · 19 in · 18 out · $0.0003 · 0.9s</p>' + gap, wait: 500 },
      { you: "/model groq:llama-3.3-70b-versatile" },
      { html: '<p class="ln"><span class="ok">✓</span> Switched to groq:llama-3.3-70b-versatile <span class="dim"> conversation kept</span></p>' + gap, wait: 500 },
      { you: "is that right? check it" },
      { stream: "Yes. Indian PIN codes are 6 digits and never start with 0, so ^[1-9][0-9]{5}$ is correct." },
      { html: '<p class="ln dim ans">llama-3.3-70b · 61 in · 24 out · <$0.0001 · 0.4s</p>', wait: 1200 },
    ],
    compare: [
      { sh: 'kunji compare "explain recursion in one line" -m openai:gpt-4o-mini -m groq:llama-3.3-70b-versatile' },
      { lanes: [["openai:gpt-4o-mini", 1.9, "1.9s · 31 tok"], ["groq:llama-3.3-70b-versatile", 0.6, "0.6s · 27 tok"]] },
      { html: gap + strip("Compare", [{ t: "Model" }, { t: "Time" }, { t: "Cost", opt: 1 }, { t: "" }],
          [{ t: "groq:llama-3.3-70b" }, { t: "0.6s" }, { t: "<$0.0001", cls: "opt" }, { t: "fastest", cls: "ok" }]), wait: 1400 },
    ],
    commit: [
      { sh: "git add ." },
      { sh: "kunji @commit" },
      { html: '<p class="ln dim">  @commit: Write a commit message for your staged git changes</p>' + gap, wait: 400 },
      { stream: "Add password reset by email\n\nUsers can now request a reset link from the login page. Links expire after 30 minutes." },
      { html: '<p class="ln dim ans">claude-sonnet · 812 in · 34 out · $0.0030 · 1.4s</p>', wait: 1400 },
    ],
    budget: [
      { sh: "kunji budget set openai 200" },
      { html: '<p class="ln"><span class="ok">✓</span> Daily budget for openai: ₹200.00</p>' + gap, wait: 600 },
      { sh: "kunji chat -m openai:gpt-4o" },
      { you: "summarise this 40-page report" },
      { html: '<p class="ln warn">! 80% of today’s budget used for OpenAI: ₹161.40 / ₹200.00</p>', wait: 700 },
      { stream: "Here are the key points: …" },
      { html: '<p class="ln dim ans">gpt-4o · 18,204 in · 512 out · ₹8.20 · 6.2s</p>', wait: 1400 },
    ],
  };
  var ORDER = tabs.map(function (t) { return t.getAttribute("data-demo"); });

  var run = 0, current = 0, userPicked = false, visible = true;

  function el(html) { var d = document.createElement("div"); d.innerHTML = html; return Array.prototype.slice.call(d.childNodes); }
  function sleep(ms, id) { return new Promise(function (r) { setTimeout(function () { r(id === run); }, ms); }); }
  function line(cls, text) { var p = document.createElement("p"); p.className = "ln " + cls; p.textContent = text || ""; screen.appendChild(p); return p; }
  function keepBottom() { screen.scrollTop = screen.scrollHeight; }

  function select(i) {
    current = i;
    tabs.forEach(function (t, n) { t.setAttribute("aria-selected", n === i ? "true" : "false"); t.tabIndex = n === i ? 0 : -1; });
    bars.forEach(function (b, n) { b.className = n < i ? "done" : n === i ? "now" : ""; });
  }

  function renderStatic(name) {
    screen.innerHTML = "";
    DEMOS[name].forEach(function (s) {
      if (s.html) el(s.html).forEach(function (n) { screen.appendChild(n); });
      if (s.sh) line("sh", s.sh);
      if (s.you) line("you", s.you);
      if (s.stream) line("ans", s.stream);
      if (s.lanes) s.lanes.forEach(function (l) { var p = line("", ""); p.innerHTML = '<span class="ok">✓</span> ' + l[0] + ' <span class="dim">' + l[2] + "</span>"; });
    });
  }

  async function play(i) {
    var id = ++run;
    select(i);
    var name = ORDER[i];
    if (reduce) { renderStatic(name); return; }
    screen.innerHTML = "";
    var steps = DEMOS[name];
    for (var s = 0; s < steps.length; s++) {
      var st = steps[s];
      while (!visible) { if (!(await sleep(300, id))) return; }
      if (st.html) { el(st.html).forEach(function (n) { screen.appendChild(n); }); keepBottom(); if (!(await sleep(st.wait || 300, id))) return; }
      if (st.sh || st.you) {
        var text = st.sh || st.you, p = line(st.sh ? "sh" : "you", "");
        for (var c = 1; c <= text.length; c++) { p.textContent = text.slice(0, c); if (!(await sleep(text.length > 60 ? 14 : 34, id))) return; }
        keepBottom();
        if (!(await sleep(350, id))) return;
      }
      if (st.stream) {
        var a = line("ans", ""), words = st.stream.split(" ");
        for (var w = 1; w <= words.length; w++) { a.textContent = words.slice(0, w).join(" "); keepBottom(); if (!(await sleep(60, id))) return; }
      }
      if (st.lanes) {
        var frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏", rows = st.lanes.map(function (l) { return line("", ""); });
        var t0 = Date.now(), finished = 0;
        while (finished < st.lanes.length) {
          finished = 0;
          var t = (Date.now() - t0) / 1000;
          st.lanes.forEach(function (l, n) {
            if (t >= l[1]) { finished++; rows[n].innerHTML = '<span class="ok">✓</span> ' + l[0] + ' <span class="dim">' + l[2] + "</span>"; }
            else { rows[n].innerHTML = '<span class="ok">' + frames[Math.floor(t * 12) % frames.length] + "</span> " + l[0] + ' <span class="dim">' + t.toFixed(1) + "s</span>"; }
          });
          if (!(await sleep(80, id))) return;
        }
      }
    }
    line("you", "").innerHTML = '<span class="caret">&nbsp;</span>';
    if (!userPicked && (await sleep(2600, id))) play((i + 1) % ORDER.length);
  }

  tabs.forEach(function (tab, i) {
    tab.addEventListener("click", function () { userPicked = true; play(i); });
    tab.addEventListener("keydown", function (e) {
      var k = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!k) return;
      e.preventDefault();
      var n = (i + k + tabs.length) % tabs.length;
      tabs[n].focus(); userPicked = true; play(n);
    });
  });
  var replay = document.getElementById("replay");
  if (replay) replay.addEventListener("click", function () { play(current); });

  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) { visible = entries[0].isIntersecting; }).observe(screen);
  }
  play(0);
})();
// Fetch contributors from GitHub API
async function loadContributors() {
  const grid = document.getElementById('contributors-grid');
  if (!grid) return;

  try {
    const response = await fetch('https://api.github.com/repos/testwithsuraj/kunji/contributors');
    const contributors = await response.json();
    
    grid.innerHTML = '';
    
    contributors.forEach(user => {
      if (user.type === 'User') {
        const avatar = document.createElement('a');
        avatar.href = user.html_url;
        avatar.target = '_blank';
        avatar.style.display = 'inline-block';
        
        const img = document.createElement('img');
        img.src = user.avatar_url;
        img.style.width = '50px';
        img.style.height = '50px';
        img.style.borderRadius = '50%';
        img.style.border = '2px solid #333';
        
        avatar.appendChild(img);
        grid.appendChild(avatar);
      }
    });
  } catch (error) {
    grid.innerHTML = '<p>Could not load contributors right now.</p>';
  }
}

document.addEventListener('DOMContentLoaded', loadContributors);
