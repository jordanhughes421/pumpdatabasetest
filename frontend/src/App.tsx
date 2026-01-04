import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import PumpList from './pages/PumpList';
import PumpCreate from './pages/PumpCreate';
import PumpDetail from './pages/PumpDetail';
import CurveSetDetail from './pages/CurveSetDetail';
import Compare from './pages/Compare';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-100 text-gray-900 font-sans flex flex-col">
          <nav className="bg-white shadow p-4 mb-4">
            <div className="container mx-auto flex justify-between items-center">
               <div className="flex items-center gap-6">
                   <Link to="/" className="text-xl font-bold text-blue-600">PumpCurve Manager</Link>
                   <Link to="/" className="text-gray-600 hover:text-blue-600">Library</Link>
                   <Link to="/compare" className="text-gray-600 hover:text-blue-600">Compare</Link>
               </div>
            </div>
          </nav>
          <div className="flex-1">
            <Routes>
                <Route path="/" element={<PumpList />} />
                <Route path="/pumps/new" element={<PumpCreate />} />
                <Route path="/pumps/:id" element={<PumpDetail />} />
                <Route path="/curve-sets/:id" element={<CurveSetDetail />} />
                <Route path="/compare" element={<Compare />} />
            </Routes>
          </div>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
