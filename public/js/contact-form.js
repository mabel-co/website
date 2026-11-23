// Contact form enhancement (Issue #2525, W6).
//
// The no-JS baseline is the plain form POST: action="/api/contact" on our own
// origin, which the brevo-form-handler answers with a 303 redirect back to
// this page carrying #form-status=<ok|duplicate|error>. The visitor's browser
// never posts to a third-party API — the Brevo key lives only in the handler.
//
// This script is progressive enhancement: it hides the no-JS notice, submits
// the same endpoint via fetch so the visitor stays on the page with inline
// status, and shows a GitHub pointer if the endpoint is unreachable (e.g. the
// handler route is not yet wired in front of the static site). It never
// carries an API key.
(function () {
  'use strict';

  var formEl = document.getElementById('contact-form');
  var submitEl = document.getElementById('contact-submit');
  var statusEl = document.getElementById('contact-status');
  var noJsEl = document.getElementById('contact-nojs');
  if (!formEl || !statusEl) return;

  if (noJsEl) noJsEl.hidden = true;

  // The JS path renders status into #contact-status; hide the static no-JS
  // :target result blocks (#2936) so a JS visitor never sees the same outcome
  // twice. `hidden` wins over `:target` via the Tailwind preflight's
  // [hidden]{display:none!important}. The JS-disabled baseline keeps them —
  // they are its only renderer.
  var staticResults = document.querySelectorAll('.form-result');
  for (var i = 0; i < staticResults.length; i++) {
    staticResults[i].hidden = true;
  }

  // Surface the outcome of a no-JS round-trip (303 back to us with
  // #form-status=...). Runs on load; the fragment is left in place so a
  // reload of the same URL re-shows the same message — harmless.
  var statusMatch = /(?:^|[#&])form-status=([a-z]+)/i.exec(window.location.hash || '');
  if (statusMatch) {
    showStatus(statusMatch[1].toLowerCase());
  }

  formEl.addEventListener('submit', function (e) {
    e.preventDefault();

    var emailEl = document.getElementById('contact-email');
    var nameEl = document.getElementById('contact-name');
    var messageEl = document.getElementById('contact-message');
    var email = (emailEl && emailEl.value) ? emailEl.value.trim() : '';
    if (!email) {
      setStatus('Please enter your email address.', 'error');
      return;
    }

    setStatus('', 'clear');
    if (submitEl) {
      submitEl.disabled = true;
      submitEl.textContent = 'Sending...';
    }

    // Submit the form exactly as the browser would without JS (urlencoded to
    // the same action) so there is one server path to wire and test. The
    // handler answers with a 303 back to this page; fetch follows it and the
    // outcome rides in response.url's #form-status= fragment.
    fetch(formEl.getAttribute('action') || '/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(new FormData(formEl)).toString(),
      redirect: 'follow'
    }).then(function (response) {
      if (response.status === 404) {
        // Handler route not wired yet (static Pages has no server): show the
        // GitHub pointer until a form handler lands.
        offlineFallback();
        return;
      }
      var match = /(?:^|[#&])form-status=([a-z]+)/i.exec(response.url || '');
      showStatus(response.ok && match ? match[1].toLowerCase() : 'error');
    }).catch(function () {
      offlineFallback();
    }).finally(function () {
      if (submitEl) {
        submitEl.disabled = false;
        submitEl.textContent = 'Send';
      }
    });
  });

  function offlineFallback() {
    // The mailto: fallback was dropped when the custom domain was retired
    // (dead address). Direct visitors to the public organisation page.
    setStatus('Something went wrong. If this keeps happening, reach us on GitHub: https://github.com/mabel-co', 'error');
  }

  function showStatus(outcome) {
    if (outcome === 'ok') {
      setStatus('Thanks! Please check your email to confirm your subscription.', 'accent');
      formEl.reset();
    } else if (outcome === 'duplicate') {
      setStatus('You are already subscribed — thanks!', 'accent');
    } else {
      setStatus('Something went wrong. Please try again or reach us on GitHub: https://github.com/mabel-co.', 'error');
    }
  }

  function setStatus(text, kind) {
    statusEl.classList.remove('hidden');
    statusEl.textContent = text;
    if (kind === 'clear') {
      statusEl.className = 'text-sm';
    } else if (kind === 'error') {
      statusEl.className = 'text-sm text-red-600';
    } else {
      statusEl.className = 'text-sm text-brand-accent';
    }
  }
})();
