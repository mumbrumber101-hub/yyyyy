(() => {
  'use strict';
  const records = window.CATALOGUE_CITATIONS;
  const format = window.CitationFormat;
  if (!records || !format) return;
  let active = null;
  const make = (tag, cls, value) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value) node.textContent = value;
    return node;
  };
  function close(restore = true) {
    if (!active) return;
    const {host, trigger} = active;
    active = null;
    host.remove();
    trigger.setAttribute('aria-expanded', 'false');
    trigger.removeAttribute('aria-controls');
    if (restore) trigger.focus({preventScroll:true});
  }
  function save(body, name, type) {
    const url = URL.createObjectURL(new Blob([body], {type}));
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
  function open(id, trigger, row) {
    if (active?.trigger === trigger) {close(); return;}
    close(false);
    const record = records[id];
    const panel = make('section', 'citation-panel');
    panel.id = 'citation-panel';
    panel.setAttribute('aria-labelledby', 'citation-heading');
    const header = make('div', 'citation-header');
    const heading = make('h3', '', 'Chicago citation');
    heading.id = 'citation-heading';
    const done = make('button', 'citation-close', 'Close citation');
    done.type = 'button';
    done.addEventListener('click', () => close());
    header.append(heading, done);
    panel.append(header, make('p', 'citation-kind', 'Bibliography · Chicago Manual of Style, 18th edition'));
    const output = make('p', 'citation-text');
    output.tabIndex = 0;
    const dateLine = make('div', 'citation-date');
    const label = make('label', '', record.needsAccessDate ? 'Date you accessed this undated source' : 'Access date (optional)');
    label.htmlFor = 'citation-access-date';
    const dateInput = make('input');
    dateInput.type = 'date';
    dateInput.id = label.htmlFor;
    dateLine.append(label, dateInput);
    panel.append(output, dateLine);
    if (record.notes.length) {
      const details = make('details', 'citation-notes');
      details.appendChild(make('summary', '', 'Publication details to check'));
      const list = make('ul');
      for (const note of record.notes) list.appendChild(make('li', '', note));
      details.appendChild(list);
      panel.appendChild(details);
    }
    const actions = make('div', 'citation-actions');
    const copy = make('button', '', 'Copy citation');
    const word = make('button', '', 'Download for Word (.rtf)');
    const plain = make('button', '', 'Download text (.txt)');
    for (const b of [copy, word, plain]) b.type = 'button';
    const status = make('p', 'citation-status');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    actions.append(copy, word, plain);
    panel.append(actions, status);
    let rendered;
    function refresh() {
      rendered = format.render(record, dateInput.value);
      output.innerHTML = rendered.html;
      for (const b of [copy, word, plain]) b.disabled = !rendered.ready;
      status.textContent = rendered.ready ? '' : 'Enter the date you accessed the source to complete this citation.';
    }
    dateInput.addEventListener('input', refresh);
    refresh();
    copy.addEventListener('click', async () => {
      let copied = false;
      try {
        if (navigator.clipboard?.write && typeof ClipboardItem !== 'undefined') {
          await navigator.clipboard.write([new ClipboardItem({
            'text/html': new Blob(['<p>' + rendered.html + '</p>'], {type:'text/html'}),
            'text/plain': new Blob([rendered.plain], {type:'text/plain'})
          })]);
          copied = true;
        }
      } catch (_) { /* The containing site may restrict clipboard permissions. */ }
      if (!copied) {
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(output);
        selection.removeAllRanges();
        selection.addRange(range);
        try {copied = document.execCommand('copy');} catch (_) { /* Keep text selected. */ }
      }
      status.textContent = copied ? 'Citation copied. Italics are retained when pasted into a rich-text editor.' : 'The citation is selected. Use your browser’s Copy command, or download it below.';
    });
    word.addEventListener('click', () => save(format.rtf(rendered.html), id + '-Chicago-citation.rtf', 'application/rtf'));
    plain.addEventListener('click', () => save(rendered.plain + '\n', id + '-Chicago-citation.txt', 'text/plain;charset=utf-8'));
    const host = make('tr', 'citation-row');
    const cell = make('td');
    cell.colSpan = 4;
    cell.appendChild(panel);
    host.appendChild(cell);
    row.after(host);
    active = {host, trigger};
    trigger.setAttribute('aria-expanded', 'true');
    trigger.setAttribute('aria-controls', panel.id);
    done.focus({preventScroll:true});
  }
  for (const row of document.querySelectorAll('#entries tr[data-id]')) {
    const id = row.dataset.id;
    if (!records[id]) continue;
    const title = row.querySelector('a.title');
    const actions = make('div', 'entry-actions');
    const reader = row.querySelector('.read-here');
    if (reader) actions.appendChild(reader);
    const cite = make('button', 'cite-entry', 'Cite');
    cite.type = 'button';
    cite.setAttribute('aria-label', 'Cite: ' + title.textContent.trim());
    cite.setAttribute('aria-expanded', 'false');
    cite.addEventListener('click', () => open(id, cite, row));
    actions.appendChild(cite);
    title.after(actions);
  }
  for (const id of ['query','category','priority','language','scope','sort']) {
    document.getElementById(id).addEventListener(id === 'query' ? 'input' : 'change', () => close(false), true);
  }
  for (const id of ['reset','mainList','postsList']) document.getElementById(id).addEventListener('click', () => close(false), true);
  document.getElementById('bibliography').addEventListener('toggle', event => {if (!event.target.open) close(false);});
  document.addEventListener('keydown', event => {if (event.key === 'Escape' && active) {event.preventDefault(); close();}});
})();
