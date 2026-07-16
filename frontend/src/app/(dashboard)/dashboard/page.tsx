"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  FileSearch,
  TrendingUp,
  Clock,
  BarChart3,
  ArrowUpRight,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { AnalyticsData, Analysis } from "@/types";
import { formatDate, getScoreColor } from "@/lib/utils";

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [recentAnalyses, setRecentAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsRes, historyRes] = await Promise.all([
          api.get("/analysis/analytics"),
          api.get("/analysis/?page=1&per_page=5"),
        ]);
        setAnalytics(analyticsRes.data);
        setRecentAnalyses(historyRes.data.analyses);
      } catch (error) {
        console.error("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const statCards = [
    {
      title: "Total Analyses",
      value: analytics?.total_analyses || 0,
      icon: FileSearch,
      color: "text-primary-light",
      bg: "bg-primary/10",
    },
    {
      title: "Average ATS Score",
      value: `${analytics?.average_ats_score || 0}%`,
      icon: TrendingUp,
      color: "text-success",
      bg: "bg-success/10",
    },
    {
      title: "This Week",
      value: analytics?.weekly_activity?.reduce((a, b) => a + b.count, 0) || 0,
      icon: Clock,
      color: "text-accent",
      bg: "bg-accent/10",
    },
    {
      title: "Top Skills",
      value: analytics?.most_common_skills?.length || 0,
      icon: BarChart3,
      color: "text-warning",
      bg: "bg-warning/10",
    },
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 rounded-xl bg-background-card animate-pulse" />
          ))}
        </div>
        <div className="h-96 rounded-xl bg-background-card animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-2xl font-bold text-gray-100 mb-1">Dashboard</h1>
        <p className="text-gray-400 text-sm">Welcome back! Here&apos;s your resume analysis overview.</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, i) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Card className="hover:border-primary/30 transition-all duration-300">
              <CardContent className="p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400 mb-1">{card.title}</p>
                    <p className="text-2xl font-bold text-gray-100">{card.value}</p>
                  </div>
                  <div className={`w-10 h-10 rounded-xl ${card.bg} flex items-center justify-center`}>
                    <card.icon className={`w-5 h-5 ${card.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Analyses</CardTitle>
            <Link href="/history">
              <Button variant="ghost" size="sm">
                View All <ArrowUpRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {recentAnalyses.length === 0 ? (
              <div className="text-center py-12">
                <FileSearch className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 mb-4">No analyses yet</p>
                <Link href="/analyze">
                  <Button>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Analyze Your First Resume
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {recentAnalyses.map((analysis) => (
                  <div
                    key={analysis.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-background/50 hover:bg-background-elevated transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <FileSearch className="w-5 h-5 text-primary-light" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-200">
                          Analysis #{analysis.id}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatDate(analysis.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={analysis.ats_score && analysis.ats_score >= 60 ? "success" : "warning"}>
                        ATS: {analysis.ats_score || 0}%
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link href="/analyze" className="block">
              <Button className="w-full justify-start" variant="outline">
                <FileSearch className="w-4 h-4 mr-2" />
                Analyze Resume
              </Button>
            </Link>
            <Link href="/history" className="block">
              <Button className="w-full justify-start" variant="outline">
                <Clock className="w-4 h-4 mr-2" />
                View History
              </Button>
            </Link>
            <Link href="/saved-jobs" className="block">
              <Button className="w-full justify-start" variant="outline">
                <BarChart3 className="w-4 h-4 mr-2" />
                Saved Jobs
              </Button>
            </Link>

            {analytics?.most_common_skills && analytics.most_common_skills.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-800">
                <p className="text-sm font-medium text-gray-300 mb-3">Top Skills</p>
                <div className="flex flex-wrap gap-2">
                  {analytics.most_common_skills.slice(0, 6).map((skill) => (
                    <Badge key={skill.skill} variant="secondary">
                      {skill.skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Score Distribution */}
      {analytics?.score_distribution && (
        <Card>
          <CardHeader>
            <CardTitle>Score Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              {[
                { label: "Excellent (80+)", value: analytics.score_distribution.excellent, color: "bg-success" },
                { label: "Good (60-79)", value: analytics.score_distribution.good, color: "bg-primary" },
                { label: "Average (40-59)", value: analytics.score_distribution.average, color: "bg-warning" },
                { label: "Poor (<40)", value: analytics.score_distribution.poor, color: "bg-danger" },
              ].map((item) => (
                <div key={item.label} className="text-center p-4 rounded-xl bg-background/50">
                  <div className={`w-full h-2 rounded-full ${item.color} mb-3`} />
                  <p className="text-2xl font-bold text-gray-100">{item.value}</p>
                  <p className="text-xs text-gray-400 mt-1">{item.label}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
