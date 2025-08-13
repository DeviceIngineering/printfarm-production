/**
 * Тесты для Analytics системы
 * Предотвращают TypeScript ошибки в production
 */

import { analytics, useAnalytics, trackFunction } from '../utils/analytics';

describe('Analytics System', () => {
  beforeEach(() => {
    // Reset localStorage
    localStorage.clear();
    // Mock environment
    process.env.REACT_APP_ANALYTICS_ENABLED = 'false';
  });

  describe('Initialization', () => {
    test('should initialize without TypeScript errors', () => {
      expect(analytics).toBeDefined();
      expect(analytics.trackEvent).toBeDefined();
      expect(analytics.trackFeatureUsage).toBeDefined();
    });

    test('should generate unique user ID', () => {
      const metrics1 = analytics.getSessionMetrics();
      const metrics2 = analytics.getSessionMetrics();
      
      expect(metrics1.userId).toBeDefined();
      expect(metrics1.userId).toBe(metrics2.userId); // Same session
    });
  });

  describe('Event Tracking', () => {
    test('should track events without errors', () => {
      expect(() => {
        analytics.trackEvent('test', 'action', { meta: 'data' });
      }).not.toThrow();
    });

    test('should track feature usage without errors', () => {
      expect(() => {
        analytics.startFeatureInteraction('feature', 'action');
        analytics.trackFeatureUsage('feature', 'action', true);
      }).not.toThrow();
    });

    test('should handle error tracking with proper types', () => {
      const error = new Error('Test error');
      expect(() => {
        analytics.trackError(error, { context: 'test' });
      }).not.toThrow();
    });
  });

  describe('React Hooks', () => {
    test('useAnalytics should return proper functions', () => {
      const hook = useAnalytics();
      
      expect(typeof hook.trackEvent).toBe('function');
      expect(typeof hook.trackFeatureUsage).toBe('function');
      expect(typeof hook.trackError).toBe('function');
    });
  });

  describe('Decorator', () => {
    test('trackFunction decorator should handle TypeScript types correctly', () => {
      class TestClass {
        @trackFunction('test', 'method')
        async testMethod(arg: string): Promise<string> {
          return `result: ${arg}`;
        }

        @trackFunction('test')
        syncMethod(arg: number): number {
          return arg * 2;
        }
      }

      const instance = new TestClass();
      
      expect(async () => {
        const result = await instance.testMethod('hello');
        expect(result).toBe('result: hello');
      }).not.toThrow();

      expect(() => {
        const result = instance.syncMethod(5);
        expect(result).toBe(10);
      }).not.toThrow();
    });

    test('decorator should handle errors with proper typing', async () => {
      class TestClass {
        @trackFunction('test', 'error')
        async errorMethod(): Promise<void> {
          throw new Error('Test error');
        }
      }

      const instance = new TestClass();
      
      await expect(instance.errorMethod()).rejects.toThrow('Test error');
    });
  });

  describe('Performance Tracking', () => {
    test('should handle performance metrics safely', () => {
      const metrics = analytics.getSessionMetrics();
      
      expect(metrics).toHaveProperty('performanceMetrics');
      expect(metrics.performanceMetrics).toBeDefined();
    });

    test('should export session data without errors', () => {
      const data = analytics.exportSessionData();
      
      expect(typeof data).toBe('string');
      expect(() => JSON.parse(data)).not.toThrow();
    });
  });

  describe('Type Safety', () => {
    test('all public methods should accept correct parameter types', () => {
      // Test parameter types don't cause TypeScript errors
      analytics.trackPageView('test-page', { meta: 'data' });
      analytics.trackABTest('test', 'variant', true);
      analytics.trackConversion('purchase', 100, { currency: 'USD' });
      analytics.trackFormInteraction('login', 'email', 'focus');
      analytics.trackAPICall('/api/test', 'GET', 150, true, 200);
      
      // Should complete without TypeScript compilation errors
      expect(true).toBe(true);
    });
  });
});

describe('FeedbackWidget TypeScript Types', () => {
  test('window.gtag should be properly typed', () => {
    // Mock gtag function
    (window as any).gtag = jest.fn();
    
    expect(() => {
      if (window.gtag) {
        window.gtag('event', 'test', {});
      }
    }).not.toThrow();
  });
});