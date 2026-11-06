/* A própria arte ASCII é amostrada: cada ponto guarda sua posição de origem. */
(function () {
  'use strict';
  var canvas = document.getElementById('character-particles');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  if (!ctx) return;
  var hero = document.getElementById('home');
  var art = hero.querySelector('.hero-art');
  var image = art.querySelector('img');
  var toggle = document.getElementById('particle-toggle');
  var motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var pointer = { x: -1000, y: -1000 };
  var particles = [];
  var width = 0;
  var height = 0;
  var frame = 0;
  var lastTime = 0;
  var paused = false;
  var ready = false;
  var needsReset = true;

  function running() {
    return ready && !paused && !motion.matches && !document.hidden;
  }
  function draw(time) {
    frame = 0;
    if (!ready) return;
    // Limite de 30 fps, independente da taxa de atualização do monitor.
    if (running() && time - lastTime < 32) { frame = requestAnimationFrame(draw); return; }
    var dt = Math.min((time - lastTime) / 33.33, 2) || 1;
    lastTime = time;
    ctx.clearRect(0, 0, width, height);
    var animate = running();
    var radius = Math.min(150, width * .2);
    for (var i = 0; i < particles.length; i++) {
      var p = particles[i];
      if (!animate || needsReset) { p.x = p.homeX; p.y = p.homeY; p.vx = p.vy = 0; }
      else {
        var dx = p.x - pointer.x;
        var dy = p.y - pointer.y;
        var distance = Math.sqrt(dx * dx + dy * dy);
        if (distance < radius) {
          var force = (1 - distance / radius) * 3;
          p.vx += dx / (distance || 1) * force * dt;
          p.vy += dy / (distance || 1) * force * dt;
        }
        p.vx = (p.vx + (p.homeX - p.x) * .035 * dt) * Math.pow(.82, dt);
        p.vy = (p.vy + (p.homeY - p.y) * .035 * dt) * Math.pow(.82, dt);
        p.x += p.vx * dt;
        p.y += p.vy * dt;
      }
      ctx.fillStyle = p.color;
      ctx.fillRect(p.x, p.y, p.size, p.size);
    }
    needsReset = false;
    if (animate) frame = requestAnimationFrame(draw);
  }
  function sync() {
    cancelAnimationFrame(frame);
    frame = 0;
    lastTime = 0;
    toggle.setAttribute('aria-pressed', String(paused));
    toggle.innerHTML = paused ? 'Resume effect <span aria-hidden="true">▷</span>' : 'Pause effect <span aria-hidden="true">Ⅱ</span>';
    toggle.hidden = !ready || motion.matches;
    if (!running()) needsReset = true;
    draw(performance.now());
  }
  function resize() {
    if (!image.naturalWidth) return;
    width = hero.clientWidth;
    height = hero.clientHeight;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    var sample = document.createElement('canvas');
    sample.width = width;
    sample.height = height;
    var sampleCtx = sample.getContext('2d', { willReadFrequently: true });
    if (!sampleCtx) return;
    // Repete o object-fit: contain e o object-position da imagem original.
    // Assim, ativar ou pausar o canvas não muda a posição do personagem.
    var imageWidth = Math.min(width, height * .9);
    var imageHeight = imageWidth / .9;
    var imageX = (width - imageWidth) * (width <= 600 ? .5 : .8);
    sampleCtx.drawImage(image, imageX, (height - imageHeight) / 2, imageWidth, imageHeight);
    try {
      var pixels = sampleCtx.getImageData(0, 0, width, height).data;
      particles = [];
      var step = Math.max(width < 600 ? 3 : 3.5, Math.sqrt(width * height / 150000));
      for (var y = 0; y < height; y += step) {
        for (var x = 0; x < width; x += step) {
          var offset = (Math.floor(y) * width + Math.floor(x)) * 4;
          var light = pixels[offset] * pixels[offset + 3] / 255;
          if (light < 22) continue;
          particles.push({ homeX: x, homeY: y, x: x, y: y, vx: 0, vy: 0,
            size: light > 150 ? 1.6 : 1.15,
            color: 'rgba(224,230,230,' + (.18 + light / 255 * .72).toFixed(2) + ')' });
        }
      }
      ready = particles.length > 0;
      art.classList.toggle('is-ready', ready);
      needsReset = true;
      sync();
    } catch (_) {
      // A arte original permanece visível se a amostragem não estiver disponível.
      ready = false;
      art.classList.remove('is-ready');
      toggle.hidden = true;
    }
  }
  hero.addEventListener('pointermove', function (event) {
    if (!running()) return;
    var rect = hero.getBoundingClientRect();
    pointer.x = event.clientX - rect.left;
    pointer.y = event.clientY - rect.top;
  }, { passive: true });
  function releasePointer() { pointer.x = pointer.y = -1000; }
  hero.addEventListener('pointerleave', releasePointer);
  hero.addEventListener('pointerup', function (event) { if (event.pointerType !== 'mouse') releasePointer(); });
  hero.addEventListener('pointercancel', releasePointer);
  toggle.addEventListener('click', function () { paused = !paused; sync(); });
  motion.addEventListener('change', sync);
  document.addEventListener('visibilitychange', sync);
  new ResizeObserver(resize).observe(hero);
  if (image.complete && image.naturalWidth) resize();
  else image.addEventListener('load', resize, { once: true });
})();
