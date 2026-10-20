/* beta_site_me — js cru. sem dependências. */
(function () {
  "use strict";

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- texto a ser "escrito" ---------- */
  var typed = $("#typed");
  if (typed) {
    var full = typed.textContent.trim();
    if (reduceMotion) typed.textContent = full;
    else {
      var n = 0;
      var t = setInterval(function () {
        typed.textContent = full.slice(0, ++n);
        if (n >= full.length) clearInterval(t);
      }, 35);
    }
  }

  /* ---------- status ---------- */
  var started = Date.now();
  var up = $("#uptime");
  function pad(x) { return (x < 10 ? "0" : "") + x; }
  if (up) setInterval(function () {
    var s = ((Date.now() - started) / 1000) | 0;
    up.textContent = pad((s / 3600) | 0) + ":" + pad(((s % 3600) / 60) | 0) + ":" + pad(s % 60);
  }, 1000);

  var vis = $("#visitor");
  if (vis) vis.textContent = "anon-" + Math.random().toString(16).slice(2, 8);

  var year = $("#year");
  if (year) year.textContent = new Date().getFullYear();

  /* ---------- lista de posts + filtros ---------- */
  var list = $("#post-list");
  var filters = $("#filters");
  var posts = typeof POSTS !== "undefined" ? POSTS : [];

  function renderPosts(tag) {
    if (!list) return;
    list.textContent = "";
    var shown = posts.filter(function (p) { return !tag || p.tags.indexOf(tag) !== -1; });
    if (!shown.length) {
      var li = document.createElement("li");
      li.className = "empty";
      li.textContent = "ls: nada encontrado.";
      list.appendChild(li);
      return;
    }
    shown.forEach(function (p) {
      var li = document.createElement("li");
      var art = document.createElement("article");
      art.className = "post-item";

      var id = document.createElement("span");
      id.className = "id";
      id.textContent = "[" + p.id + "]";

      var body = document.createElement("div");
      var h = document.createElement("h3");
      var a = document.createElement("a");
      a.href = "posts/" + p.slug + ".html";
      a.textContent = p.title;
      h.appendChild(a);

      var meta = document.createElement("p");
      meta.className = "meta";
      var time = document.createElement("time");
      time.dateTime = p.date;
      time.textContent = p.date;
      meta.appendChild(time);
      p.tags.forEach(function (tg) {
        var s = document.createElement("span");
        s.className = "tag";
        s.textContent = tg;
        meta.appendChild(document.createTextNode(" "));
        meta.appendChild(s);
      });

      var d = document.createElement("p");
      d.className = "desc";
      d.textContent = p.desc;

      body.appendChild(h);
      body.appendChild(meta);
      body.appendChild(d);
      art.appendChild(id);
      art.appendChild(body);
      li.appendChild(art);
      list.appendChild(li);
    });
  }

  function renderFilters() {
    if (!filters) return;
    var tags = [];
    posts.forEach(function (p) {
      p.tags.forEach(function (t) { if (tags.indexOf(t) === -1) tags.push(t); });
    });
    ["todos"].concat(tags).forEach(function (t, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = t;
      b.setAttribute("aria-pressed", i === 0 ? "true" : "false");
      b.addEventListener("click", function () {
        Array.prototype.forEach.call(filters.children, function (c) { c.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", "true");
        renderPosts(i === 0 ? null : t);
      });
      filters.appendChild(b);
    });
  }

  renderFilters();
  renderPosts(null);

  /* ---------- mini terminal ---------- */
  var out = $("#term-out");
  var form = $("#term-form");
  var input = $("#term-in");
  var term = $("#term");
  var history = [], hpos = 0;

  function print(text, cls) {
    var d = document.createElement("div");
    if (cls) d.className = cls;
    d.textContent = text;
    out.appendChild(d);
    term.scrollTop = term.scrollHeight;
  }

  function findPost(q) {
    q = (q || "").toLowerCase();
    return posts.filter(function (p) { return p.id === q || p.slug.indexOf(q) !== -1; })[0];
  }

  var commands = {
    help: function () {
      print([
        "comandos disponíveis:",
        "  help            esta lista",
        "  ls              listar posts",
        "  cat <id>        ver resumo de um post",
        "  open <id>       abrir um post",
        "  about           quem és tu, afinal?",
        "  whoami          mesmo assim",
        "  plague          memento mori",
        "  date            data atual",
        "  clear           limpar ecrã",
        "  sudo ...        boa sorte"
      ].join("\n"));
    },
    ls: function () {
      posts.forEach(function (p) { print(p.id + "  " + p.date + "  " + p.title); });
    },
    cat: function (a) {
      var p = findPost(a[0]);
      if (!a[0]) return print("uso: cat <id>", "dim");
      if (!p) return print("cat: " + a[0] + ": ficheiro não existe", "dim");
      print(p.title + "\n" + p.desc + "\ntags: " + p.tags.join(", "));
    },
    open: function (a) {
      var p = findPost(a[0]);
      if (!a[0]) return print("uso: open <id>", "dim");
      if (!p) return print("open: " + a[0] + ": não encontrado", "dim");
      print("a abrir " + p.slug + " ...");
      setTimeout(function () { window.location.href = "posts/" + p.slug + ".html"; }, 400);
    },
    about: function () { print("um caderno de projetos pessoais. html, css, js e teimosia."); },
    whoami: function () { print(vis ? vis.textContent : "anon"); },
    plague: function () {
      print("proc 0x1347: a corromper... memento mori.", "dim");
      var hero = $(".hero");
      if (hero) setTimeout(function () { hero.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth" }); }, 400);
    },
    date: function () { print(new Date().toString()); },
    clear: function () { out.textContent = ""; },
    sudo: function () { print("visitor não está no ficheiro sudoers. este incidente será reportado.", "dim"); },
    rm: function () { print("boa tentativa.", "dim"); },
    exit: function () { print("não há saída. só scroll.", "dim"); }
  };

  if (form && input && out) {
    print("beta_site_me tty1 — escreve 'help' para começar.", "dim");

    term.addEventListener("click", function () { input.focus(); });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var line = input.value.trim();
      input.value = "";
      if (!line) return;
      history.push(line);
      hpos = history.length;
      print("visitor@beta:~$ " + line);
      var parts = line.split(/\s+/);
      var cmd = parts.shift().toLowerCase();
      if (Object.prototype.hasOwnProperty.call(commands, cmd)) commands[cmd](parts);
      else print(cmd + ": comando não encontrado", "dim");
    });

    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowUp" && hpos > 0) {
        input.value = history[--hpos];
        e.preventDefault();
      } else if (e.key === "ArrowDown") {
        hpos = Math.min(hpos + 1, history.length);
        input.value = history[hpos] || "";
        e.preventDefault();
      }
    });
  }

  /* ---------- konami ---------- */
  var code = ["ArrowUp","ArrowUp","ArrowDown","ArrowDown","ArrowLeft","ArrowRight","ArrowLeft","ArrowRight","b","a"];
  var pos = 0;
  document.addEventListener("keydown", function (e) {
    var k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
    pos = k === code[pos] ? pos + 1 : (k === code[0] ? 1 : 0);
    if (pos === code.length) {
      pos = 0;
      document.body.classList.toggle("pwned");
    }
  });
})();
