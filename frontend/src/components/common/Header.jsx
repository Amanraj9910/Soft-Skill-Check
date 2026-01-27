// Header component with navigation - Professional Assessment Theme
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import Button from './Button';

const Header = () => {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const { isAuthenticated, user, signOut } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();

    const handleSignOut = async () => {
        await signOut();
        navigate('/');
        setMobileMenuOpen(false);
    };

    const NavLink = ({ to, children }) => {
        const isActive = location.pathname === to;
        return (
            <Link
                to={to}
                className={`px-4 py-2 text-sm font-semibold transition-colors duration-200 ${isActive
                    ? 'text-red-600'
                    : 'text-slate-600 hover:text-slate-900'
                    }`}
                onClick={() => setMobileMenuOpen(false)}
            >
                {children}
            </Link>
        );
    };

    return (
        <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-slate-200">
            <div className="container mx-auto px-6">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-3 group">
                        <div className="w-8 h-8 rounded bg-red-600 flex items-center justify-center shadow-sm group-hover:bg-red-700 transition-colors">
                            <img src="../img/favicon.ico.png" alt="" />
                        </div>
                        <div className="flex flex-col">
                            <span className="font-bold text-lg text-slate-900 tracking-tight leading-none">
                                Hosho Digital
                            </span>
                        </div>
                    </Link>

                    {/* Desktop Navigation */}
                    <nav className="hidden md:flex items-center gap-6">
                        {isAuthenticated ? (
                            <>
                                <NavLink to="/dashboard">Dashboard</NavLink>
                                <NavLink to="/assessment">Start New Assessment</NavLink>
                            </>
                        ) : (
                            <>
                                <NavLink to="/">Platform</NavLink>
                                <NavLink to="/login">Sign In</NavLink>
                            </>
                        )}
                    </nav>

                    {/* Right side actions */}
                    <div className="flex items-center gap-4">
                        {/* Desktop auth buttons */}
                        {isAuthenticated ? (
                            <div className="hidden md:flex items-center gap-6">
                                <div className="flex items-center gap-3">
                                    <div className="flex flex-col items-end">
                                        <span className="text-xs font-semibold text-slate-900 leading-none">
                                            {user?.email}
                                        </span>
                                        <span className="text-[10px] text-slate-500 uppercase tracking-wider">Candidate</span>
                                    </div>
                                    <div className="w-8 h-8 rounded bg-slate-100 flex items-center justify-center text-slate-700 text-xs font-bold border border-slate-200">
                                        {user?.email?.charAt(0).toUpperCase() || 'U'}
                                    </div>
                                </div>
                                <div className="h-6 w-px bg-slate-200"></div>
                                <button
                                    onClick={handleSignOut}
                                    className="text-sm font-medium text-slate-500 hover:text-red-600 transition-colors"
                                >
                                    Sign out
                                </button>
                            </div>
                        ) : (
                            <div className="hidden md:block">
                                <Button onClick={() => navigate('/signup')} size="sm" className="bg-slate-900 text-white hover:bg-black">
                                    Get Started
                                </Button>
                            </div>
                        )}

                        {/* Mobile menu button */}
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="md:hidden p-2 text-slate-600 hover:text-slate-900"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Mobile menu */}
                <AnimatePresence>
                    {mobileMenuOpen && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="md:hidden border-t border-slate-200 bg-white"
                        >
                            <nav className="py-4 flex flex-col px-2">
                                {isAuthenticated ? (
                                    <>
                                        <Link to="/dashboard" className="px-4 py-3 hover:bg-slate-50 rounded-lg text-slate-700 font-medium" onClick={() => setMobileMenuOpen(false)}>Dashboard</Link>
                                        <Link to="/assessment" className="px-4 py-3 hover:bg-slate-50 rounded-lg text-slate-700 font-medium" onClick={() => setMobileMenuOpen(false)}>New Assessment</Link>
                                        <div className="border-t border-slate-100 my-2"></div>
                                        <button
                                            onClick={handleSignOut}
                                            className="w-full text-left px-4 py-3 text-red-600 font-medium hover:bg-red-50 rounded-lg"
                                        >
                                            Sign out
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <Link to="/" className="px-4 py-3 hover:bg-slate-50 rounded-lg text-slate-700 font-medium" onClick={() => setMobileMenuOpen(false)}>Home</Link>
                                        <Link to="/login" className="px-4 py-3 hover:bg-slate-50 rounded-lg text-slate-700 font-medium" onClick={() => setMobileMenuOpen(false)}>Login</Link>
                                        <Link to="/signup" className="px-4 py-3 hover:bg-slate-50 rounded-lg text-slate-700 font-medium" onClick={() => setMobileMenuOpen(false)}>Sign Up</Link>
                                    </>
                                )}
                            </nav>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </header>
    );
};

export default Header;
