'use client';

import { useEffect, useState } from 'react';
import { dashboard } from '@/lib/api';
import DemoBadge from '@/components/DemoBadge';
import Link from 'next/link';

export default function DashboardOverview() {
  const [billsAnalysis, setBillsAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const analysis = await dashboard.getBillsAnalysis();
      setBillsAnalysis(analysis);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  const variance = billsAnalysis?.variance;
  const anomalies = billsAnalysis?.anomalies;
  const forecast = billsAnalysis?.forecast;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">Welcome to your water services dashboard</p>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Current Bill</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                ₹{variance?.current || 'N/A'}
              </p>
            </div>
            <DemoBadge />
          </div>
          {variance && (
            <p className="mt-2 text-sm text-gray-600">
              {variance.increase ? 'Increased' : 'Decreased'} by ₹{variance.difference} ({variance.percent_change}%)
            </p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Anomalies</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                {anomalies?.count || 0}
              </p>
            </div>
            <DemoBadge />
          </div>
          {anomalies?.count > 0 && (
            <p className="mt-2 text-sm text-amber-600">
              {anomalies.count} possible anomaly(s) detected
            </p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Next Bill Forecast</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">
                ₹{forecast?.forecast || 'N/A'}
              </p>
            </div>
            <DemoBadge />
          </div>
          {forecast && forecast.range && (
            <p className="mt-2 text-sm text-gray-600">
              Range: ₹{forecast.range.min} - ₹{forecast.range.max}
            </p>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            href="/dashboard/assistant"
            className="block p-4 border border-gray-200 rounded-lg hover:border-cyan-500 hover:bg-cyan-50 transition-colors"
          >
            <p className="font-medium text-gray-900">Ask Assistant</p>
            <p className="text-sm text-gray-500 mt-1">Chat or voice help</p>
          </Link>

          <Link
            href="/dashboard/bills"
            className="block p-4 border border-gray-200 rounded-lg hover:border-cyan-500 hover:bg-cyan-50 transition-colors"
          >
            <p className="font-medium text-gray-900">View Bills</p>
            <p className="text-sm text-gray-500 mt-1">Billing history</p>
          </Link>

          <Link
            href="/dashboard/tanker"
            className="block p-4 border border-gray-200 rounded-lg hover:border-cyan-500 hover:bg-cyan-50 transition-colors"
          >
            <p className="font-medium text-gray-900">Book Tanker</p>
            <p className="text-sm text-gray-500 mt-1">Request water tanker</p>
          </Link>

          <Link
            href="/dashboard/grievances"
            className="block p-4 border border-gray-200 rounded-lg hover:border-cyan-500 hover:bg-cyan-50 transition-colors"
          >
            <p className="font-medium text-gray-900">File Grievance</p>
            <p className="text-sm text-gray-500 mt-1">Report an issue</p>
          </Link>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> This is an unofficial demo service. For official HMWSSB services, please visit{' '}
          <a href="https://www.hmwssb.gov.in" target="_blank" rel="noopener noreferrer" className="underline">
            hmwssb.gov.in
          </a>
        </p>
      </div>
    </div>
  );
}
