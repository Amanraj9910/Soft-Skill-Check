// Header component with navigation - Interview Theme
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import Button from './Button';

const Header = () => {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const { isAuthenticated, user, signOut } = useAuth();
    const { isDark, toggleTheme } = useTheme();
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
                className={`px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${isActive
                    ? 'text-red-600 bg-red-50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                onClick={() => setMobileMenuOpen(false)}
            >
                {children}
            </Link>
        );
    };

    return (
        <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-xl border-b border-gray-200">
            <div className="container mx-auto px-6">
                <div className="flex items-center justify-between h-18 py-4">
                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-3">
                        <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-red-600 to-red-700 flex items-center justify-center shadow-lg shadow-red-600/20">
                            <svg
                                className="w-6 h-6 text-white"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                                />
                            </svg>
                        </div>
                        <div className="hidden sm:block">
                            <span className="font-bold text-xl text-gray-900">
                                SpeakAssess
                            </span>
                            <span className="block text-xs text-gray-500 -mt-0.5">Interview Assessment</span>
                        </div>
                    </Link>

                    {/* Desktop Navigation */}
                    <nav className="hidden md:flex items-center gap-2">
                        {isAuthenticated ? (
                            <>
                                <NavLink to="/dashboard">Dashboard</NavLink>
                                <NavLink to="/assessment">New Assessment</NavLink>
                            </>
                        ) : (
                            <>
                                <NavLink to="/">Home</NavLink>
                                <NavLink to="/login">Login</NavLink>
                            </>
                        )}
                    </nav>

                    {/* Right side actions */}
                    <div className="flex items-center gap-4">
                        {/* Theme toggle */}
                        <button
                            onClick={toggleTheme}
                            className="p-2.5 rounded-lg bg-gray-100 text-gray-600 hover:text-gray-900 hover:bg-gray-200 transition-all duration-200"
                            aria-label="Toggle theme"
                        >
                            {isDark ? (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                                    />
                                </svg>
                            ) : (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                                    />
                                </svg>
                            )}
                        </button>

                        {/* Desktop auth buttons */}
                        {isAuthenticated ? (
                            <div className="hidden md:flex items-center gap-4">
                                <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-gray-100">
                                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-red-600 to-red-700 flex items-center justify-center text-white text-sm font-bold">
                                        {user?.email?.charAt(0).toUpperCase() || 'U'}
                                    </div>
                                    <span className="text-sm text-gray-600 max-w-32 truncate font-medium">
                                        {user?.email}
                                    </span>
                                </div>
                                <Button variant="ghost" size="sm" onClick={handleSignOut}>
                                    Sign out
                                </Button>
                            </div>
                        ) : (
                            <div className="hidden md:block">
                                <Button onClick={() => navigate('/signup')} size="sm">
                                    Get Started
                                </Button>
                            </div>
                        )}

                        {/* Mobile menu button */}
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="md:hidden p-2.5 rounded-lg bg-gray-100 text-gray-600"
                            aria-label="Toggle menu"
                        >
                            {mobileMenuOpen ? (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            ) : (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            )}
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
                            className="md:hidden border-t border-gray-200"
                        >
                            <nav className="py-4 flex flex-col gap-2">
                                {isAuthenticated ? (
                                    <>
                                        <NavLink to="/dashboard">Dashboard</NavLink>
                                        <NavLink to="/assessment">New Assessment</NavLink>
                                        <div className="border-t border-gray-200 mt-2 pt-2">
                                            <button
                                                onClick={handleSignOut}
                                                className="w-full px-4 py-2.5 text-left text-red-600 hover:bg-red-50 rounded-lg font-medium"
                                            >
                                                Sign out
                                            </button>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <NavLink to="/">Home</NavLink>
                                        <NavLink to="/login">Login</NavLink>
                                        <NavLink to="/signup">Sign Up</NavLink>
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
