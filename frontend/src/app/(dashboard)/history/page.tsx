"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { History as HistoryIcon, Trash2, Search, Download, FileText, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { Analysis } from "@/types";
import { formatDate, getScoreColor } from "@/lib/utils";
import toast from "react-hot-toast";

export default function HistoryPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [deleting, setDeleting] = useState<number | null>(null);

  const fetchAnalyses = async (p: number) => {
    setLoading(true);
    try {
      const res = await api.get(`/analysis/?page=${p}&per_page=10`);
      setAnalyses(res.data.analyses);
      setTotal(res.data.total);
    } catch {
      toast.error("Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses(page);
  }, [page]);

  const handleDelete = async (id: number) => {
    setDeleting(id);
    try {
      await api.delete(`/analysis/${id}`);
      setAnalyses((prev) => prev.filter((a) => a.id !== id));
      setTotal((prev) => prev - 1);
      toast.success("Analysis deleted");
    } catch {
      toast.error("Failed to delete");
    } finally {
      setDeleting(null);
    }
  };

  const filtered = analyses.filter(
    (a) =>
      a.resume_id.toString().includes(search) ||
      formatDate(a.created_at).toLowerCase().includes(search.toLowerCase())
  );

  const totalPages = Math.ceil(total / 10);

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-gray-100 mb-1">Analysis History</h1>
        <p className="text-gray-400 text-sm">View and manage your past resume analyses</p>
      </motion.div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <Input
            placeholder="Search by ID or date..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <p className="text-sm text-gray-400">{total} analyses total</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <HistoryIcon className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 mb-2">No analyses found</p>
            <p className="text-sm text-gray-500">Upload a resume to get started</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-3">
            {filtered.map((analysis, i) => (
              <motion.div
                key={analysis.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
              >
                <Card className="hover:border-primary/30 transition-all">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <FileText className="w-5 h-5 text-primary-light" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-200">
                            Analysis #{analysis.id}
                          </p>
                          <p className="text-xs text-gray-500">
                            Resume #{analysis.resume_id} &middot; {formatDate(analysis.created_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {analysis.ats_score && (
                          <Badge variant={analysis.ats_score >= 60 ? "success" : analysis.ats_score >= 40 ? "warning" : "danger"}>
                            ATS: {analysis.ats_score}%
                          </Badge>
                        )}
                        {analysis.match_percentage != null && (
                          <Badge variant="secondary">Match: {analysis.match_percentage}%</Badge>
                        )}
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Download className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-danger hover:text-danger"
                            onClick={() => handleDelete(analysis.id)}
                            disabled={deleting === analysis.id}
                          >
                            {deleting === analysis.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Previous
              </Button>
              <span className="text-sm text-gray-400">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
