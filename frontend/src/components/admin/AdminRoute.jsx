import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import LoadingSpinner from '../common/LoadingSpinner';

const AdminRoute = ({ children }) => {
    const { user, loading, isAuthenticated } = useAuth();

    if (loading) {
        return <LoadingSpinner fullScreen text="Verifying access..." />;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    // TODO: Implement proper role check when backend supports it
    // For now, we assume if you are authenticated and trying to access /admin, you are authorized
    // OR we can check specific email whitelist
    // const isAdmin = user?.email?.endsWith('@admin.com') || user?.app_metadata?.role === 'admin';
    // if (!isAdmin) {
    //     return <Navigate to="/dashboard" replace />;
    // }

    return children;
};

export default AdminRoute;
