import { useState } from 'react';
import { Layout } from './components/Layout';
import { PredictionForm } from './components/PredictionForm';
import { ComingSoon } from './components/ComingSoon';

type Tab = 'predict' | 'batch' | 'history' | 'stats';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('predict');

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'predict' && <PredictionForm />}
      {activeTab === 'batch' && (
        <ComingSoon
          title="Batch Processing"
          description="Submit multiple predictions at once. Upload a list of questions and receive probability forecasts for all of them."
        />
      )}
      {activeTab === 'history' && (
        <ComingSoon
          title="Prediction History"
          description="View your past predictions and their outcomes. Track your prediction accuracy over time."
        />
      )}
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
