// PA Microphone page: record the voice, send it to the add-on, show what happens.
//
// Tap the big button to talk, tap again to send (or Cancel). The add-on answers
// at once with a message id and plays the messages in order; this page asks
// /status until its message has played. The add-on makes the voice loud
// (play_msg.sh), so the page sends the recording as it is.
(function () {
  "use strict";

  var MAX_SEC = 60;            // recording stops and is sent after this
  var MIN_SEC = 0.7;           // shorter than this is a mis-tap: not sent
  var POLL_MS = 600;

  var $ = function (id) { return document.getElementById(id); };
  var talk = $("talk"), label = $("talk-label"), halo = $("halo"),
      timeEl = $("time"), statusEl = $("status"),
      cancelBtn = $("cancel"), retryBtn = $("retry"), repeatBtn = $("repeat");

  var ctx = null;              // one AudioContext for the page (iOS allows only a few)
  var stream = null, source = null, analyser = null, rec = null;
  var recState = "idle";       // idle | starting | recording | sending
  var t0 = 0, tickTimer = null, meterFrame = 0;
  var failedBlob = null;       // a recording that could not be sent, for "Send again"
  var waitId = 0, pollTimer = null, pollUntil = 0;

  // ---------- small helpers

  function setRec(s) {
    recState = s;
    document.body.setAttribute("data-rec", s);
    label.textContent = s === "recording" ? "Send" : s === "sending" ? "Sending" : "Talk";
    talk.setAttribute("aria-label", s === "recording" ? "Send the message" : "Record a message");
    cancelBtn.hidden = s !== "recording";
    if (s === "recording") retryBtn.hidden = true;
  }

  function setStatus(text, kind) {
    statusEl.textContent = text;
    statusEl.className = "status" + (kind ? " " + kind : "");
  }

  function fmtTime(sec) {
    sec = Math.max(0, Math.floor(sec));
    return Math.floor(sec / 60) + ":" + ("0" + (sec % 60)).slice(-2);
  }

  function micError(e) {
    var n = e && e.name;
    if (n === "NotAllowedError" || n === "SecurityError")
      return "Microphone blocked: allow it for this page in the browser settings";
    if (n === "NotFoundError" || n === "OverconstrainedError") return "No microphone found";
    if (n === "NotReadableError") return "The microphone is busy in another app";
    return "Could not start the microphone";
  }

  // ---------- recording

  function startRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus(window.isSecureContext ? "This browser cannot record"
                                       : "Open the page with https:// to use the microphone", "err");
      return;
    }
    setRec("starting");
    setStatus("Starting the microphone…");

    // create / wake the audio context inside the tap (iOS needs that)
    try {
      if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
      if (ctx.state === "suspended") ctx.resume();
    } catch (e) {
      setRec("idle");
      setStatus("This browser cannot record", "err");
      return;
    }

    navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: true, autoGainControl: true, channelCount: 1 },
      video: false
    }).then(function (s) {
      if (recState !== "starting") {                 // cancelled while asking
        s.getTracks().forEach(function (t) { t.stop(); });
        return;
      }
      stream = s;
      source = ctx.createMediaStreamSource(s);
      analyser = ctx.createAnalyser();
      analyser.fftSize = 1024;
      source.connect(analyser);
      rec = new Recorder(source, { numChannels: 1 });
      rec.record();

      $("format").textContent = "mono · " + Math.round(ctx.sampleRate / 100) / 10 + " kHz";
      t0 = Date.now();
      setRec("recording");
      setStatus("Recording… tap again to send", "rec");
      timeEl.textContent = "0:00";
      timeEl.classList.remove("ending");
      tickTimer = setInterval(tick, 200);
      meter();
    }).catch(function (e) {
      setRec("idle");
      setStatus(micError(e), "err");
    });
  }

  function tick() {
    var sec = (Date.now() - t0) / 1000;
    timeEl.textContent = fmtTime(sec);
    timeEl.classList.toggle("ending", MAX_SEC - sec <= 10);
    if (sec >= MAX_SEC) finishRecording();
  }

  // mic level -> the red halo around the button
  function meter() {
    if (!analyser) return;
    var buf = new Uint8Array(analyser.fftSize);
    analyser.getByteTimeDomainData(buf);
    var sum = 0;
    for (var i = 0; i < buf.length; i++) { var v = (buf[i] - 128) / 128; sum += v * v; }
    var db = 20 * Math.log10(Math.sqrt(sum / buf.length) + 1e-6);
    var lvl = Math.min(1, Math.max(0, (db + 50) / 40));   // -50 dB .. -10 dB -> 0..1
    halo.style.setProperty("--lvl", lvl.toFixed(2));
    meterFrame = requestAnimationFrame(meter);
  }

  // stops the microphone; the recorded audio stays in rec until exported
  function stopCapture() {
    if (tickTimer) { clearInterval(tickTimer); tickTimer = null; }
    if (meterFrame) { cancelAnimationFrame(meterFrame); meterFrame = 0; }
    halo.style.setProperty("--lvl", "0");
    timeEl.classList.remove("ending");
    if (rec) {
      rec.stop();
      try { rec.node.disconnect(); } catch (e) {}
    }
    if (source) { try { source.disconnect(); } catch (e) {} source = null; }
    analyser = null;
    if (stream) { stream.getTracks().forEach(function (t) { t.stop(); }); stream = null; }
  }

  function dropRecorder() {
    if (rec && rec.worker && rec.worker.terminate) rec.worker.terminate();
    rec = null;
  }

  function finishRecording() {
    if (recState !== "recording") return;
    var sec = (Date.now() - t0) / 1000;
    stopCapture();
    if (sec < MIN_SEC) {
      dropRecorder();
      setRec("idle");
      timeEl.textContent = "0:00";
      setStatus("Too short: tap, speak, then tap again", "err");
      return;
    }
    setRec("sending");
    setStatus("Sending…");
    var r = rec;
    r.exportWAV(function (blob) {
      dropRecorder();
      send(blob);
    });
  }

  function cancelRecording() {
    if (recState === "starting") { setRec("idle"); setStatus("Cancelled"); return; }
    if (recState !== "recording") return;
    stopCapture();
    dropRecorder();
    setRec("idle");
    timeEl.textContent = "0:00";
    setStatus("Cancelled: nothing was sent");
  }

  // ---------- talking to the add-on

  function postTo(url, body) {
    return fetch(url, { method: "POST", body: body, cache: "no-store" })
      .then(function (r) {
        return r.json().catch(function () { return { ok: false }; })
          .then(function (j) {
            if (!r.ok || !j.ok) throw new Error(j.error || ("HTTP " + r.status));
            return j;
          });
      });
  }

  function send(blob) {
    setRec("sending");
    setStatus("Sending…");
    var fd = new FormData();
    fd.append("audio_data", blob, new Date().toISOString() + ".wav");
    postTo("/", fd).then(function (j) {
      failedBlob = null;
      retryBtn.hidden = true;
      setRec("idle");
      waitFor(j.id);
    }).catch(function (e) {
      failedBlob = blob;
      setRec("idle");
      retryBtn.hidden = false;
      setStatus("Could not send: " + (e.message || "no connection"), "err");
    });
  }

  function repeatLast() {
    repeatBtn.disabled = true;
    setStatus("Repeating the last message…");
    postTo("/repeat", "").then(function (j) {
      waitFor(j.id);
    }).catch(function (e) {
      setStatus("Could not repeat: " + (e.message || "no connection"), "err");
      refreshStatus();
    });
  }

  // follow message id until the add-on has played it
  function waitFor(id) {
    waitId = id;
    pollUntil = Date.now() + 5 * 60 * 1000;
    setStatus("Playing in the house…", "play");
    if (pollTimer) clearTimeout(pollTimer);
    pollTimer = setTimeout(poll, POLL_MS);
  }

  function poll() {
    pollTimer = null;
    getStatus().then(function (s) {
      if (!waitId) return;
      if (s.done >= waitId) {
        waitId = 0;
        if (recState === "idle") {
          if (s.error) setStatus(s.error, "err");
          else setStatus("Played ✓", "ok");
        }
        return;
      }
      if (recState === "idle") {
        if (s.done < waitId - 1) setStatus("Waiting for the message before it…", "play");
        else setStatus("Playing in the house…", "play");
      }
      if (Date.now() < pollUntil) pollTimer = setTimeout(poll, POLL_MS);
    }).catch(function () {
      if (Date.now() < pollUntil) pollTimer = setTimeout(poll, POLL_MS * 3);
    });
  }

  function getStatus() {
    return fetch("/status", { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error(); return r.json(); })
      .then(function (s) { repeatBtn.disabled = !s.has_last; return s; });
  }

  function refreshStatus() { getStatus().catch(function () {}); }

  // ---------- buttons

  talk.addEventListener("click", function () {
    if (recState === "idle") startRecording();
    else if (recState === "recording") finishRecording();
  });
  cancelBtn.addEventListener("click", cancelRecording);
  retryBtn.addEventListener("click", function () { if (failedBlob && recState === "idle") send(failedBlob); });
  repeatBtn.addEventListener("click", function () { if (recState === "idle") repeatLast(); });

  // space bar = the big button, Esc = cancel (on a computer)
  document.addEventListener("keydown", function (e) {
    if (e.repeat) return;
    if (e.code === "Space" && document.activeElement !== talk) { e.preventDefault(); talk.click(); }
    else if (e.key === "Escape") cancelRecording();
  });

  $("version").textContent = window.WM_VERSION ? "v" + window.WM_VERSION : "";
  refreshStatus();
})();
