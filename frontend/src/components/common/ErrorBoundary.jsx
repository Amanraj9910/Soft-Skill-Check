import React from 'react';
import Button from './Button';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        // Update state so the next render will show the fallback UI.
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        // You can also log the error to an error reporting service
        console.error("Uncaught error:", error, errorInfo);
        this.setState({ error, errorInfo });
    }

    handleReload = () => {
        window.location.reload();
    };

    handleGoHome = () => {
        window.location.href = '/';
    };

    render() {
        if (this.state.hasError) {
            // You can render any custom fallback UI
            return (
                <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
                    <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 border border-slate-200 text-center">
                        <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
                            <span className="text-3xl">⚠️</span>
                        </div>

                        <h1 className="text-2xl font-bold text-slate-900 mb-2">Something went wrong</h1>
                        <p className="text-slate-600 mb-6">
                            We're sorry, but an unexpected error occurred. Please try reloading the page.
                        </p>

                        <div className="bg-slate-50 p-4 rounded-lg text-left mb-6 overflow-auto max-h-48 text-xs font-mono text-slate-700 border border-slate-200">
                            <strong>{this.state.error && this.state.error.toString()}</strong>
                            <br />
                            {this.state.errorInfo && this.state.errorInfo.componentStack}
                        </div>

                        <div className="flex gap-4 justify-center">
                            <Button onClick={this.handleReload} className="bg-slate-900 text-white hover:bg-black">
                                Reload Page
                            </Button>
                            <Button variant="secondary" onClick={this.handleGoHome}>
                                Go to Home
                            </Button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
