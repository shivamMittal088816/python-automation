import { Component } from 'react';
import { Alert, Button } from './Controls';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { failed: true, error };
  }

  componentDidCatch(error, details) {
    console.error('Unexpected interface error', error, details);
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return <main className="mx-auto max-w-xl p-8">
      <Alert type="error">The page could not be displayed because of an unexpected error.</Alert>
      <p className="mb-4 text-sm text-slate-600">Reload the application. If the problem continues, contact support.</p>
      <Button primary onClick={() => window.location.reload()}>Reload application</Button>
    </main>;
  }
}
