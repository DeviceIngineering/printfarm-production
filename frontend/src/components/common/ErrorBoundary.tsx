import React from 'react';
import { Alert, Button } from 'antd';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '24px' }}>
          <Alert
            message="Произошла ошибка"
            description={this.state.error?.message || 'Неизвестная ошибка'}
            type="error"
            showIcon
            action={
              <Button 
                size="small" 
                onClick={() => window.location.reload()}
              >
                Перезагрузить
              </Button>
            }
          />
        </div>
      );
    }

    return this.props.children;
  }
}