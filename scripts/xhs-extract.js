/* Search-card extraction adapted from nashsu/AutoCLI v0.3.8
 * adapters/xiaohongshu/search.yaml, itself derived from jackwener/OpenCLI.
 * Apache-2.0; see ../vendor/licenses/AutoCLI-Apache-2.0.txt and NOTICE.
 * Modified 2026-09-16: no CLI/daemon/extension; require prior UI sort evidence;
 * preserve unknown counts, normalize counts, deduplicate and strip public tokens.
 */
function tripMasterXhsExtract(options = {}) {
  const clean = v => String(v ?? '').replace(/\s+/g, ' ').trim();
  const parseLikes = raw => {
    const s = clean(raw).replace(/,/g, '');
    const m = s.match(/^(\d+(?:\.\d+)?)\s*([kKwW万千]?)\s*(\+)?$/);
    if (!m) return {value: null, approximate: false};
    const unit = m[2].toLowerCase();
    const value = Math.round(Number(m[1]) * ({k:1000, w:10000, '万':10000, '千':1000}[unit] || 1));
    return {value, approximate: Boolean(m[2] || m[3])};
  };
  const query = clean(options.query);
  const proof = options.sortEvidence;
  if (!query || !proof || proof.label !== '最多点赞' || proof.query !== query ||
      proof.selected !== true || proof.resultsSettled !== true ||
      !['screenshot', 'accessibility', 'dom'].includes(proof.kind) ||
      !Number.isFinite(Date.parse(proof.observedAt)) ||
      Math.abs(Date.now() - Date.parse(proof.observedAt)) > 300000) {
    throw new Error('SORT_NOT_VERIFIED: select site 最多点赞, confirm selected state and refreshed results first');
  }
  if (typeof document === 'undefined') throw new Error('BROWSER_REQUIRED');
  if (location.hostname !== 'www.xiaohongshu.com' || !location.pathname.startsWith('/search_result')) throw new Error('WRONG_PAGE');
  if (clean(new URL(location.href).searchParams.get('keyword')) !== query) throw new Error('QUERY_CHANGED');
  if (/登录后查看搜索结果/.test(document.body.innerText)) throw new Error('LOGIN_REQUIRED');
  const notes = [], seen = new Set();
  for (const el of document.querySelectorAll('section.note-item')) {
    if (el.classList.contains('query-note-item')) continue;
    const a = el.querySelector('a.cover.mask') || el.querySelector('a[href*="/search_result/"]') || el.querySelector('a[href*="/explore/"]') || el.querySelector('a[href*="/note/"]');
    const href = a?.getAttribute('href');
    if (!href) continue;
    let url; try { url = new URL(href, location.origin); } catch { continue; }
    if (url.hostname !== 'www.xiaohongshu.com') continue;
    const id = url.pathname.match(/\/(?:search_result|explore|note)\/([a-f0-9]{24})/)?.[1];
    if (!id || seen.has(id)) continue;
    seen.add(id);
    const title = clean(el.querySelector('.title, .note-title, a.title, .footer .title span')?.textContent);
    const authorDate = clean(el.querySelector('a.author')?.textContent || el.querySelector('.author-name, .nick-name, .name')?.textContent);
    const likesRaw = clean(el.querySelector('.like-wrapper .count, .like-count, .count')?.textContent);
    const likes = parseLikes(likesRaw);
    notes.push({id, rank:notes.length+1, title, author_date_raw:authorDate, likes_raw:likesRaw || null,
      likes:likes.value, likes_approximate:likes.approximate,
      url:url.origin+url.pathname, detail_url_private:url.href});
    if (notes.length >= Math.min(50,Math.max(1,Number(options.limit)||20))) break;
  }
  return {query, sort:'最多点赞', sort_evidence:proof, retrieved_at:new Date().toISOString(),
    scope:'站内最多点赞筛选后的已加载结果；非全站榜单；未读正文',
    status:notes.length?'ok':(/没有筛选到相关内容/.test(document.body.innerText)?'empty':'not_ready'), notes};
}
if (typeof module !== 'undefined') module.exports = {tripMasterXhsExtract};
