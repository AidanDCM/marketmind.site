# MarketMind Command Center - Enhanced Monitoring & AI Decision Tracking

## Overview

The MarketMind Command Center is a comprehensive real-time monitoring dashboard that provides complete visibility into system operations, AI decision-making, and business performance. This enhanced version includes interactive visualizations, real-time alerts, and detailed AI reasoning transparency.

## Features

### 🎯 Real-time System Monitoring
- **Auto-refresh every 30 seconds** using SWR for efficient data fetching
- **Live system health status** with color-coded indicators
- **Performance KPIs** with trend visualization
- **API endpoint monitoring** with response time tracking

### 📊 Interactive Charts & Visualizations
- **Time-series charts** for profit margins, order volume, and AI confidence
- **Sparklines** for quick trend visualization in model performance
- **Donut charts** for model performance distribution
- **Real-time data updates** with smooth animations

### 🧠 AI Decision Making & Reasoning
- **Recent AI decisions** with detailed reasoning explanations
- **Confidence scores** and decision factors
- **Reasoning patterns** with accuracy metrics
- **Current AI focus areas** and system logic transparency

### 🚨 System Alerts & Notifications
- **Real-time alerts** with severity levels (low, medium, high, critical)
- **Alert acknowledgment** and dismissal functionality
- **Alert history** with timestamps and sources
- **Color-coded alert types** (error, warning, info, success)

### 🔐 Platform Integration Monitoring
- **Credential status** for all integrated platforms
- **API call tracking** with success/failure rates
- **Real-time usage statistics** for Amazon SP-API, CJ, Google Sheets, eBay

### 🧠 Machine Learning Insights
- **Model performance tracking** with accuracy trends
- **Training status** and deployment rollouts
- **Performance distribution** across model portfolio
- **Historical metrics** and improvement tracking

## API Endpoints

### AI Decision Tracking
```
GET /ai/decisions?limit=10&offset=0
GET /ai/reasoning?limit=8&offset=0
GET /ai/insights?limit=5
GET /ai/health
```

### System Monitoring
```
GET /health/summary
GET /dash/kpis
GET /profit/kpis
GET /profit/log?limit=10
```

### Learning System
```
GET /learning/models?limit=10
GET /learning/metrics?limit=10
GET /learning/rollouts?limit=10
```

## Usage Guide

### Accessing the Command Center
1. Navigate to `http://localhost:3000/command-center` (development)
2. Or visit the deployed version at your GitHub Pages URL
3. Ensure API server is running on `http://127.0.0.1:8001`

### Understanding the Dashboard

#### Key Performance Indicators (KPIs)
- **Publish Success %**: Percentage of successful product listings
- **VTR/ODR**: View-through rate and order defect rate
- **Recon %**: Reconciliation success rate
- **Models**: Number of active ML models

#### Real-time Metrics Charts
- **Profit Margin Trend**: 24-hour profit margin visualization
- **Order Volume**: Real-time order processing metrics
- **AI Decision Confidence**: Average confidence of AI decisions

#### AI Reasoning Section
- **Recent AI Decisions**: Latest automated decisions with full reasoning
- **Reasoning Patterns**: Active AI logic patterns and their accuracy
- **Current Focus**: What the AI is currently optimizing for

#### System Alerts
- **Unread Alerts**: New system notifications requiring attention
- **Alert Types**: Error (🚨), Warning (⚠️), Info (ℹ️), Success (✅)
- **Severity Levels**: Critical, High, Medium, Low

### Operator Actions
- **Promote to Canary**: Deploy models to canary environment
- **Train Historical**: Trigger historical data training
- **RBAC Token Required**: Secure actions require valid authentication

## Configuration

### Environment Variables
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001
NEXT_PUBLIC_API_TOKEN=your_rbac_token

# GitHub Pages Deployment
NEXT_PUBLIC_BASEPATH=/MarketMind
```

### Auto-refresh Settings
The dashboard automatically refreshes data every 30 seconds. This can be customized by modifying the interval in the `useEffect` hook:

```typescript
React.useEffect(() => {
  const interval = setInterval(async () => {
    // Refresh all endpoints
  }, 30000); // 30 seconds
  return () => clearInterval(interval);
}, []);
```

## Development

### Running Locally
```bash
# Start API server
make api-live

# Start console development server
make console-dev

# Or manually:
cd apps/console
npm run dev
```

### Building for Production
```bash
cd apps/console
npm run build
npm run export  # For static deployment
```

### Adding New Charts
1. Create chart component in `components/charts/`
2. Import in Command Center page
3. Add data fetching with SWR
4. Include in auto-refresh cycle

### Adding New Alerts
1. Extend Alert interface in `components/alerts/SystemAlerts.tsx`
2. Add alert generation logic in backend
3. Update alert display components
4. Test acknowledgment and dismissal flows

## Deployment

### GitHub Pages
The Command Center is automatically deployed to GitHub Pages via GitHub Actions:

1. Push to main branch triggers deployment
2. Next.js app is built with static export
3. Deployed to `https://yourusername.github.io/MarketMind`

### Manual Deployment
```bash
# Build static export
cd apps/console
npm run build
npm run export

# Deploy to your hosting provider
# Upload contents of `out/` directory
```

## Troubleshooting

### Common Issues

#### API Connection Errors
- Verify API server is running on correct port
- Check CORS configuration in API settings
- Ensure RBAC tokens are valid

#### Chart Display Issues
- Check browser console for JavaScript errors
- Verify data format matches chart expectations
- Ensure SVG rendering is supported

#### Auto-refresh Not Working
- Check network connectivity
- Verify SWR configuration
- Look for JavaScript errors in console

#### Alerts Not Displaying
- Check alert data format
- Verify component imports
- Test with mock data first

### Performance Optimization
- Use React.memo for expensive components
- Implement virtualization for large data sets
- Optimize chart rendering with canvas if needed
- Cache API responses appropriately

## Security Considerations

### RBAC Token Management
- Store tokens securely (environment variables)
- Implement token refresh logic
- Use HTTPS in production
- Validate tokens on backend

### Data Privacy
- Sanitize sensitive data in logs
- Implement proper access controls
- Audit trail for operator actions
- Secure API endpoints

## Future Enhancements

### Planned Features
- **Real-time WebSocket connections** for instant updates
- **Custom dashboard layouts** with drag-and-drop
- **Advanced filtering** and search capabilities
- **Export functionality** for reports and data
- **Mobile-responsive design** improvements
- **Dark mode** theme option

### Integration Opportunities
- **Slack/Teams notifications** for critical alerts
- **Email reports** for daily/weekly summaries
- **Third-party monitoring** tools integration
- **Custom webhook** support for external systems

## Support

For issues, feature requests, or questions:
1. Check this documentation first
2. Review the codebase and comments
3. Test with mock data to isolate issues
4. Check browser developer tools for errors

## Changelog

### v2.0.0 - Enhanced Command Center
- ✅ Added interactive charts and visualizations
- ✅ Implemented AI decision tracking and reasoning
- ✅ Created comprehensive alert system
- ✅ Enhanced real-time monitoring capabilities
- ✅ Improved visual design and user experience
- ✅ Added deployment automation

### v1.0.0 - Initial Command Center
- Basic KPI display
- System health monitoring
- Simple data tables
- Manual refresh functionality
