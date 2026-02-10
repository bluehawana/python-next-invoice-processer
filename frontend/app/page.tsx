"use client";

import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [records, setRecords] = useState<any[]>([]);
  const [config, setConfig] = useState<any>({});
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [hasMounted, setHasMounted] = useState(false);

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
      const res = await fetch(`${API_URL}/trigger-download?year=2025&month=12`, {
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
    <div className="min-h-screen bg-slate-50 dark:bg-zinc-950 p-8 font-sans text-zinc-900 dark:text-zinc-100">
      <header className="max-w-5xl mx-auto mb-12 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Invoice Center</h1>
          <p className="text-zinc-500 dark:text-zinc-400 mt-2">Manage your restaurant invoices automatically.</p>
        </div>
        <div className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-xl px-4 py-2 text-sm font-medium">
          {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        </div>
      </header>

      <main className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Collection Card */}
        <section className="bg-white dark:bg-zinc-900 p-8 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800">
          <h2 className="text-xl font-semibold mb-4">Invoice Collection</h2>
          <p className="text-zinc-500 mb-6">Fetch the latest invoices from Foodora, UberEats, Stripe, and Wolt for the previous month.</p>

          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-xl border border-zinc-100 dark:border-zinc-800">
              <span className="font-medium">Target Month</span>
              <span className="text-zinc-500">Dec 2025</span>
            </div>

            <button
              onClick={triggerDownload}
              disabled={loading}
              className={`w-full py-4 rounded-xl font-semibold transition-all shadow-lg shadow-emerald-500/10 ${loading
                ? "bg-zinc-200 text-zinc-500 cursor-not-allowed"
                : "bg-emerald-600 text-white hover:bg-emerald-700"
                }`}
            >
              {loading ? "Syncing..." : "🔄 Sync Invoices (API & Email)"}
            </button>
          </div>

          {status && (
            <div className="mt-4 p-4 rounded-xl bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 text-sm">
              {status}
            </div>
          )}
        </section>

        {/* Upload Card */}
        <section className="bg-white dark:bg-zinc-900 p-8 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800">
          <h2 className="text-xl font-semibold mb-4">Yan's Records</h2>
          <p className="text-zinc-500 mb-6">Upload a photo of the handwritten income paper to reconcile with invoices.</p>

          <label className="border-2 border-dashed border-zinc-200 dark:border-zinc-800 rounded-2xl p-8 flex flex-col items-center justify-center gap-4 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors cursor-pointer group relative">
            <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" onChange={handleFileUpload} accept="image/*" />
            <div className="w-12 h-12 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
            </div>
            <span className="text-sm font-medium">Click to upload or drag & drop</span>
            <span className="text-xs text-zinc-400">PNG, JPG up to 10MB</span>
          </label>
        </section>

        {/* Status Section */}
        <section className="md:col-span-2 bg-white dark:bg-zinc-900 p-8 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800">
          <h2 className="text-xl font-semibold mb-6">Partner Status</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { name: "Stripe", key: "Stripe" },
              { name: "Foodora", key: "Foodora" },
              { name: "UberEats", key: "UberEats" },
              { name: "Wolt", key: "Wolt" },
              { name: "Swish", key: "Swish" },
            ].map((partner) => {
              const isConnected = config[partner.key];
              return (
                <div key={partner.name} className="p-4 rounded-xl border border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/50">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-500" : "bg-zinc-300"}`}></div>
                    <span className="font-semibold text-sm">{partner.name}</span>
                  </div>
                  <span className="text-xs text-zinc-500">{isConnected ? "Ready" : "Not Configured"}</span>
                </div>
              );
            })}
          </div>

          {records.length > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold mb-4 text-emerald-600 dark:text-emerald-400">Successfully Parsed Records</h3>
              <div className="overflow-x-auto rounded-xl border border-zinc-100 dark:border-zinc-800">
                <table className="w-full text-left text-sm">
                  <thead className="bg-zinc-50 dark:bg-zinc-800/50">
                    <tr className="border-b border-zinc-100 dark:border-zinc-800">
                      <th className="py-3 px-4 w-10">
                        <input
                          type="checkbox"
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
                      <th className="py-3 px-4 font-semibold text-zinc-500">Partner</th>
                      <th className="py-3 px-4 font-semibold text-zinc-500">Status</th>
                      <th className="py-3 px-4 font-semibold text-zinc-500">Daily Records</th>
                      <th className="py-3 px-4 font-semibold text-zinc-500 text-right">Monthly Total</th>
                      <th className="py-3 px-4 font-semibold text-zinc-500 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((record) => (
                      <tr key={record.partner} className="border-b border-zinc-50 dark:border-zinc-800 last:border-0 hover:bg-zinc-50/50 transition-colors">
                        <td className="py-4 px-4">
                          {record.files && record.files.length > 0 && (
                            <input
                              type="checkbox"
                              checked={record.files.every((f: any) => selectedFiles.includes(f))}
                              onChange={() => togglePartnerFiles(record.files)}
                            />
                          )}
                        </td>
                        <td className="py-4 px-4 font-medium">{record.partner}</td>
                        <td className="py-4 px-4">
                          {record.reconciled ? (
                            <span className="px-2 py-1 bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400 rounded-md text-xs font-bold uppercase tracking-wider">
                              Reconciled
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 rounded-md text-xs font-bold uppercase tracking-wider">
                              {record.matched_count}/{record.handwritten_count} Linked
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-4 text-zinc-500 max-w-xs truncate">{record.amounts?.join(", ")}</td>
                        <td className="py-4 px-4 text-right font-bold text-zinc-900 dark:text-zinc-100">
                          {record.handwritten_total?.toLocaleString('sv-SE', { style: 'currency', currency: 'SEK' })}
                        </td>
                        <td className="py-4 px-4 text-right space-x-2">
                          {record.files && record.files.length > 0 && (
                            <div className="flex flex-col items-end gap-2">
                              {/* Action Buttons */}
                              <div className="flex gap-2 flex-wrap justify-end">
                                {record.files.map((file: string, idx: number) => (
                                  <a
                                    key={idx}
                                    href={`${API_URL}/view-file?path=${encodeURIComponent(file)}`}
                                    target="_blank"
                                    className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 font-medium border border-blue-100 dark:border-blue-900 px-2 py-1 rounded"
                                    title={`View Invoice ${idx + 1}`}
                                  >
                                    View {idx + 1}
                                  </a>
                                ))}
                              </div>
                              <button
                                onClick={() => handlePrintBatch(record.files)}
                                className="text-sm text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100 font-medium bg-zinc-100 dark:bg-zinc-800 px-3 py-1.5 rounded-md w-fit"
                              >
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
                <div className="mt-6 flex justify-end">
                  <button
                    onClick={handlePrintSelected}
                    className="bg-black text-white dark:bg-white dark:text-black px-6 py-3 rounded-xl font-bold hover:scale-105 transition-transform"
                  >
                    🖨️ Print Selected ({selectedFiles.length})
                  </button>
                </div>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
