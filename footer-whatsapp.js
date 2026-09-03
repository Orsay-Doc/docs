(() => {
  const selector =
    '#footer a[href="https://wa.me/33780905889"], #footer a[href="https://wa.me/33780905889/"]';

  function ensureWhatsAppLink() {
    const link = document.querySelector(selector);
    if (!link) return;

    link.setAttribute('aria-label', 'WhatsApp');
    link.setAttribute('title', 'WhatsApp');

    let icon = link.querySelector('img[data-orsay-whatsapp-icon]');
    if (!icon) {
      link.querySelectorAll('svg, img').forEach((element) => element.remove());
      icon = document.createElement('img');
      icon.dataset.orsayWhatsappIcon = '';
      icon.src = '/logo/whatsapp.svg';
      icon.alt = '';
      icon.setAttribute('aria-hidden', 'true');
      link.prepend(icon);
    }
  }

  let scheduled = false;
  function scheduleUpdate() {
    if (scheduled) return;
    scheduled = true;
    queueMicrotask(() => {
      scheduled = false;
      ensureWhatsAppLink();
    });
  }

  ensureWhatsAppLink();
  new MutationObserver(scheduleUpdate).observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
})();
