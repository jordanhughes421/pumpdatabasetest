import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import PumpList from './pages/PumpList';
import PumpCreate from './pages/PumpCreate';
import PumpDetail from './pages/PumpDetail';
import CurveSetDetail from './pages/CurveSetDetail';
import Compare from './pages/Compare';
import Login from './pages/Login';
import Admin from './pages/Admin';
import InviteRedeem from './pages/InviteRedeem';
import { AuthProvider, useAuth } from './context/AuthContext';

const queryClient = new QueryClient();

// Protected Route Wrapper
const ProtectedRoute = ({ children, requireAdmin = false }: { children: JSX.Element, requireAdmin?: boolean }) => {
    const { user, role, isLoading } = useAuth();
    const location = useLocation();

    if (isLoading) return <div>Loading...</div>;

    if (!user) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    if (requireAdmin && role !== 'admin') {
        return <div>Access Denied</div>;
    }

    return children;
};

const Navbar = () => {
    const { user, activeOrg, role, logout } = useAuth();

    if (!user) return null;

    return (
        <nav className="bg-white shadow p-4 mb-4">
            <div className="container mx-auto flex justify-between items-center">
               <div className="flex items-center gap-6">
                   <Link to="/" className="text-xl font-bold text-blue-600">PumpCurve Manager</Link>
                   <Link to="/" className="text-gray-600 hover:text-blue-600">Library</Link>
                   <Link to="/compare" className="text-gray-600 hover:text-blue-600">Compare</Link>
                   {role === 'admin' && (
                       <Link to="/admin" className="text-gray-600 hover:text-blue-600 font-medium">Admin</Link>
                   )}
               </div>
               <div className="flex items-center gap-4">
                   {activeOrg && (
                       <span className="text-sm px-2 py-1 bg-gray-100 rounded border">
                           {activeOrg.name} ({role})
                       </span>
                   )}
                   <span className="text-sm text-gray-500">{user.email}</span>
                   <button onClick={logout} className="text-sm text-red-600 hover:text-red-800">Logout</button>
               </div>
            </div>
        </nav>
    );
};

function App() {
  return (
    <AuthProvider>
        <QueryClientProvider client={queryClient}>
        <Router>
            <div className="min-h-screen bg-gray-100 text-gray-900 font-sans flex flex-col">
            <Navbar />
            <div className="flex-1">
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/invite/:token" element={<InviteRedeem />} />

                    <Route path="/" element={<ProtectedRoute><PumpList /></ProtectedRoute>} />
                    <Route path="/pumps/new" element={<ProtectedRoute><PumpCreate /></ProtectedRoute>} />
                    <Route path="/pumps/:id" element={<ProtectedRoute><PumpDetail /></ProtectedRoute>} />
                    <Route path="/curve-sets/:id" element={<ProtectedRoute><CurveSetDetail /></ProtectedRoute>} />
                    <Route path="/compare" element={<ProtectedRoute><Compare /></ProtectedRoute>} />
                    <Route path="/admin" element={<ProtectedRoute requireAdmin={true}><Admin /></ProtectedRoute>} />
                </Routes>
            </div>
            </div>
        </Router>
        </QueryClientProvider>
    </AuthProvider>
  );
}

export default App;
