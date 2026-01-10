import { useState } from 'react';
import { Layout } from './components/Layout';
import { PredictionForm } from './components/PredictionForm';
import { ComingSoon } from './components/ComingSoon';
import { History } from './components/History';
import { PredictionDetail } from './components/PredictionDetail';
import { SharedPrediction } from './components/SharedPrediction';
import type { Tab } from './types/app';

function getSharedPredictionId(): string | null {
  const match = window.location.pathname.match(/^\/predictions\/([a-f0-9-]+)$/i);
  return match ? match[1] : null;
}

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('predict');
  const [detailId, setDetailId] = useState<string | null>(null);

  // Public shareable view - standalone, no app chrome
  const sharedId = getSharedPredictionId();
  if (sharedId) {
    return <SharedPrediction requestId={sharedId} />;
  }

  // Internal detail view from history
  if (detailId) {
    return (
      <Layout activeTab={activeTab} onTabChange={setActiveTab}>
        <PredictionDetail
          requestId={detailId}
          onBack={() => setDetailId(null)}
        />
      </Layout>
    );
  }

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'predict' && <PredictionForm />}
      {activeTab === 'batch' && (
        <ComingSoon
          title="Batch Processing"
          description="Submit multiple predictions at once. Upload a list of questions and receive probability forecasts for all of them."
        />
      )}
      {activeTab === 'history' && <History onSelectPrediction={setDetailId} />}
      {activeTab === 'stats' && (
        <ComingSoon
          title="Statistics"
          description="Analyze prediction patterns, agent performance, and overall accuracy metrics."
        />
      )}
    </Layout>
  );
}

export default App;
