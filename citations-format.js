/* Pure citation/export functions, also used by the regression checks. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.CitationFormat = api;
})(typeof window === 'undefined' ? this : window, function () {
  'use strict';
  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  function accessDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return '';
    const [year, month, day] = value.split('-').map(Number);
    const parsed = new Date(Date.UTC(year, month - 1, day));
    if (parsed.getUTCFullYear() !== year || parsed.getUTCMonth() !== month - 1 || parsed.getUTCDate() !== day) return '';
    return months[month - 1] + ' ' + day + ', ' + year;
  }
  function render(record, accessed) {
    const date = accessDate(accessed || '');
    const access = date ? ' Accessed ' + date + '.' : '';
    return {
      html: record.html + access + ' ' + record.url.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') + '.',
      plain: record.plain + access + ' ' + record.url + '.',
      ready: !record.needsAccessDate || !!date
    };
  }
  function decode(s) {
    const named = {amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",nbsp:' '};
    return s.replace(/&(#x[\da-f]+|#\d+|amp|lt|gt|quot|apos|nbsp);/gi, (_, code) => {
      if (code[0] === '#') return String.fromCodePoint(parseInt(code.slice(code[1].toLowerCase() === 'x' ? 2 : 1), code[1].toLowerCase() === 'x' ? 16 : 10));
      return named[code.toLowerCase()];
    });
  }
  function rtf(html) {
    const parts = html.split(/(<\/?em>)/g);
    let out = '{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Times New Roman;}}\\uc1\\pard\\li720\\fi-720\\sa160\\f0\\fs24 ';
    for (const part of parts) {
      if (part === '<em>') {out += '{\\i '; continue;}
      if (part === '</em>') {out += '}'; continue;}
      const decoded = decode(part);
      for (let i = 0; i < decoded.length; i++) {
        const c = decoded[i], n = decoded.charCodeAt(i);
        if ('\\{}'.includes(c)) out += '\\' + c;
        else if (c === '\n') out += '\\line ';
        else if (n > 127) out += '\\u' + (n > 32767 ? n - 65536 : n) + '?';
        else out += c;
      }
    }
    return out + '\\par}';
  }
  return {accessDate, render, rtf};
});
