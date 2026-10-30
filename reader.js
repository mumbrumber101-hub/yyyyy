/* One inline reader, shared by the catalogue and resource links. */
(() => {
  'use strict';
  const main = document.querySelector('main');
  const sourceSelector = '#entries a[href], .resource-links a[href]';
  let active = null;

  function element(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text) el.textContent = text;
    return el;
  }

  function previewURL(href) {
    const url = new URL(href, document.baseURI);
    if (url.protocol !== 'https:') return null;
    // Drive's public preview keeps the same file ID and resource-key query.
    if (url.hostname === 'drive.google.com' && /^\/file\/d\/[\w-]+\/(?:view|edit)$/.test(url.pathname)) {
      url.pathname = url.pathname.replace(/\/(view|edit)$/, '/preview');
    }
    // A same-origin page would share this page's scripting authority.
    if (url.origin === location.origin) return null;
    return url.href;
  }

  function closeReader(restore = true) {
    if (!active) return;
    const {host, trigger, source, frame} = active;
    active = null;
    if (frame) frame.src = 'about:blank';
    host.remove();
    source.setAttribute('aria-expanded', 'false');
    source.removeAttribute('aria-controls');
    const button = source.parentElement.querySelector('.read-here');
    if (button) {
      button.setAttribute('aria-expanded', 'false');
      button.removeAttribute('aria-controls');
    }
    if (restore && trigger.isConnected) {
      trigger.focus({preventScroll: true});
    }
  }

  function openReader(source, trigger) {
    closeReader(false);
    const row = source.closest('#entries > tr');
    const title = row ? row.querySelector('a.title') : source;
    const panel = element('section', 'source-reader');
    panel.id = 'source-reader';
    panel.setAttribute('role', 'region');
    panel.setAttribute('aria-labelledby', 'reader-title');
    const header = element('div', 'reader-header');
    const heading = element('h3', 'reader-title');
    heading.id = 'reader-title';
    for (const child of title.childNodes) heading.appendChild(child.cloneNode(true));
    const actions = element('div', 'reader-actions');
    const original = element('a', 'button', 'Open original ↗');
    original.href = source.href;
    original.target = '_blank';
    original.rel = 'noopener noreferrer';
    original.setAttribute('aria-label', 'Open original in a new tab');
    const close = element('button', 'reader-close', 'Close reader');
    close.type = 'button';
    close.addEventListener('click', () => closeReader());
    actions.append(original, close);
    header.append(heading, actions);
    const note = element('p', 'reader-note', 'If the source is blank or unavailable here, use Open original.');
    note.id = 'reader-note';
    panel.append(header, note);
    const preview = previewURL(source.href);
    let frame = null;
    if (preview) {
      frame = element('iframe', 'reader-frame');
      frame.title = 'Read: ' + title.textContent.trim();
      frame.setAttribute('aria-describedby', 'reader-note');
      frame.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox allow-downloads');
      frame.referrerPolicy = 'strict-origin-when-cross-origin';
      frame.src = preview;
      panel.appendChild(frame);
    } else {
      note.textContent = 'This source needs to open in a new tab. Use Open original above.';
    }
    const bottom = element('div', 'reader-footer');
    const back = element('button', 'reader-close', 'Close and return to the list');
    back.type = 'button';
    back.addEventListener('click', () => closeReader());
    bottom.appendChild(back);
    panel.appendChild(bottom);
    let host;
    if (row) {
      host = element('tr', 'reading-row');
      const cell = document.createElement('td');
      cell.colSpan = 4;
      cell.appendChild(panel);
      host.appendChild(cell);
      row.after(host);
    } else {
      host = panel;
      source.closest('li').appendChild(host);
    }
    active = {host, trigger, source, frame};
    source.setAttribute('aria-expanded', 'true');
    source.setAttribute('aria-controls', panel.id);
    if (trigger !== source) {
      trigger.setAttribute('aria-expanded', 'true');
      trigger.setAttribute('aria-controls', panel.id);
    }
    // Wix embeds this document in a tall iframe. Scrolling an element into
    // view here also scrolls its ancestors and can move the reader off screen.
    // Keep focus on the activating link or button, as with an inline disclosure.
    // Even focus({preventScroll:true}) can move the containing Wix page.
    // Leave the viewport at the clicked entry as the panel expands beneath it.
  }

  main.addEventListener('click', event => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const source = event.target.closest(sourceSelector);
    if (!source || source.closest('.source-reader') || !/^https?:$/.test(new URL(source.href).protocol)) return;
    event.preventDefault();
    openReader(source, source);
  });

  for (const source of document.querySelectorAll('#entries a.title')) {
    const button = element('button', 'read-here', 'Read here');
    button.type = 'button';
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-label', 'Read here: ' + source.textContent.trim());
    button.addEventListener('click', () => openReader(source, button));
    source.after(button);
  }

  // Remove the extra reader row before the catalogue reorders its own rows.
  for (const id of ['query', 'category', 'priority', 'language', 'scope', 'sort']) {
    document.getElementById(id).addEventListener(id === 'query' ? 'input' : 'change', () => closeReader(false), true);
  }
  for (const id of ['reset', 'mainList', 'postsList']) {
    document.getElementById(id).addEventListener('click', () => closeReader(false), true);
  }
  document.getElementById('bibliography').addEventListener('toggle', event => {
    if (!event.target.open && active?.source.closest('#entries')) closeReader(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && active) {
      event.preventDefault();
      closeReader();
    }
  });
  document.querySelector('.reader-help').hidden = false;
})();
