import { Component } from 'react';
import { Alert, Button } from './Controls';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error, details) {
    console.error('Unexpected interface error', error, details);
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return <main className="mx-auto max-w-xl p-8">
      <Alert type="error">The page could not be displayed because of an unexpected error.</Alert>
      <Button primary onClick={() => window.location.reload()}>Reload application</Button>
    </main>;
  }
}
