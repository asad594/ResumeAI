import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Simple rendering logic extracted from Analyze.tsx to test rendering correctness
function CategoryBreakdown({ analysis, expandedCategory, setExpandedCategory }: any) {
  const expectedCategories = [
    'formatting',
    'contact_information',
    'skills',
    'experience',
    'keywords',
    'action_verbs',
    'grammar',
    'metrics'
  ];

  return (
    <div className="flex-1 w-full space-y-3">
      {expectedCategories.map((k) => {
        let rawVal = analysis.breakdown ? analysis.breakdown[k] : undefined;

        // Validate raw score
        if (rawVal === null || rawVal === undefined || isNaN(rawVal) || typeof rawVal !== 'number') {
          console.error(`Invalid score for category ${k}:`, rawVal);
          rawVal = 0;
        }

        const score = Math.round(rawVal);
        let badgeText = "Needs Improvement";
        let badgeColor = "bg-[#EF4444]/20 text-[#EF4444] border-[#EF4444]/30";
        let progressColor = "bg-[#EF4444]";

        if (score >= 90) {
          badgeText = "Excellent";
          badgeColor = "bg-[#22C55E]/20 text-[#22C55E] border-[#22C55E]/30";
          progressColor = "bg-[#22C55E]";
        } else if (score >= 75) {
          badgeText = "Good";
          badgeColor = "bg-[#3B82F6]/20 text-[#60A5FA] border-[#3B82F6]/30";
          progressColor = "bg-[#3B82F6]";
        } else if (score >= 50) {
          badgeText = "Average";
          badgeColor = "bg-[#EAB308]/20 text-[#EAB308] border-[#EAB308]/30";
          progressColor = "bg-[#EAB308]";
        }

        const isExpanded = expandedCategory === k;

        return (
          <div key={k} data-testid={`category-card-${k}`} className="p-4 rounded-xl bg-[#0F172A]/40 border border-gray-800 hover:border-gray-700/50 transition-all space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-gray-200 capitalize">{k.replace(/_/g, ' ')}</span>
                <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${badgeColor}`}>{badgeText}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-bold text-gray-300">{score}/100</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

describe('ATS Score Breakdown UI Component', () => {
  it('renders exactly eight categories and handles missing/invalid scores', () => {
    // Mock analysis data containing some missing keys, invalid keys (NaN), and metadata fields in the breakdown dictionary
    const mockAnalysis = {
      overall_score: 82.0,
      breakdown: {
        formatting: 90.0,
        contact_information: 100.0,
        skills: NaN, // Invalid number
        experience: null, // Null value
        keywords: undefined, // Undefined value
        action_verbs: 95.0,
        grammar: 98.0,
        // metrics is missing completely from the breakdown
        overall_score: 82.0, // Metadata field in breakdown
        breakdown: {}, // Metadata field in breakdown
        category_suggestions: [] // Metadata field in breakdown
      } as any,
      category_suggestions: []
    };

    const spyConsoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<CategoryBreakdown analysis={mockAnalysis} expandedCategory={null} setExpandedCategory={() => {}} />);

    // Assert that the exact 8 cards are rendered
    const expectedKeys = [
      'formatting',
      'contact_information',
      'skills',
      'experience',
      'keywords',
      'action_verbs',
      'grammar',
      'metrics'
    ];

    expectedKeys.forEach((key) => {
      const card = screen.getByTestId(`category-card-${key}`);
      expect(card).toBeInTheDocument();
    });

    // Verify metadata keys are not rendered
    const metadataKeys = ['overall_score', 'breakdown', 'category_suggestions'];
    metadataKeys.forEach((key) => {
      const card = screen.queryByTestId(`category-card-${key}`);
      expect(card).not.toBeInTheDocument();
    });

    // Check invalid/missing categories defaulted to 0
    expect(screen.getByText('formatting').nextSibling).toHaveTextContent('Excellent');
    expect(screen.getByTestId('category-card-skills')).toHaveTextContent('0/100');
    expect(screen.getByTestId('category-card-experience')).toHaveTextContent('0/100');
    expect(screen.getByTestId('category-card-keywords')).toHaveTextContent('0/100');
    expect(screen.getByTestId('category-card-metrics')).toHaveTextContent('0/100');

    // Confirm that console.error was called for the invalid values
    expect(spyConsoleError).toHaveBeenCalled();
    spyConsoleError.mockRestore();
  });
});
