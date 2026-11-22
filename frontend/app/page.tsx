"use client";

import { useState, useEffect, useRef } from "react";

const API_URL = typeof window !== 'undefined' && window.location.hostname === 'localhost' 
  ? "http://localhost:8003"
  : "https://api.bluehawana.com";

type Period = { year: number; month: number };

// Invoices are collected for the PREVIOUS calendar month - worked out from today's date,
// so the site never needs to be edited or redeployed when a new month starts.
const previousMonth = (): Period => {
  const now = new Date();
  const d = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  return { year: d.getFullYear(), month: d.getMonth() + 1 };
};

const periodLabel = (p: Period) =>
  new Date(p.year, p.month - 1, 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

const periodQuery = (p: Period) => `year=${p.year}&month=${p.month}`;

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [statusKind, setStatusKind] = useState<"info" | "ok" | "error">("info");
  const [records, setRecords] = useState<any[]>([]);
  const [config, setConfig] = useState<any>({});
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [hasMounted, setHasMounted] = useState(false);
  const [period, setPeriod] = useState<Period>(previousMonth);
  const [dragging, setDragging] = useState(false);
  const [invoiceLink, setInvoiceLink] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const targetMonth = { ...period, display: periodLabel(period) };

  const say = (msg: string, kind: "info" | "ok" | "error" = "info") => {
    setStatus(msg);
    setStatusKind(kind);
  };

  const summarise = (recs: any[]) => {
    const hw = recs.reduce((n, r) => n + (r.handwritten_count || 0), 0);
    const matched = recs.reduce((n, r) => n + (r.matched_count || 0), 0);
    return { hw, matched };
  };

  // Invoices that matched a handwritten amount = exactly what needs to be printed
  const matchedFiles: string[] = Array.from(new Set(
    records.flatMap(r => (r.matches || []).map((m: any) => m.file).filter((f: any) => f && !String(f).startsWith("http")))
  ));

  const fetchStatus = async (p: Period = period) => {
    try {
      const res = await fetch(`${API_URL}/reconciliation-status?${periodQuery(p)}`);
      const data = await res.json();
      setRecords(data.records || []);
      if (data.config) setConfig(data.config);
      return data;
    } catch (err) {
      return null;
    }
  };

  const stopPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = null;
  };

  // Follow a running sync until the backend says it is finished
  const followSync = (p: Period) => {
    stopPolling();
    let ticks = 0;
    pollRef.current = setInterval(async () => {
      ticks++;
      const data = await fetchStatus(p);
      if (data?.syncing) {
        say(data.sync_message || "Collecting invoices...");
      }
      if ((data && !data.syncing) || ticks > 200) {
        stopPolling();
        setLoading(false);
        const { hw, matched } = summarise(data?.records || []);
        if (hw === 0) {
          say(`Invoices for ${periodLabel(p)} collected. Drop the photo of the handwritten sheet to match them.`, "ok");
        } else if (matched === hw) {
          say(`Done: all ${hw} handwritten amounts matched an invoice. Click "Print all matched".`, "ok");
        } else {
          say(`Done: ${matched} of ${hw} handwritten amounts matched. Check the rows marked "no invoice found".`, "info");
        }
      }
    }, 3000);
  };

  const startSync = async (p: Period = period) => {
    setLoading(true);
    say(`Collecting ${periodLabel(p)} invoices from Stripe and email (incl. last two weeks of the previous month)...`);
    try {
      await fetch(`${API_URL}/trigger-download?${periodQuery(p)}`, { method: "POST" });
      followSync(p);
    } catch (err) {
      say("Error: Could not start the invoice sync. Is the API online?", "error");
      setLoading(false);
    }
  };

  useEffect(() => {
    setHasMounted(true);
    (async () => {
      const data = await fetchStatus(period);
      if (data?.syncing) {
        setLoading(true);
        followSync(period);
      }
    })();
    return stopPolling;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!hasMounted) return null;

  const changePeriod = async (value: string) => {
    const [y, m] = value.split("-").map(Number);
    if (!y || !m) return;
    const p = { year: y, month: m };
    setPeriod(p);
    setSelectedFiles([]);
    say(`Loading ${periodLabel(p)}...`);
    const data = await fetchStatus(p);
    say(data ? `Showing ${periodLabel(p)}.` : "Error: API not reachable.", data ? "info" : "error");
  };

  const triggerDownload = () => startSync(period);

  // The whole job from one photo: read the sheet -> collect the month's invoices -> match
  // A PDF dropped here is an invoice to add (e.g. the Uber monthly statement from the Uber portal)
  const addInvoicePdf = async (file: File) => {
    const p = period;
    setLoading(true);
    say(`Adding ${file.name} to the ${periodLabel(p)} invoices...`);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch(`${API_URL}/upload-invoice?${periodQuery(p)}`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) {
        say(`Error: ${data.detail || "The PDF could not be added."}`, "error");
        return;
      }
      setRecords(data.records || []);
      const { hw, matched } = summarise(data.records || []);
      say(`${data.message}. ${matched} of ${hw} handwritten amounts now match.`, matched === hw && hw > 0 ? "ok" : "info");
    } catch (err) {
      say("Error: Failed to add the PDF. Is the API online?", "error");
    } finally {
      setLoading(false);
    }
  };

  // Paste the statement link copied from Uber Eats Manager instead of downloading the PDF first
  const addInvoiceLink = async (url: string) => {
    if (!url.trim()) return;
    const p = period;
    setLoading(true);
    say(`Fetching the Uber statement for ${periodLabel(p)}...`);
    try {
      const res = await fetch(`${API_URL}/upload-invoice-url?${periodQuery(p)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok) {
        say(`Error: ${data.detail || "The link could not be used."}`, "error");
        return;
      }
      setRecords(data.records || []);
      setInvoiceLink("");
      const { hw, matched } = summarise(data.records || []);
      say(`${data.message}. ${matched} of ${hw} handwritten amounts now match.`, matched === hw && hw > 0 ? "ok" : "info");
    } catch (err) {
      say("Error: Failed to fetch the link. Is the API online?", "error");
    } finally {
      setLoading(false);
    }
  };

  const processHandwritten = async (file: File) => {
    if (file.type === "application/pdf" || /\.pdf$/i.test(file.name)) {
      return addInvoicePdf(file);
    }
    if (!file.type.startsWith("image/") && !/\.(heic|heif|jpe?g|png|webp)$/i.test(file.name)) {
      say("Please drop a photo of the handwritten sheet (JPG, PNG, HEIC) or an invoice PDF.", "error");
      return;
    }
    const p = period;
    setLoading(true);
    say(`Step 1/3: AI is reading the handwriting in ${file.name} for ${periodLabel(p)}...`);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_URL}/upload-paper?${periodQuery(p)}`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok || data.ocr_ok === false) {
        say(`Error: ${data.message || data.detail || "The photo could not be read."}`, "error");
        setLoading(false);
        return;
      }
      setRecords(data.records || data.results || []);
      const { hw } = summarise(data.records || []);
      say(`Step 2/3: Read ${hw} amounts. Collecting the ${periodLabel(p)} invoices...`);
      // Step 2+3 run on the server; we just follow along
      await fetch(`${API_URL}/trigger-download?${periodQuery(p)}`, { method: "POST" });
      followSync(p);
    } catch (err) {
      say("Error: Failed to process the photo. Is the API online?", "error");
      setLoading(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";  // allow dropping the same photo again
    if (file) processHandwritten(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && !loading) processHandwritten(file);
  };

  // One PDF with everything -> one print dialog on THIS computer's printer
  const openMergedPdf = async (files: string[]) => {
    if (files.length === 0) return;
    const tab = window.open("", "_blank");
    try {
      const res = await fetch(`${API_URL}/merged-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_paths: files }),
      });
      if (!res.ok) throw new Error("merge failed");
      const url = URL.createObjectURL(await res.blob());
      if (tab) tab.location.href = url; else window.location.href = url;
    } catch (err) {
      if (tab) tab.close();
      say("Error: Could not build the print file.", "error");
    }
  };

  const handlePrintSelected = async () => {
    await openMergedPdf(selectedFiles);
  };

  const toggleFile = (filePath: string) => {
    setSelectedFiles(prev =>
      prev.includes(filePath)
        ? prev.filter(f => f !== filePath)
        : [...prev, filePath]
    );
  };

  const togglePartnerFiles = (files: string[]) => {
    const allSelected = files.every(f => selectedFiles.includes(f));
    if (allSelected) {
      setSelectedFiles(prev => prev.filter(f => !files.includes(f)));
    } else {
      const missing = files.filter(f => !selectedFiles.includes(f));
      setSelectedFiles(prev => [...prev, ...missing]);
    }
  };

  const handleSEBUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;

    setLoading(true);
    const fileName = e.target.files[0].name;
    setStatus(`Processing SEB transaction file: ${fileName}...`);

    const formData = new FormData();
    formData.append("file", e.target.files[0]);

    try {
      const res = await fetch(`${API_URL}/upload-seb-transactions?year=${targetMonth.year}&month=${targetMonth.month}`, {
        method: "POST",
        body: formData,
      });
      
      if (!res.ok) {
        const error = await res.json();
        say(`Error: ${error.detail || 'Failed to process SEB file'}`, "error");
        return;
      }

      const data = await res.json();
      say(`Bankgiro report generated! Found ${data.transactions_count} transaction days. Report ready for printing.`, "ok");
      
      // Refresh reconciliation status to show the new Bankgiro report
      await fetchStatus();
    } catch (err) {
      say("Error: Failed to process SEB transaction file.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-4 md:p-8 font-sans text-white">
      {/* Header with BlueHawana branding */}
      <header className="max-w-7xl mx-auto mb-8 md:mb-12">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
          <div className="flex items-center gap-4">
            <a href="https://www.bluehawana.com" className="text-blue-400 hover:text-blue-300 transition-colors">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </a>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                Invoice Management System
              </h1>
              <p className="text-slate-400 mt-1 text-sm md:text-base">Automated invoice collection & reconciliation for Ichiban Sushi</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg px-4 py-2 text-sm font-medium">
              <span className="text-slate-400">Period:</span> <span className="text-white ml-2">{targetMonth.display}</span>
            </div>
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg px-4 py-2 text-sm">
              {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </div>
          </div>
        </div>
        
        {/* Status bar */}
        <div className="bg-slate-800/30 backdrop-blur-sm border border-slate-700 rounded-lg p-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-slate-300">System Online</span>
            </div>
            <div className="flex gap-6 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">API:</span>
                <span className="text-green-400 font-medium">Connected</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Storage:</span>
                <span className="text-green-400 font-medium">R2 Active</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
        {/* Collection Card */}
        <section className="bg-slate-800/40 backdrop-blur-sm p-6 md:p-8 rounded-xl border border-slate-700 hover:border-slate-600 transition-all">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold">Invoice Collection</h2>
          </div>
          <p className="text-slate-400 mb-6 text-sm">Fetches Stripe payouts plus Wolt, Uber Eats and Foodora invoices from email, including the last two weeks of the previous month. Starts automatically after you drop the handwritten sheet.</p>

          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg border border-slate-700">
              <span className="font-medium text-slate-300">Target Month</span>
              <input
                type="month"
                value={`${period.year}-${String(period.month).padStart(2, "0")}`}
                onChange={(e) => changePeriod(e.target.value)}
                disabled={loading}
                className="bg-slate-800 border border-slate-600 rounded-md px-3 py-1.5 text-blue-400 font-semibold [color-scheme:dark]"
              />
            </div>

            <button
              onClick={triggerDownload}
              disabled={loading}
              className={`w-full py-4 rounded-lg font-semibold transition-all relative overflow-hidden group ${loading
                ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                : "bg-gradient-to-r from-blue-600 to-cyan-600 text-white hover:from-blue-500 hover:to-cyan-500 shadow-lg shadow-blue-500/20"
                }`}
            >
              <span className="relative z-10 flex items-center justify-center gap-2">
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Syncing...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Sync Invoices
                  </>
                )}
              </span>
            </button>
          </div>

          {status && (
            <div className={`mt-4 p-4 rounded-lg border text-sm flex items-start gap-3 ${
              statusKind === "error" ? "bg-red-500/10 border-red-500/40 text-red-300"
              : statusKind === "ok" ? "bg-green-500/10 border-green-500/40 text-green-300"
              : "bg-blue-500/10 border-blue-500/30 text-blue-300"}`}>
              <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{status}</span>
            </div>
          )}
        </section>

        {/* Upload Card */}
        <section className="bg-slate-800/40 backdrop-blur-sm p-6 md:p-8 rounded-xl border border-slate-700 hover:border-slate-600 transition-all">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold">Handwritten Records</h2>
          </div>
          <p className="text-slate-400 mb-6 text-sm">Drop one photo of the handwritten sheet. AI reads the amounts, the {targetMonth.display} invoices are collected and matched automatically, then print everything in one go.</p>

          <label
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center gap-4 transition-all cursor-pointer group relative ${
              dragging ? "border-cyan-400 bg-cyan-500/10" : "border-slate-600 hover:border-cyan-500 hover:bg-slate-800/30"
            } ${loading ? "opacity-60 pointer-events-none" : ""}`}
          >
            <input type="file" className="hidden" onChange={handleFileUpload} accept="image/*,.heic,.heif,.pdf,application/pdf" disabled={loading} />
            <div className="w-16 h-16 rounded-full bg-slate-700/50 group-hover:bg-cyan-500/20 flex items-center justify-center group-hover:scale-110 transition-all">
              <svg className="w-8 h-8 text-slate-400 group-hover:text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div className="text-center">
              <span className="text-sm font-medium text-slate-300 block mb-1">{loading ? "Working..." : `Drag & drop the ${targetMonth.display} sheet here, or click`}</span>
              <span className="text-xs text-slate-500">Photo of the sheet (PNG, JPG, HEIC), or a missing invoice PDF such as the Uber monthly statement</span>
            </div>
          </label>

          <div className="mt-4 flex gap-2">
            <input
              type="url"
              value={invoiceLink}
              onChange={(e) => setInvoiceLink(e.target.value)}
              placeholder="...or paste the Uber monthly statement link"
              disabled={loading}
              className="flex-1 min-w-0 bg-slate-900/50 border border-slate-600 rounded-md px-3 py-2 text-sm text-slate-200 placeholder-slate-500"
            />
            <button
              onClick={() => addInvoiceLink(invoiceLink)}
              disabled={loading || !invoiceLink.trim()}
              className="px-4 py-2 rounded-md text-sm font-semibold bg-slate-700 hover:bg-slate-600 disabled:opacity-40 transition-colors"
            >
              Add
            </button>
          </div>
        </section>

        {/* SEB Bankgiro Upload Card */}
        <section className="bg-slate-800/40 backdrop-blur-sm p-6 md:p-8 rounded-xl border border-slate-700 hover:border-slate-600 transition-all">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold">SEB Bankgiro Transactions</h2>
          </div>
          <p className="text-slate-400 mb-6 text-sm">Upload SEB transaction export (CSV) to generate Bankgiro specification report for days with multiple payments.</p>

          <label className="border-2 border-dashed border-slate-600 hover:border-green-500 rounded-xl p-8 flex flex-col items-center justify-center gap-4 hover:bg-slate-800/30 transition-all cursor-pointer group relative">
            <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" onChange={handleSEBUpload} accept=".csv,.xlsx,.xls" />
            <div className="w-16 h-16 rounded-full bg-slate-700/50 group-hover:bg-green-500/20 flex items-center justify-center group-hover:scale-110 transition-all">
              <svg className="w-8 h-8 text-slate-400 group-hover:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="text-center">
              <span className="text-sm font-medium text-slate-300 block mb-1">Upload SEB Export</span>
              <span className="text-xs text-slate-500">CSV or Excel file</span>
            </div>
          </label>
        </section>

        {/* Partner Status Section */}
        <section className="lg:col-span-2 bg-slate-800/40 backdrop-blur-sm p-6 md:p-8 rounded-xl border border-slate-700">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold">Integration Status</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { name: "Stripe", key: "Stripe", icon: "💳" },
              { name: "Foodora", key: "Foodora", icon: "🍕" },
              { name: "Uber Eats", key: "UberEats", icon: "🚗" },
              { name: "Wolt", key: "Wolt", icon: "⚡" },
              { name: "Swish", key: "Swish", icon: "💰" },
            ].map((partner) => {
              const isConnected = config[partner.key];
              return (
                <div key={partner.name} className={`p-4 rounded-lg border transition-all ${
                  isConnected 
                    ? 'border-green-500/30 bg-green-500/10' 
                    : 'border-slate-700 bg-slate-900/30'
                }`}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-400 animate-pulse" : "bg-slate-600"}`}></div>
                    <span className="font-semibold text-sm">{partner.icon} {partner.name}</span>
                  </div>
                  <span className={`text-xs ${isConnected ? "text-green-400" : "text-slate-500"}`}>
                    {isConnected ? "Connected" : "Not Configured"}
                  </span>
                </div>
              );
            })}
          </div>

          {records.length > 0 && (
            <div className="mt-8">
              <div className="flex items-center gap-3 mb-4">
                <h3 className="text-lg font-semibold text-cyan-400">Reconciliation Results</h3>
                <span className="px-3 py-1 bg-cyan-500/20 text-cyan-300 rounded-full text-xs font-medium">
                  {targetMonth.display} · {records.length} Partners
                </span>
                {matchedFiles.length > 0 && (
                  <a
                    href={`${API_URL}/print-pdf?${periodQuery(period)}`}
                    target="_blank"
                    rel="noopener"
                    className="ml-auto bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white px-4 py-2 rounded-lg font-bold text-sm transition-all shadow-lg shadow-green-500/20"
                  >
                    🖨 Print all matched ({matchedFiles.length})
                  </a>
                )}
              </div>
              <div className="overflow-x-auto rounded-lg border border-slate-700">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-900/50">
                    <tr className="border-b border-slate-700">
                      <th className="py-3 px-4 w-10">
                        <input
                          type="checkbox"
                          className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-900"
                          onChange={(e) => {
                            if (e.target.checked) {
                              const all = records.flatMap(r => r.files || []);
                              setSelectedFiles(all);
                            } else {
                              setSelectedFiles([]);
                            }
                          }}
                        />
                      </th>
                      <th className="py-3 px-4 font-semibold text-slate-400">Partner</th>
                      <th className="py-3 px-4 font-semibold text-slate-400">Status</th>
                      <th className="py-3 px-4 font-semibold text-slate-400">Handwritten → Invoice Match</th>
                      <th className="py-3 px-4 font-semibold text-slate-400 text-right">Total (SEK)</th>
                      <th className="py-3 px-4 font-semibold text-slate-400 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((record) => (
                      <tr key={record.partner} className="border-b border-slate-800 last:border-0 hover:bg-slate-800/30 transition-colors align-top">
                        <td className="py-4 px-4">
                          {record.files && record.files.length > 0 && (
                            <input
                              type="checkbox"
                              className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-900"
                              checked={record.files.every((f: any) => selectedFiles.includes(f))}
                              onChange={() => togglePartnerFiles(record.files)}
                            />
                          )}
                        </td>
                        <td className="py-4 px-4 font-medium text-white">{record.partner}</td>
                        <td className="py-4 px-4">
                          {record.reconciled ? (
                            <span className="px-2 py-1 bg-green-500/20 text-green-400 border border-green-500/30 rounded-md text-xs font-bold uppercase tracking-wider">
                              ✓ Matched
                            </span>
                          ) : record.handwritten_count === 0 ? (
                            <span className="px-2 py-1 bg-slate-600/20 text-slate-400 border border-slate-600/30 rounded-md text-xs font-bold uppercase tracking-wider">
                              No Handwriting
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-md text-xs font-bold uppercase tracking-wider">
                              {record.matched_count}/{record.handwritten_count} Matched
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-4 text-xs max-w-sm">
                          {/* Matched pairs */}
                          {record.matches && record.matches.length > 0 && (
                            <div className="space-y-1">
                              {record.matches.map((m: any, i: number) => (
                                <div key={i} className="flex items-center gap-2">
                                  <span className="text-slate-300 font-mono">{Number(m.hw).toLocaleString('sv-SE', {minimumFractionDigits: 2})} kr</span>
                                  <span className="text-slate-500">→</span>
                                  <span className="text-green-400 font-mono">{m.pdf != null ? Number(m.pdf).toLocaleString('sv-SE', {minimumFractionDigits: 2}) + ' kr' : 'linked'}</span>
                                  {m.corrected && (
                                    <span className="text-amber-400 text-[10px] border border-amber-500/30 bg-amber-500/10 px-1 rounded" title="The handwritten amount differed by one digit from the real payout">digit corrected</span>
                                  )}
                                  {m.diff != null && m.diff > 0.005 && !m.corrected && (
                                    <span className="text-amber-500/70 text-[10px]">(Δ{Number(m.diff).toFixed(2)})</span>
                                  )}
                                  {m.file && (
                                    <a href={`${API_URL}/view-file?path=${encodeURIComponent(m.file)}`} target="_blank"
                                      className="text-blue-400 hover:text-blue-300 text-[10px] border border-blue-500/20 bg-blue-500/10 px-1 rounded">📄</a>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                          {/* Unmatched handwritten amounts */}
                          {record.unmatched && record.unmatched.length > 0 && (
                            <div className="space-y-1 mt-1">
                              {record.unmatched.map((amt: number, i: number) => (
                                <div key={i} className="flex items-center gap-2">
                                  <span className="text-slate-300 font-mono">{Number(amt).toLocaleString('sv-SE', {minimumFractionDigits: 2})} kr</span>
                                  <span className="text-red-400 text-[10px] border border-red-500/30 bg-red-500/10 px-1 rounded">no invoice found</span>
                                  {(() => {
                                    const near = (record.near_misses || []).find((n: any) => n.hw === amt);
                                    return near && near.pdf != null ? (
                                      <span className="text-slate-500 text-[10px]">closest invoice: {Number(near.pdf).toLocaleString('sv-SE', {minimumFractionDigits: 2})} kr</span>
                                    ) : null;
                                  })()}
                                </div>
                              ))}
                            </div>
                          )}
                          {record.other_files && record.other_files.length > 0 && (
                            <div className="text-slate-600 text-[10px] mt-1">
                              {record.other_files.length} other invoice{record.other_files.length > 1 ? 's' : ''} from the period not on the sheet (hidden, not printed)
                            </div>
                          )}
                          {/* Files with no handwritten record */}
                          {(!record.matches || record.matches.length === 0) && (!record.unmatched || record.unmatched.length === 0) && record.files && record.files.length > 0 && (
                            <span className="text-slate-500 italic">
                              {record.files.length} invoice{record.files.length > 1 ? 's' : ''} found, upload handwritten record to match
                            </span>
                          )}
                          {(!record.files || record.files.length === 0) && record.amounts?.length > 0 && (
                            <span className="text-amber-500/70 italic">No invoices collected yet</span>
                          )}
                        </td>
                        <td className="py-4 px-4 text-right font-bold text-cyan-400">
                          {record.handwritten_total > 0
                            ? record.handwritten_total.toLocaleString('sv-SE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' kr'
                            : '—'}
                        </td>
                        <td className="py-4 px-4 text-right">
                          {record.files && record.files.length > 0 && (
                            <div className="flex flex-col items-end gap-2">
                              <div className="flex gap-1.5 flex-wrap justify-end max-w-xs">
                                {record.files.map((file: string, idx: number) => (
                                  <a
                                    key={idx}
                                    href={`${API_URL}/view-file?path=${encodeURIComponent(file)}`}
                                    target="_blank"
                                    className="text-xs text-blue-400 hover:text-blue-300 font-medium border border-blue-500/30 bg-blue-500/10 px-2 py-1 rounded transition-colors"
                                    title={file.split('/').pop()}
                                  >
                                    📄 {idx + 1}
                                  </a>
                                ))}
                              </div>
                              <a
                                href={`${API_URL}/print-pdf?${periodQuery(period)}&partner=${encodeURIComponent(record.partner)}`}
                                target="_blank"
                                rel="noopener"
                                className="text-sm text-slate-300 hover:text-white font-medium bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-md transition-colors flex items-center gap-2"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                                </svg>
                                Print ({record.files.length})
                              </a>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {selectedFiles.length > 0 && (
                <div className="mt-6 flex justify-between items-center p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                  <span className="text-sm text-slate-400">
                    {selectedFiles.length} file(s) selected
                  </span>
                  <button
                    onClick={handlePrintSelected}
                    className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white px-6 py-3 rounded-lg font-bold transition-all shadow-lg shadow-blue-500/20 flex items-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                    </svg>
                    Print Selected ({selectedFiles.length})
                  </button>
                </div>
              )}
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto mt-12 pt-8 border-t border-slate-800">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-slate-500">
          <div className="flex items-center gap-2">
            <span>Powered by</span>
            <a href="https://www.bluehawana.com" className="text-blue-400 hover:text-blue-300 font-medium transition-colors">
              BlueHawana
            </a>
          </div>
          <div className="flex items-center gap-6">
            <span>© 2025 Ichiban Sushi</span>
            <span className="text-slate-700">|</span>
            <span>Invoice Management System v1.0</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
