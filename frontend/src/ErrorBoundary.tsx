import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  failed: boolean;
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { failed: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { failed: true };
  }

  componentDidCatch(error: Error, information: ErrorInfo) {
    console.error("WebAnn UI failed", error, information.componentStack);
  }

  render() {
    if (this.state.failed) {
      return (
        <main className="error-page">
          <h1>Something went wrong</h1>
          <p>Reload the page. If the problem continues, contact your manager.</p>
        </main>
      );
    }
    return this.props.children;
  }
}
