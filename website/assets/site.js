// Woodcore's website (website/build.py): copy buttons, the 1 · 2 · 3 levels of an example, the sidebar's search, the menu on a phone, and the table of contents following the reading. Every page works without it; this only adds.
(function () {
  "use strict";
  var html = document.documentElement;
  var root = html.getAttribute("data-root") || "./";
  var lang = html.getAttribute("data-lang") || "fr";
  function word(key, fallback) { return html.getAttribute("data-t-" + key) || fallback; }

  // A language chosen by its switch is remembered, so the site's root opens in it next time.
  document.querySelectorAll(".langs a[data-lang]").forEach(function (a) {
    a.addEventListener("click", function () {
      try { localStorage.setItem("woodcore-lang", a.getAttribute("data-lang")); } catch (e) { /* private window */ }
    });
  });

  // Copy buttons: the code of the block they sit on.
  document.querySelectorAll("[data-copy]").forEach(function (button) {
    button.addEventListener("click", function () {
      var code = button.parentElement.querySelector("pre code");
      if (!code) return;
      var text = code.innerText;
      var done = function () {
        var label = button.textContent;
        button.textContent = word("copied", "Copied");
        button.classList.add("done");
        setTimeout(function () { button.textContent = label; button.classList.remove("done"); }, 1400);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done, function () {});
      } else {
        var area = document.createElement("textarea");
        area.value = text; document.body.appendChild(area); area.select();
        try { document.execCommand("copy"); done(); } catch (e) {}
        document.body.removeChild(area);
      }
    });
  });

  // The levels of an example: one page shown at a time.
  document.querySelectorAll("[data-levels]").forEach(function (preview) {
    var buttons = preview.querySelectorAll(".levels button");
    buttons.forEach(function (button) {
      button.addEventListener("click", function () {
        var level = button.getAttribute("data-level");
        buttons.forEach(function (b) { b.setAttribute("aria-selected", b === button ? "true" : "false"); });
        preview.querySelectorAll(".paper").forEach(function (paper) {
          paper.hidden = paper.getAttribute("data-level") !== level;
        });
      });
    });
  });

  // The menu on a narrow screen.
  var toggle = document.querySelector("[data-menu]");
  if (toggle) {
    toggle.addEventListener("click", function () { document.body.classList.toggle("menu-open"); });
    document.addEventListener("click", function (event) {
      if (!document.body.classList.contains("menu-open")) return;
      if (event.target.closest("[data-sidebar]") || event.target.closest("[data-menu]")) return;
      document.body.classList.remove("menu-open");
    });
  }

  // The sidebar's search: the index of this language, loaded the first time it is used.
  var input = document.querySelector("[data-search]");
  var results = document.querySelector("[data-results]");
  var sidenav = document.querySelector("[data-sidenav]");
  var index = null, loading = null, selected = -1;

  function load() {
    if (index || loading) return loading;
    loading = fetch(root + "search/" + lang + ".json?v=" + (html.getAttribute("data-stamp") || "")).then(function (r) { return r.json(); })
      .then(function (data) { index = data; return data; }).catch(function () { index = []; });
    return loading;
  }
  function normalise(text) {
    return String(text || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }
  function score(entry, terms) {
    if (!entry._n) entry._n = { t: normalise(entry.t), s: normalise([entry.s, entry.a, entry.c, entry.x].join(" ")) };
    var title = entry._n.t, text = entry._n.s, total = 0;
    for (var i = 0; i < terms.length; i++) {
      var term = terms[i];
      if (title === term) total += 100;
      else if (title.indexOf(term) === 0) total += 40;
      else if (title.indexOf(term) >= 0) total += 25;
      else if (text.indexOf(term) >= 0) total += 6;
      else return 0;
    }
    if (entry.k === "cmd") total += 2;
    return total;
  }
  function render(query) {
    var terms = normalise(query).split(/\s+/).filter(Boolean);
    results.innerHTML = "";
    selected = -1;
    if (!terms.length) { results.hidden = true; sidenav.hidden = false; return; }
    var found = (index || []).map(function (e) { return { e: e, s: score(e, terms) }; })
      .filter(function (x) { return x.s > 0; }).sort(function (a, b) { return b.s - a.s; }).slice(0, 30);
    sidenav.hidden = true; results.hidden = false;
    if (!found.length) {
      var li = document.createElement("li"); li.className = "empty"; li.textContent = word("empty", "No results");
      results.appendChild(li); return;
    }
    found.forEach(function (x) {
      var e = x.e, li = document.createElement("li"), a = document.createElement("a");
      a.href = root + e.u;
      var title = document.createElement("span");
      title.className = "r-title" + (e.k === "cmd" ? " mono" : ""); title.textContent = e.t;
      var meta = document.createElement("span");
      meta.className = "r-meta"; meta.textContent = [word(e.k, ""), e.c].filter(Boolean).join(" · ");
      a.appendChild(title); a.appendChild(meta);
      if (e.s) { var text = document.createElement("span"); text.className = "r-text"; text.textContent = e.s; a.appendChild(text); }
      li.appendChild(a); results.appendChild(li);
    });
  }
  function move(step) {
    var links = results.querySelectorAll("a");
    if (!links.length) return;
    if (selected >= 0) links[selected].classList.remove("selected");
    selected = (selected + step + links.length) % links.length;
    links[selected].classList.add("selected");
    links[selected].scrollIntoView({ block: "nearest" });
  }
  if (input && results && sidenav) {
    input.addEventListener("focus", load);
    input.addEventListener("input", function () {
      var query = input.value;
      if (index) render(query); else load().then(function () { render(input.value); });
    });
    input.addEventListener("keydown", function (event) {
      if (event.key === "ArrowDown") { event.preventDefault(); move(1); }
      else if (event.key === "ArrowUp") { event.preventDefault(); move(-1); }
      else if (event.key === "Enter") {
        var links = results.querySelectorAll("a");
        var target = links[selected >= 0 ? selected : 0];
        if (target) { event.preventDefault(); location.href = target.href; }
      } else if (event.key === "Escape") { input.value = ""; render(""); input.blur(); }
    });
    document.addEventListener("keydown", function (event) {
      var typing = /INPUT|TEXTAREA|SELECT/.test((document.activeElement || {}).tagName || "");
      if ((event.key === "/" && !typing) || (event.key.toLowerCase() === "k" && (event.ctrlKey || event.metaKey))) {
        event.preventDefault();
        document.body.classList.add("menu-open");
        input.focus(); input.select();
      }
    });
  }

  // The table of contents lights the section being read.
  var toc = document.querySelectorAll(".toc a[href^='#']");
  if (toc.length && "IntersectionObserver" in window) {
    var byId = {};
    toc.forEach(function (a) { byId[decodeURIComponent(a.getAttribute("href").slice(1))] = a; });
    var headings = Object.keys(byId).map(function (id) { return document.getElementById(id); }).filter(Boolean);
    var current = null;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          if (current) current.classList.remove("current");
          current = byId[entry.target.id];
          if (current) current.classList.add("current");
        }
      });
    }, { rootMargin: "-70px 0px -70% 0px" });
    headings.forEach(function (h) { observer.observe(h); });
  }

  // The active entry of the sidebar in view -- the sidebar scrolled, never the page (scrollIntoView would move both).
  var active = document.querySelector(".sidenav a.active");
  var bar = document.querySelector("[data-sidebar]");
  if (active && bar) {
    var offset = active.getBoundingClientRect().top - bar.getBoundingClientRect().top;
    if (offset > bar.clientHeight - 40) bar.scrollTop += offset - bar.clientHeight / 2;
  }
})();
