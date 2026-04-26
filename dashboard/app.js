const SCORE_LABELS = {
  qa_relevance: "QA relevance",
  company_size: "Company size",
  urgency: "Urgency",
  nearshore_fit: "Nearshore fit",
  deal_size: "Deal size",
};
const SCORE_CAPS = {
  qa_relevance: 25, company_size: 20, urgency: 20,
  nearshore_fit: 20, deal_size: 15,
};

function leadsApp() {
  return {
    leads: [],
    filters: { country: "", minScore: 0, status: "", q: "" },
    sort: "score-desc",
    expanded: {},
    statuses: JSON.parse(localStorage.getItem("leadStatuses") || "{}"),
    lastUpdate: "",
    scoreLabels: SCORE_LABELS,
    scoreCaps: SCORE_CAPS,

    async init() {
      const resp = await fetch("./data/leads.json", { cache: "no-cache" });
      this.leads = await resp.json();
      const lm = resp.headers.get("last-modified");
      this.lastUpdate = lm ? `Last update: ${new Date(lm).toLocaleString()}` : "";
    },

    get filtered() {
      const f = this.filters;
      let list = this.leads.filter(l => {
        if (f.country && l.company.country !== f.country) return false;
        if (f.minScore && l.lead_score < f.minScore) return false;
        if (f.status && this.getStatus(l) !== f.status) return false;
        if (f.q && !l.company.name.toLowerCase().includes(f.q.toLowerCase())) return false;
        return true;
      });
      switch (this.sort) {
        case "score-asc": list.sort((a,b) => a.lead_score - b.lead_score); break;
        case "score-desc": list.sort((a,b) => b.lead_score - a.lead_score); break;
        case "newest": list.sort((a,b) => (b.first_seen || "").localeCompare(a.first_seen || "")); break;
        case "name": list.sort((a,b) => a.company.name.localeCompare(b.company.name)); break;
      }
      return list;
    },

    toggle(id) { this.expanded[id] = !this.expanded[id]; },

    getStatus(lead) { return this.statuses[lead.lead_id] || lead.status || "new"; },

    setStatus(lead, status) {
      this.statuses[lead.lead_id] = status;
      localStorage.setItem("leadStatuses", JSON.stringify(this.statuses));
    },

    scoreClass(s) {
      if (s >= 70) return "text-emerald-700";
      if (s >= 50) return "text-amber-700";
      return "text-slate-500";
    },

    statusClass(s) {
      const map = {
        new: "bg-blue-100 text-blue-800",
        contacted: "bg-amber-100 text-amber-800",
        replied: "bg-purple-100 text-purple-800",
        client: "bg-emerald-100 text-emerald-800",
        dead: "bg-slate-200 text-slate-600",
      };
      return map[s] || map.new;
    },

    copyMessage(lead) {
      const text = `Subject: ${lead.outreach_message.subject}\n\n${lead.outreach_message.body}`;
      navigator.clipboard.writeText(text).then(() => { alert("Copied"); });
    },

    gmailUrl(lead) {
      const subject = encodeURIComponent(lead.outreach_message.subject);
      const body = encodeURIComponent(lead.outreach_message.body);
      return `https://mail.google.com/mail/?view=cm&fs=1&su=${subject}&body=${body}`;
    },
  };
}
