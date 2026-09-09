import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null, info: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    this.setState({ info });
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 20, fontFamily: 'monospace', fontSize: 14 }}>
          <h2 style={{ color: 'red' }}>ERROR: {String(this.state.error)}</h2>
          <pre style={{ whiteSpace: 'pre-wrap' }}>
            {this.state.error?.stack}
          </pre>
          <h3>Component stack:</h3>
          <pre style={{ whiteSpace: 'pre-wrap' }}>
            {this.state.info?.componentStack}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}
