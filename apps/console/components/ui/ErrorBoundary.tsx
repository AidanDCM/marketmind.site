"use client";

import React from "react";

type State = { hasError: boolean; error?: any; info?: any };

export default class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  constructor(props: any){
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: any){
    return { hasError: true, error };
  }

  componentDidCatch(error: any, info: any){
    // In production, this can be wired to Sentry/OTel as needed
    if (typeof console !== 'undefined') console.error('ErrorBoundary caught:', error, info);
    this.setState({ info });
  }

  handleReload = () => { if (typeof window !== 'undefined') window.location.reload(); };

  render(){
    if (this.state.hasError){
      return (
        <div className="mm-card p-6">
          <h2 className="text-lg font-semibold mb-2">Something went wrong</h2>
          <p className="text-sm text-gray-600">An unexpected error occurred. You can try reloading the page. If this persists, contact support.</p>
          <div className="mt-3 flex items-center gap-2">
            <button className="mm-btn primary" onClick={this.handleReload}>Reload</button>
            {this.state.error && (
              <details className="text-xs bg-gray-50 p-3 rounded border">
                <summary className="cursor-pointer">Show technical details</summary>
                <pre className="overflow-auto">{String(this.state.error?.stack || this.state.error)}</pre>
              </details>
            )}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
