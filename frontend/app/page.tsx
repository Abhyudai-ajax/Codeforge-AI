'use client';

import React from 'react';
import { useAppStore } from '@/store/useAppStore';
import { Navbar } from '@/components/layout/Navbar';
import { VSCodeWorkbench } from '@/components/vscode/VSCodeWorkbench';
import { LeetCodeHub } from '@/components/leetcode/LeetCodeHub';
import { GitHubPRReview } from '@/components/github/GitHubPRReview';
import { UserProfileView } from '@/components/profile/UserProfileView';
import { AICopilotDrawer } from '@/components/ai/AICopilotDrawer';

export default function Home() {
  const { activeView } = useAppStore();

  return (
    <main className="min-h-screen bg-[#0B0F17] flex flex-col font-sans overflow-hidden">
      {/* Top Navbar Header */}
      <Navbar />

      {/* Dynamic View & Sidebar Container */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Main Active View */}
        <div className="flex-1 flex overflow-hidden">
          {activeView === 'vscode' && <VSCodeWorkbench />}
          {activeView === 'leetcode' && <LeetCodeHub />}
          {activeView === 'github' && <GitHubPRReview />}
          {activeView === 'profile' && <UserProfileView />}
        </div>

        {/* AI Copilot Drawer */}
        <AICopilotDrawer />
      </div>
    </main>
  );
}
