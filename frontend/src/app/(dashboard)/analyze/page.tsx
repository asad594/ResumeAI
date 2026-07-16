"use client";

import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileText,
  X,
  Loader2,
  Sparkles,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import api from "@/lib/api";
import { Resume, Analysis, ATSDetails } from "@/types";
import { formatFileSize, getScoreColor, getScoreBg } from "@/lib/utils";
import toast from "react-hot-toast";

type Step = "upload" | "details" | "results";

function CircularScore({ score, size = 160 }: { score: number; size?: number }) {
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const getColor = (s: number) => {
    if (s >= 80) return "#22C55E";
    if (s >= 60) return "#EAB308";
    return "#EF4444";
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#334155"
          strokeWidth="8"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute text-center">
        <p className={`text-3xl font-bold ${getScoreColor(score)}`}>{Math.round(score)}</p>
        <p className="text-xs text-gray-400">out of 100</p>
      </div>
    </div>
  );
}

export default function AnalyzePage() {
  const [step, setStep] = useState<Step>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [resume, setResume] = useState<Resume | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const selectedFile = acceptedFiles[0];
    if (!selectedFile) return;

    const maxSize = 10 * 1024 * 1024;
    if (selectedFile.size > maxSize) {
      toast.error("File size must be less than 10MB");
      return;
    }

    setFile(selectedFile);
    setUploading(true);
    setUploadProgress(0);

    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 10;
      });
    }, 100);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const res = await api.post("/resumes/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResume(res.data);
      setUploadProgress(100);
      toast.success("Resume uploaded successfully!");
      setStep("details");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      clearInterval(interval);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"] },
    maxFiles: 1,
    disabled: uploading,
  });

  const handleAnalyze = async () => {
    if (!resume) return;
    setAnalyzing(true);
    try {
      const res = await api.post("/analysis/", {
        resume_id: resume.id,
        job_description: jobDescription || undefined,
      });
      setAnalysis(res.data);
      setStep("results");
      toast.success("Analysis complete!");
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  const reset = () => {
    setStep("upload");
    setFile(null);
    setResume(null);
    setJobDescription("");
    setAnalysis(null);
    setUploadProgress(0);
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-gray-100 mb-1">Resume Analyzer</h1>
        <p className="text-gray-400 text-sm">Upload your resume and get AI-powered insights</p>
      </motion.div>

      {/* Steps indicator */}
      <div className="flex items-center gap-4 mb-6">
        {(["upload", "details", "results"] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                step === s
                  ? "bg-primary text-white"
                  : i < ["upload", "details", "results"].indexOf(step)
                  ? "bg-success text-white"
                  : "bg-gray-800 text-gray-500"
              }`}
            >
              {i < ["upload", "details", "results"].indexOf(step) ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                i + 1
              )}
            </div>
            <span className={`text-sm capitalize ${step === s ? "text-gray-100" : "text-gray-500"}`}>
              {s}
            </span>
            {i < 2 && <div className="w-12 h-px bg-gray-700 mx-2" />}
          </div>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {/* Step 1: Upload */}
        {step === "upload" && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <Card>
              <CardContent className="p-8">
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 cursor-pointer ${
                    isDragActive
                      ? "border-primary bg-primary/5"
                      : "border-gray-700 hover:border-primary/50 hover:bg-primary/5"
                  }`}
                >
                  <input {...getInputProps()} />
                  {uploading ? (
                    <div className="space-y-4">
                      <Loader2 className="w-12 h-12 text-primary-light mx-auto animate-spin" />
                      <p className="text-gray-300">Uploading...</p>
                      <Progress value={uploadProgress} className="max-w-xs mx-auto" />
                    </div>
                  ) : (
                    <>
                      <Upload className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-gray-200 mb-2">
                        {isDragActive ? "Drop your resume here" : "Drag & drop your resume"}
                      </h3>
                      <p className="text-gray-400 text-sm mb-4">
                        or click to browse files
                      </p>
                      <div className="flex items-center justify-center gap-4 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <FileText className="w-3 h-3" /> PDF
                        </span>
                        <span className="flex items-center gap-1">
                          <FileText className="w-3 h-3" /> DOCX
                        </span>
                        <span>Max 10MB</span>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Step 2: Details */}
        {step === "details" && resume && (
          <motion.div
            key="details"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-primary-light" />
                  Uploaded Resume
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between p-4 rounded-xl bg-background/50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-primary-light" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-200">{resume.original_filename}</p>
                      <p className="text-xs text-gray-500">{formatFileSize(resume.file_size)}</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => { setFile(null); setResume(null); setStep("upload"); }}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>

                {resume.extracted_data && (
                  <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { label: "Name", value: resume.extracted_data.name },
                      { label: "Email", value: resume.extracted_data.email },
                      { label: "Phone", value: resume.extracted_data.phone },
                      { label: "Skills", value: `${resume.extracted_data.skills?.length || 0} found` },
                    ].map((item) => (
                      <div key={item.label} className="p-3 rounded-lg bg-background/50">
                        <p className="text-xs text-gray-500 mb-1">{item.label}</p>
                        <p className="text-sm text-gray-200 truncate">{item.value || "Not found"}</p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Job Description (Optional)</CardTitle>
              </CardHeader>
              <CardContent>
                <Label htmlFor="jobDesc" className="mb-2 block text-gray-400 text-sm">
                  Paste a job description to compare your resume against
                </Label>
                <Textarea
                  id="jobDesc"
                  placeholder="Paste the job description here for better analysis and job matching..."
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  rows={6}
                />
              </CardContent>
            </Card>

            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={reset}>
                Start Over
              </Button>
              <Button onClick={handleAnalyze} disabled={analyzing} size="lg">
                {analyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Analyze Resume
                  </>
                )}
              </Button>
            </div>
          </motion.div>
        )}

        {/* Step 3: Results */}
        {step === "results" && analysis && (
          <motion.div
            key="results"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {/* ATS Score */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary-light" />
                  ATS Score
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col md:flex-row items-center gap-8">
                  <CircularScore score={analysis.ats_score?.overall || 0} />
                  <div className="flex-1 grid grid-cols-2 md:grid-cols-3 gap-4 w-full">
                    {analysis.ats_score && Object.entries(analysis.ats_score)
                      .filter(([key]) => key !== "overall")
                      .map(([key, value]) => (
                        <div key={key} className="p-3 rounded-xl bg-background/50">
                          <p className="text-xs text-gray-500 mb-1 capitalize">{key}</p>
                          <div className="flex items-center gap-2">
                            <Progress value={value} className="flex-1 h-2" />
                            <span className={`text-sm font-medium ${getScoreColor(value)}`}>
                              {Math.round(value)}
                            </span>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Skills Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success" />
                    Matched Skills
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {analysis.matched_skills?.map((skill) => (
                      <Badge key={skill} variant="success">{skill}</Badge>
                    ))}
                    {(!analysis.matched_skills || analysis.matched_skills.length === 0) && (
                      <p className="text-sm text-gray-500">No matched skills</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-danger" />
                    Missing Skills
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {analysis.missing_skills?.map((skill) => (
                      <Badge key={skill} variant="danger">{skill}</Badge>
                    ))}
                    {(!analysis.missing_skills || analysis.missing_skills.length === 0) && (
                      <p className="text-sm text-gray-500">No missing skills</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-warning" />
                    Partial Match
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {analysis.partial_skills?.map((skill) => (
                      <Badge key={skill} variant="warning">{skill}</Badge>
                    ))}
                    {(!analysis.partial_skills || analysis.partial_skills.length === 0) && (
                      <p className="text-sm text-gray-500">No partial matches</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Suggestions */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary-light" />
                  Suggestions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analysis.suggestions?.map((suggestion, i) => (
                    <div
                      key={i}
                      className="p-4 rounded-xl bg-background/50 border border-gray-800 hover:border-primary/30 transition-all"
                    >
                      <div className="flex items-start gap-3">
                        <Badge
                          variant={
                            suggestion.severity === "high"
                              ? "danger"
                              : suggestion.severity === "medium"
                              ? "warning"
                              : "secondary"
                          }
                        >
                          {suggestion.severity}
                        </Badge>
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-gray-200 mb-1">
                            {suggestion.title}
                          </h4>
                          <p className="text-xs text-gray-400">{suggestion.description}</p>
                        </div>
                        <Badge variant="outline">{suggestion.category}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Job Match */}
            {analysis.job_match && analysis.job_match.recommended_roles?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-primary-light" />
                    Job Match Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-400 mb-4">
                    Similarity Score:{" "}
                    <span className="text-primary-light font-semibold">
                      {analysis.job_match.similarity_score}%
                    </span>
                  </p>
                  <div className="space-y-3">
                    {analysis.job_match.recommended_roles.map((role) => (
                      <div
                        key={role.title}
                        className="flex items-center justify-between p-3 rounded-xl bg-background/50"
                      >
                        <span className="text-sm font-medium text-gray-200">{role.title}</span>
                        <div className="flex items-center gap-3">
                          <Progress value={role.match} className="w-24 h-2" />
                          <span className={`text-sm font-medium ${getScoreColor(role.match)}`}>
                            {role.match}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={reset}>
                Analyze Another Resume
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
