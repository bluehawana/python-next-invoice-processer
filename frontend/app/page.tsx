"use client";

import { useState, useEffect } from "react";

const API_URL = typeof window !== 'undefined' && window.location.hostname === 'localhost' 
  ? "http://localhost:8000"
  : "https://api.bluehawana.com";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [records, setRecords] = useState<any[]>([]);
  const [config, setConfig] = useState<any>({});
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [hasMounted, setHasMounted] = useState(false);

  // Calculate previous month (the month we're collecting invoices for)
  const getPreviousMonth = () => {
    const now = new Date();
    const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    return {
      year: lastMonth.getFullYear(),
      month: lastMonth.getMonth() + 1, // JavaScript months are 0-indexed
      display: lastMonth.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    };
  };

  const targetMonth = getPreviousMonth();

  // Moved definition UP before usage to fix ReferenceError
  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/reconciliation-status`);
      const data = await res.json();
      setRecords(data.records);
      if (data.config) setConfig(data.config);
    } catch (err) { }
  };

  useEffect(() => {
    setHasMounted(true);
    fetchStatus();
  }, []);

  if (!hasMounted) return null;

  const triggerDownload = async () => {
    setLoading(true);
    setStatus("Phase 2: Connecting to Stripe and fetching Gmail invoices...");
    try {
      const res = await fetch(`${API_URL}/trigger-download?year=${targetMonth.year}&month=${targetMonth.month}`, {
        method: "POST",
      });
      const data = await res.json();
      setStatus("Digital Sync Started! Invoices will appear in the table as they are found.");

      // Poll periodically for ~45 seconds
      let pollCount = 0;
      const interval = setInterval(async () => {
        pollCount++;
        await fetchStatus(); // Wait for the fetch to complete
        if (pollCount > 40) { // Increased to ~2 minutes
          clearInterval(interval);
          setStatus("Syncing complete. All available invoices should be linked.");
        }
      }, 3000);
    } catch (err) {
      setStatus("Error: Could not sync invoices.");
    } finally {
      setLoading(false);
    }
  };

  const handlePrintSelected = async () => {
    if (selectedFiles.length === 0) return;
    try {
      await fetch(`${API_URL}/print-batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(selectedFiles),
      });
      alert(`Sent ${selectedFiles.length} files to printer!`);
      setSelectedFiles([]);
    } catch (err) {
      alert("Print failed.");
    }
  };

  const toggleFile = (filePath: string) => {
    setSelectedFiles(prev =>
      prev.includes(filePath)
        ? prev.filter(f => f !== filePath)
        : [...prev, filePath]
    );
  };

  const handlePrint = async (filePath: string) => {
    try {
      await fetch(`${API_URL}/print-file?file_path=${encodeURIComponent(filePath)}`, {
        method: "POST",
      });
      alert("Print job sent!");
    } catch (err) {
      alert("Failed to print.");
    }
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

  const handlePrintBatch = async (files: string[]) => {
    try {
      await fetch(`${API_URL}/print-batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(files),
      });
      alert(`Sent ${files.length} files to printer!`);
    } catch (err) {
      alert("Print failed.");
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;

    setLoading(true);
    const fileName = e.target.files[0].name;
    setStatus(`Phase 1: Recognizing handwriting from ${fileName}...`);

    const formData = new FormData();
    formData.append("file", e.target.files[0]);

    try {
      const res = await fetch(`${API_URL}/upload-paper`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      setRecords(data.results);
      setStatus("OCR Finished! Please verify results in the table. When ready, click 'Sync' to fetch digital copies.");
    } catch (err) {
      setStatus("Error: Failed to process paper.");
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
          <p className="text-slate-400 mb-6 text-sm">Automatically fetch invoices from Stripe, Wolt, Uber Eats, and Foodora via API and email.</p>

          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg border border-slate-700">
              <span className="font-medium text-slate-300">Target Month</span>
              <span className="text-blue-400 font-semibold">{targetMonth.display}</span>
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
            <div className="mt-4 p-4 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300 text-sm flex items-start gap-3">
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
          <p className="text-slate-400 mb-6 text-sm">Upload a photo of handwritten income records for OCR processing and reconciliation.</p>

          <label className="border-2 border-dashed border-slate-600 hover:border-cyan-500 rounded-xl p-8 flex flex-col items-center justify-center gap-4 hover:bg-slate-800/30 transition-all cursor-pointer group relative">
            <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" onChange={handleFileUpload} accept="image/*" />
            <div className="w-16 h-16 rounded-full bg-slate-700/50 group-hover:bg-cyan-500/20 flex items-center justify-center group-hover:scale-110 transition-all">
              <svg className="w-8 h-8 text-slate-400 group-hover:text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div className="text-center">
              <span className="text-sm font-medium text-slate-300 block mb-1">Click to upload or drag & drop</span>
              <span className="text-xs text-slate-500">PNG, JPG, HEIC up to 10MB</span>
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
                  {records.length} Partners
                </span>
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
                      <th className="py-3 px-4 font-semibold text-slate-400">Records</th>
                      <th className="py-3 px-4 font-semibold text-slate-400 text-right">Total (SEK)</th>
                      <th className="py-3 px-4 font-semibold text-slate-400 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((record) => (
                      <tr key={record.partner} className="border-b border-slate-800 last:border-0 hover:bg-slate-800/30 transition-colors">
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
                              ✓ Reconciled
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-md text-xs font-bold uppercase tracking-wider">
                              {record.matched_count}/{record.handwritten_count} Linked
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-4 text-slate-400 text-xs max-w-xs truncate">
                          {record.amounts?.length > 0 ? `${record.amounts.length} entries` : 'No data'}
                        </td>
                        <td className="py-4 px-4 text-right font-bold text-cyan-400">
                          {record.handwritten_total?.toLocaleString('sv-SE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} kr
                        </td>
                        <td className="py-4 px-4 text-right space-x-2">
                          {record.files && record.files.length > 0 && (
                            <div className="flex flex-col items-end gap-2">
                              {/* View Buttons */}
                              <div className="flex gap-2 flex-wrap justify-end">
                                {record.files.slice(0, 3).map((file: string, idx: number) => (
                                  <a
                                    key={idx}
                                    href={`${API_URL}/view-file?path=${encodeURIComponent(file)}`}
                                    target="_blank"
                                    className="text-xs text-blue-400 hover:text-blue-300 font-medium border border-blue-500/30 bg-blue-500/10 px-2 py-1 rounded transition-colors"
                                    title={`View Invoice ${idx + 1}`}
                                  >
                                    📄 {idx + 1}
                                  </a>
                                ))}
                                {record.files.length > 3 && (
                                  <span className="text-xs text-slate-500 px-2 py-1">+{record.files.length - 3}</span>
                                )}
                              </div>
                              <button
                                onClick={() => handlePrintBatch(record.files)}
                                className="text-sm text-slate-300 hover:text-white font-medium bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-md transition-colors flex items-center gap-2"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                                </svg>
                                Print All ({record.files.length})
                              </button>
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
