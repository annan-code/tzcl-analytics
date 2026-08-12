/* TransitionZero Claude Analytics — monthly harvester
 *
 * HOW TO USE
 * ----------
 * 1. Log in to claude.ai as an org admin.
 * 2. Open https://claude.ai/analytics/overview and let it fully load (scroll to the bottom).
 * 3. Paste this whole file into the browser console and press Enter.
 * 4. It returns a JSON object. Copy it and hand it to Claude to rebuild data.json.
 *
 * Everything here is FETCHED. Nothing is typed in by hand.
 * Spend figures come from the internal JSON API; the rest is read off the rendered page.
 */
(async () => {
  const ORG = '1ff088d0-8eb1-42a3-95d3-ea2ca315a26e'; // TransitionZero
  const B = 'https://claude.ai/api/organizations/' + ORG + '/analytics/';
  const g = async (u) => {
    try {
      const r = await fetch(u, { headers: { accept: 'application/json' } });
      return r.status === 200 ? await r.json() : null;
    } catch (e) { return null; }
  };

  const monthStart = new Date();
  monthStart.setUTCDate(1);
  const MS = monthStart.toISOString().slice(0, 10);
  const today = new Date().toISOString().slice(0, 10);
  const from30 = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);

  const H = { fetchedAt: new Date().toISOString(), org: 'TransitionZero', windowStart: from30, windowEnd: today };

  /* ---------- SPEND (JSON API) ---------- */
  const conc = await g(B + 'spend/concentration?period=mtd');
  const proj = await g(B + 'spend/projection');
  H.spend = {
    concentration: conc && {
      gini: conc.gini, top10Share: conc.top10_pct_share,
      users: conc.total_users, asOf: conc.as_of
    },
    mtdActual: proj && proj.list && proj.list.mtd_actual_usd,
    projectedEom: proj && proj.list && proj.list.projected_eom_l7_usd,
    dailyActuals: proj && proj.list && proj.list.mtd_daily_actuals,
    byModel: await g(B + 'spend/by-model?start_date=' + MS),
    limitRisk: await g(B + 'spend/limit-risk'),
    byProduct: {}
  };
  for (const p of ['claude_code', 'cowork', 'claude-ai', 'office', 'teammate']) {
    const t = await g(B + 'spend/timeseries?start_date=' + MS + '&end_date=' + today + '&product_filter=' + p);
    if (t) H.spend.byProduct[p] = t;
  }

  /* ---------- COWORK FILE CATEGORIES (JSON API) ---------- */
  H.fileCategories = await g(B + 'cowork/file-categories?start_date=' + from30 + '&end_date=' + today);

  /* ---------- RENDERED PAGE ---------- */
  const T = document.body.innerText;
  const num = (s) => Number(String(s).replace(/[^0-9.\-]/g, ''));
  const one = (re) => { const m = T.match(re); return m ? num(m[1]) : null; };

  H.headline = {
    weeklyActive: one(/\n(\d+)\s*\n\s*[\d.]+% WoW/),
    seats: one(/out of (\d+) seats/),
    prsCreated: one(/(\d+)\s*\nPRs created/),
    coworkSessions: one(/\n(\d[\d,]*)\s*\n[\d.]+%\s*\n\s*\nSessions in Cowork/),
    fileOperations: one(/(\d[\d,]*)\s*\nFile operations/),
    conversations: one(/(\d[\d,]*)\s*\nConversations/),
    mcpWrites: one(/(\d[\d,]*)\s*\nMCP writes/),
    designsCreated: one(/(\d+)\s*\nDesigns created/),
    actionsPerPrompt: Number((T.match(/Actions per prompt · org average\s*\n([\d.]+)/) || [])[1]) || null,
    timeSavedHours: one(/~([\d,]+) hours/),
    usersWithLimits: one(/(\d+) users with limits/),
    usersWithoutLimits: one(/\d+ users with limits · (\d+) without/)
  };

  // Skills: "docx $0.08 42"
  H.skills = [...T.matchAll(/^([a-z0-9][a-z0-9\-_]{1,40})\s+\$([0-9.]+)\s+(\d[\d,]*)$/gmi)]
    .map((m) => ({ skill: m[1], costPerUse: Number(m[2]), uses: num(m[3]) }));

  // Connectors: "Notion 8 698 149" — reject the spend-decile axis labels (Top 10 20 30...)
  H.connectors = [...T.matchAll(/^([A-Z][A-Za-z0-9 .]{1,30})\s+(\d+)\s+(\d[\d,]*)\s+(\d[\d,]*)$/gm)]
    .map((m) => ({ connector: m[1].trim(), users: num(m[2]), reads: num(m[3]), writes: num(m[4]) }))
    .filter((c) => c.connector !== 'Top');

  // Member spend, one row per line: "someone@example.org $12.34"
  H.memberSpend = [...T.matchAll(/^(\S+@\S+\.\w+)\s+\$([0-9,.]+)$/gm)]
    .map((m) => ({ email: m[1], spend: num(m[2]) }));

  // Product stickiness, in rendered order
  const stickNames = ['Claude Code', 'Cowork', 'Claude.ai', 'Office Agents'];
  H.stickiness = [...T.matchAll(/(\d+)%\s*\nDAU\/MAU/g)]
    .map((m, i) => ({ product: stickNames[i] || ('product' + i), dauMau: num(m[1]) / 100 }));

  // Spend by product table: "Claude Code\n$101.00 $398.00"
  H.spendByProductTable = [...T.matchAll(/^(Claude Code|Cowork|Claude\.ai|Other)\s*\n\$([\d,.]+)\s+\$([\d,.]+)$/gm)]
    .map((m) => ({ product: m[1], periodToDate: num(m[2]), projectedEom: num(m[3]) }));

  console.log('skills=%d connectors=%d members=%d stickiness=%d',
    H.skills.length, H.connectors.length, H.memberSpend.length, H.stickiness.length);
  window.__TZ_HARVEST = H;
  return H;
})();
