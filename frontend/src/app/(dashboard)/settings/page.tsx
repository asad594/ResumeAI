"use client";

import React from "react";
import { motion } from "framer-motion";
import { Moon, Sun, Bell, Shield, Trash2, Monitor } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "@/context/ThemeContext";

export default function SettingsPage() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-gray-100 mb-1">Settings</h1>
        <p className="text-gray-400 text-sm">Customize your application preferences</p>
      </motion.div>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="w-5 h-5 text-primary-light" />
            Appearance
          </CardTitle>
          <CardDescription>Customize the look and feel</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-xl bg-background/50">
            <div className="flex items-center gap-3">
              {theme === "dark" ? (
                <Moon className="w-5 h-5 text-primary-light" />
              ) : (
                <Sun className="w-5 h-5 text-warning" />
              )}
              <div>
                <p className="text-sm font-medium text-gray-200">Dark Mode</p>
                <p className="text-xs text-gray-500">Toggle between dark and light themes</p>
              </div>
            </div>
            <button
              onClick={toggleTheme}
              className={`relative w-12 h-6 rounded-full transition-colors duration-200 cursor-pointer ${
                theme === "dark" ? "bg-primary" : "bg-gray-600"
              }`}
            >
              <div
                className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform duration-200 ${
                  theme === "dark" ? "translate-x-6" : "translate-x-0.5"
                }`}
              />
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-primary-light" />
            Notifications
          </CardTitle>
          <CardDescription>Manage notification preferences</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            { label: "Email notifications", desc: "Receive analysis results via email" },
            { label: "Analysis completion", desc: "Get notified when analysis is done" },
            { label: "Weekly digest", desc: "Summary of your activity" },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between p-4 rounded-xl bg-background/50">
              <div>
                <p className="text-sm font-medium text-gray-200">{item.label}</p>
                <p className="text-xs text-gray-500">{item.desc}</p>
              </div>
              <button className="relative w-12 h-6 rounded-full bg-primary transition-colors cursor-pointer">
                <div className="absolute top-0.5 left-6 w-5 h-5 rounded-full bg-white transition-transform" />
              </button>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-primary-light" />
            Security
          </CardTitle>
          <CardDescription>Manage your security settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 rounded-xl bg-background/50">
            <div>
              <p className="text-sm font-medium text-gray-200">Two-Factor Authentication</p>
              <p className="text-xs text-gray-500">Add an extra layer of security</p>
            </div>
            <Badge variant="secondary">Coming Soon</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-danger/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-danger">
            <Trash2 className="w-5 h-5" />
            Danger Zone
          </CardTitle>
          <CardDescription>Irreversible actions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 rounded-xl bg-danger/5 border border-danger/20">
            <div>
              <p className="text-sm font-medium text-gray-200">Delete Account</p>
              <p className="text-xs text-gray-500">Permanently delete your account and all data</p>
            </div>
            <Button variant="destructive" size="sm">
              Delete Account
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
