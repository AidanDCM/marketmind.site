"use client";

import React from 'react';

interface Alert {
  id: string;
  type: 'error' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: string;
  source?: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
  acknowledged?: boolean;
}

interface SystemAlertsProps {
  alerts?: Alert[];
  onAcknowledge?: (alertId: string) => void;
  onDismiss?: (alertId: string) => void;
}

export function SystemAlerts({ alerts = [], onAcknowledge, onDismiss }: SystemAlertsProps) {
  // Mock alerts for demonstration
  const mockAlerts: Alert[] = [
    {
      id: '1',
      type: 'warning',
      title: 'High API Error Rate',
      message: 'Amazon SP-API error rate increased to 8.2% in the last hour. Investigating connection issues.',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      source: 'Amazon SP-API',
      severity: 'medium',
      acknowledged: false
    },
    {
      id: '2',
      type: 'info',
      title: 'Model Retrain Complete',
      message: 'Pricing model v3.2 training completed successfully. Accuracy improved by 2.3%.',
      timestamp: new Date(Date.now() - 900000).toISOString(),
      source: 'Learning System',
      severity: 'low',
      acknowledged: true
    },
    {
      id: '3',
      type: 'error',
      title: 'Inventory Sync Failed',
      message: 'Failed to sync inventory levels for 12 products. Manual intervention required.',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
      source: 'Inventory System',
      severity: 'high',
      acknowledged: false
    },
    {
      id: '4',
      type: 'success',
      title: 'Performance Milestone',
      message: 'System achieved 99.2% uptime this month, exceeding SLA targets.',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      source: 'System Monitor',
      severity: 'low',
      acknowledged: false
    }
  ];

  const displayAlerts = alerts.length > 0 ? alerts : mockAlerts;
  const unacknowledgedAlerts = displayAlerts.filter(alert => !alert.acknowledged);

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'error': return '🚨';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      case 'success': return '✅';
      default: return '📢';
    }
  };

  const getAlertColor = (type: Alert['type']) => {
    switch (type) {
      case 'error': return 'border-red-200 bg-red-50';
      case 'warning': return 'border-yellow-200 bg-yellow-50';
      case 'info': return 'border-blue-200 bg-blue-50';
      case 'success': return 'border-green-200 bg-green-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const getSeverityColor = (severity?: Alert['severity']) => {
    switch (severity) {
      case 'critical': return 'bg-red-600 text-white';
      case 'high': return 'bg-red-500 text-white';
      case 'medium': return 'bg-yellow-500 text-white';
      case 'low': return 'bg-blue-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-4">
      {/* Alert Summary */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="font-medium text-gray-900">System Alerts</h3>
          {unacknowledgedAlerts.length > 0 && (
            <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-medium rounded-full">
              {unacknowledgedAlerts.length} unread
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span>Last updated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {displayAlerts.length > 0 ? (
          displayAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-4 rounded-lg border ${getAlertColor(alert.type)} ${
                alert.acknowledged ? 'opacity-60' : ''
              } transition-all hover:shadow-sm`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <div className="text-lg">{getAlertIcon(alert.type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-gray-900">{alert.title}</h4>
                      {alert.severity && (
                        <span className={`px-2 py-0.5 text-xs font-medium rounded ${getSeverityColor(alert.severity)}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{alert.message}</p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>{formatTime(alert.timestamp)}</span>
                      {alert.source && <span>Source: {alert.source}</span>}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 ml-4">
                  {!alert.acknowledged && onAcknowledge && (
                    <button
                      onClick={() => onAcknowledge(alert.id)}
                      className="px-3 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                    >
                      Acknowledge
                    </button>
                  )}
                  {onDismiss && (
                    <button
                      onClick={() => onDismiss(alert.id)}
                      className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">🔔</div>
            <p className="text-sm">No alerts at this time</p>
          </div>
        )}
      </div>
    </div>
  );
}

interface AlertBannerProps {
  alert: Alert;
  onDismiss?: () => void;
}

export function AlertBanner({ alert, onDismiss }: AlertBannerProps) {
  const getBannerColor = (type: Alert['type']) => {
    switch (type) {
      case 'error': return 'bg-red-600 text-white';
      case 'warning': return 'bg-yellow-600 text-white';
      case 'info': return 'bg-blue-600 text-white';
      case 'success': return 'bg-green-600 text-white';
      default: return 'bg-gray-600 text-white';
    }
  };

  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'error': return '🚨';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      case 'success': return '✅';
      default: return '📢';
    }
  };

  return (
    <div className={`${getBannerColor(alert.type)} px-4 py-3 rounded-lg shadow-sm`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-lg">{getAlertIcon(alert.type)}</span>
          <div>
            <div className="font-medium">{alert.title}</div>
            <div className="text-sm opacity-90">{alert.message}</div>
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="p-1 hover:bg-black hover:bg-opacity-10 rounded transition-colors"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}

interface NotificationToastProps {
  notifications: Alert[];
  onDismiss?: (id: string) => void;
}

export function NotificationToast({ notifications, onDismiss }: NotificationToastProps) {
  const getAlertIcon = (type: Alert['type']) => {
    switch (type) {
      case 'error': return '🚨';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      case 'success': return '✅';
      default: return '📢';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 animate-slide-in"
        >
          <div className="flex items-start gap-3">
            <span className="text-lg">{getAlertIcon(notification.type)}</span>
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-gray-900 text-sm">{notification.title}</h4>
              <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
            </div>
            {onDismiss && (
              <button
                onClick={() => onDismiss(notification.id)}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
